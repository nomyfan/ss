import argparse
import io
import logging
import os
import re
import sys
import tomllib
from pathlib import Path

from ebooklib import epub
from PIL import Image
from dataclasses import dataclass
from result import Result, Ok, Err


@dataclass
class Metadata:
    title: str
    author: str
    identifier: str
    language: str = "ja"


@dataclass
class ChapterNode:
    """Recursive chapter node supporting arbitrary hierarchy levels"""

    chapter: int  # Chapter number at this level
    title: str | None = None  # Custom title (optional)
    start_file: str | None = None  # For leaf nodes: starting file
    children: list["ChapterNode"] | None = None  # For non-leaf nodes: sub-chapters

    def is_leaf(self) -> bool:
        """Check if this is a leaf node (has start_file)"""
        return self.start_file is not None

    def get_all_leaves(self) -> list["ChapterNode"]:
        """Recursively get all leaf nodes"""
        if self.is_leaf():
            return [self]
        if self.children:
            leaves = []
            for child in self.children:
                leaves.extend(child.get_all_leaves())
            return leaves
        return []


@dataclass
class ParsedImage:
    """Parsed manga image filename with chapter path assignment"""

    filename: str  # Original filename
    sort_num: int  # Sort number from filename (VOL{num})
    page_num: int  # Page number
    chapter_path: list[int]  # Path to chapter (e.g., [1, 2] means vol 1, chapter 2)
    chapter_titles: list[str | None]  # Titles at each level


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)


def load_config(config_path: Path) -> tuple[Metadata, list[str], list[ChapterNode]]:
    """
    Load configuration from TOML file with nested chapter structure.

    Returns:
        (metadata, hierarchy_levels, chapter_roots)
    """
    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    # Parse metadata - all fields required
    if "metadata" not in config:
        raise ValueError("Missing [metadata] section in config file")

    meta = config["metadata"]
    required_meta_fields = ["title", "author", "language"]
    for field in required_meta_fields:
        if field not in meta:
            raise ValueError(f"Missing required metadata field: {field}")

    metadata = Metadata(
        title=meta["title"],
        author=meta["author"],
        identifier=f"manga-{meta['title']}",
        language=meta["language"],
    )

    # Parse hierarchy levels
    if "hierarchy" not in config:
        raise ValueError("Missing [hierarchy] section in config file")

    if "levels" not in config["hierarchy"]:
        raise ValueError("Missing 'levels' in [hierarchy] section")

    hierarchy_levels = config["hierarchy"]["levels"]
    if not isinstance(hierarchy_levels, list) or len(hierarchy_levels) == 0:
        raise ValueError("hierarchy.levels must be a non-empty list")

    # Parse chapter definitions (nested structure)
    if "chapters" not in config or not config["chapters"]:
        raise ValueError("Missing or empty [[chapters]] in config file")

    def parse_chapter_node(ch_data: dict, level: int, path: str) -> ChapterNode:
        """Recursively parse a chapter node"""
        if "chapter" not in ch_data:
            raise ValueError(f"Missing 'chapter' field in {path}")

        chapter_num = ch_data["chapter"]
        title = ch_data.get("title")
        start_file = ch_data.get("start_file")
        sub_chapters = ch_data.get("sub")

        # Validate: either leaf (has start_file) or non-leaf (has children)
        if start_file and sub_chapters:
            raise ValueError(
                f"Chapter at {path} cannot have both 'start_file' and 'sub' (leaf nodes should only have start_file)"
            )

        # Parse children if present
        children = None
        if sub_chapters:
            if level + 1 >= len(hierarchy_levels):
                raise ValueError(
                    f"Chapter at {path} has sub-chapters but hierarchy only defines {len(hierarchy_levels)} levels"
                )
            children = []
            for idx, sub_ch in enumerate(sub_chapters):
                child_path = f"{path}.sub[{idx}]"
                children.append(parse_chapter_node(sub_ch, level + 1, child_path))

        # Leaf node validation
        if level == len(hierarchy_levels) - 1:
            # Last level must be leaf nodes
            if not start_file:
                raise ValueError(
                    f"Chapter at {path} is at the last hierarchy level ('{hierarchy_levels[level]}') but missing 'start_file'"
                )

        return ChapterNode(
            chapter=chapter_num,
            title=title,
            start_file=start_file,
            children=children,
        )

    # Parse root chapters
    chapter_roots = []
    for idx, ch in enumerate(config["chapters"]):
        path = f"chapters[{idx}]"
        chapter_roots.append(parse_chapter_node(ch, level=0, path=path))

    return metadata, hierarchy_levels, chapter_roots


def parse_vol_page_filename(filename: str) -> tuple[int, int] | None:
    """
    Parse VOL{num}_{page}.ext format filename.
    Note: {num} is used for sorting, not semantic volume number.

    Returns:
        (sort_num, page_num) or None if parsing fails
    """
    match = re.match(r"^VOL(\d+)_(\d+)\.", filename, re.IGNORECASE)
    if not match:
        return None

    sort_num = int(match.group(1))
    page_num = int(match.group(2))
    return (sort_num, page_num)


def assign_chapters_to_images(
    image_files: list[str], chapter_roots: list[ChapterNode]
) -> Result[list[ParsedImage], str]:
    """
    Parse image filenames and assign chapters based on nested chapter structure.

    Args:
        image_files: List of image filenames (VOL{num}_{page}.ext format)
        chapter_roots: Root chapter nodes from config file

    Returns:
        List of ParsedImage with chapter path assignments
    """
    if not image_files:
        return Err("No image files to parse")

    if not chapter_roots:
        return Err("No chapter definitions provided")

    # Parse all filenames
    parsed_files = []
    for filename in image_files:
        result = parse_vol_page_filename(filename)
        if result is None:
            return Err(
                f"Invalid filename format: {filename}\nExpected format: VOL{{num}}_{{page}}.ext (e.g., VOL01_005.jpg)"
            )

        sort_num, page = result
        parsed_files.append((filename, sort_num, page))

    # Sort by sort_num and page
    parsed_files.sort(key=lambda x: (x[1], x[2]))

    # Extract all leaf nodes with their paths
    def get_leaf_paths(
        nodes: list[ChapterNode],
        current_path: list[int] = [],
        current_titles: list[str | None] = [],
    ) -> list[tuple[list[int], list[str | None], str]]:
        """
        Get all leaf nodes with their chapter paths and start files.
        Returns: [(chapter_path, chapter_titles, start_file), ...]
        """
        leaves = []
        for node in nodes:
            new_path = current_path + [node.chapter]
            new_titles = current_titles + [node.title]

            if node.is_leaf():
                if node.start_file:
                    leaves.append((new_path, new_titles, node.start_file))
            elif node.children:
                leaves.extend(get_leaf_paths(node.children, new_path, new_titles))

        return leaves

    leaf_paths = get_leaf_paths(chapter_roots)

    # Build lookup: start_file -> (chapter_path, titles, sort_num, page_num)
    chapter_lookup = []
    for chapter_path, chapter_titles, start_file in leaf_paths:
        result = parse_vol_page_filename(start_file)
        if result is None:
            return Err(f"Invalid start_file in chapter definition: {start_file}")

        sort_num, page_num = result
        chapter_lookup.append((sort_num, page_num, chapter_path, chapter_titles))

    # Sort by sort_num and page_num
    chapter_lookup.sort(key=lambda x: (x[0], x[1]))

    # Assign chapters to images
    parsed_images = []
    for filename, sort_num, page in parsed_files:
        # Find the chapter whose start (sort_num, page) <= current (sort_num, page)
        assigned_chapter = None

        for ch_sort, ch_page, ch_path, ch_titles in reversed(chapter_lookup):
            if (ch_sort, ch_page) <= (sort_num, page):
                assigned_chapter = (ch_path, ch_titles)
                break

        if assigned_chapter is None:
            return Err(
                f"Cannot assign chapter for {filename} (sort_num={sort_num}, page={page})\n"
                f"No chapter starts before this file"
            )

        chapter_path, chapter_titles = assigned_chapter
        parsed_images.append(
            ParsedImage(
                filename=filename,
                sort_num=sort_num,
                page_num=page,
                chapter_path=chapter_path,
                chapter_titles=chapter_titles,
            )
        )

    return Ok(parsed_images)


def format_chapter_title(
    chapter_path: list[int],
    hierarchy_levels: list[str],
    custom_title: str | None,
) -> str:
    """
    Format chapter title based on hierarchy path.

    Args:
        chapter_path: Chapter path (e.g., [1, 2] for vol 1, chapter 2)
        hierarchy_levels: Level names (e.g., ["卷", "话"])
        custom_title: Custom title if provided

    Returns:
        Formatted title
    """
    # If custom title provided, use it
    if custom_title is not None:
        return custom_title

    # Otherwise generate default title from path
    parts = []
    for i, (level_name, chapter_num) in enumerate(zip(hierarchy_levels, chapter_path)):
        parts.append(f"{level_name}{chapter_num}")

    return " ".join(parts)


def create_manga_epub(
    input_folder: Path,
    metadata: Metadata,
    hierarchy_levels: list[str],
    chapter_roots: list[ChapterNode],
) -> Result[epub.EpubBook, str]:
    """
    Convert manga image folder to EPUB with flexible hierarchy support

    Args:
        input_folder: Folder path containing images
        metadata: Book metadata
        hierarchy_levels: Level names (e.g., ["卷", "话"])
        chapter_roots: Root chapter nodes from config file
    """
    # Create EPUB book object
    book = epub.EpubBook()

    # Set metadata
    book.set_identifier(metadata.identifier)
    book.set_title(metadata.title)
    book.set_language(metadata.language)
    book.add_author(metadata.author)

    # Get all image files
    image_files = [
        f
        for f in os.listdir(input_folder)
        if f.lower().endswith((".jpeg", ".jpg", ".png", ".webp"))
    ]

    if not image_files:
        return Err("No images found in the input folder.")

    logger.info(f"Found {len(image_files)} images")

    # Assign chapters to images based on config
    assign_result = assign_chapters_to_images(image_files, chapter_roots)
    match assign_result:
        case Err(error):
            return Err(error)
        case Ok(parsed_images):
            logger.info(f"Assigned chapters to {len(parsed_images)} images")

    # Store chapters for TOC and spine
    all_chapters: list[epub.EpubHtml] = []
    chapter_info: dict[
        epub.EpubHtml, tuple[list[int], list[str | None]]
    ] = {}  # chapter -> (path, titles)
    spine: list[epub.EpubHtml] = []
    chapter_counter = 0

    # Group by chapter_path
    chapter_images: list[tuple[str, str]] = []
    last_chapter_path: list[int] | None = None
    last_chapter_titles: list[str | None] | None = None
    cover_set = False

    for idx, parsed_img in enumerate(parsed_images, 1):
        img_file = parsed_img.filename
        current_path = parsed_img.chapter_path
        current_titles = parsed_img.chapter_titles

        # If new chapter, save the previous chapter
        if current_path != last_chapter_path and last_chapter_path is not None:
            chapter_counter += 1
            # Get the last title (leaf level)
            last_title = last_chapter_titles[-1] if last_chapter_titles else None  # type: ignore
            chapter = create_chapter(
                book,
                chapter_images,
                last_chapter_path,
                hierarchy_levels,
                last_title,
                chapter_counter,
            )

            spine.append(chapter)
            all_chapters.append(chapter)
            chapter_info[chapter] = (last_chapter_path, last_chapter_titles)  # type: ignore

            chapter_images = []

        # Read and add image
        img_path = os.path.join(input_folder, img_file)
        with Image.open(img_path) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")

            max_size = (1200, 1600)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format="JPEG", quality=60, optimize=True)
            img_data = img_byte_arr.getvalue()

        # Set first image as cover
        if not cover_set:
            book.set_cover("cover.jpg", img_data, create_page=False)
            cover_set = True

        # Create EPUB image item
        epub_img = epub.EpubItem(
            uid=f"image_{idx}",
            file_name=f"images/{img_file}",
            media_type="image/jpeg",
            content=img_data,
        )
        book.add_item(epub_img)

        chapter_images.append((img_file, f"images/{img_file}"))

        if idx % 50 == 0:
            sys.stderr.write(f"\rProcessed {idx}/{len(parsed_images)} images...")
            sys.stderr.flush()

        last_chapter_path = current_path
        last_chapter_titles = current_titles

    # Show final progress
    sys.stderr.write(
        f"\rProcessed {len(parsed_images)}/{len(parsed_images)} images...\n"
    )
    sys.stderr.flush()

    # Add the last chapter
    if chapter_images and last_chapter_path is not None:
        chapter_counter += 1
        last_title = last_chapter_titles[-1] if last_chapter_titles else None  # type: ignore
        chapter = create_chapter(
            book,
            chapter_images,
            last_chapter_path,
            hierarchy_levels,
            last_title,
            chapter_counter,
        )

        spine.append(chapter)
        all_chapters.append(chapter)
        chapter_info[chapter] = (last_chapter_path, last_chapter_titles)  # type: ignore

    # Build hierarchical TOC based on chapter paths
    def build_toc_recursive(
        chapters_with_info: list[tuple[epub.EpubHtml, list[int], list[str | None]]],
        level: int,
    ) -> list:
        """Recursively build TOC structure"""
        if level >= len(hierarchy_levels):
            return []

        # Group chapters by their value at current level
        from collections import defaultdict

        groups = defaultdict(list)

        for chapter, path, titles in chapters_with_info:
            if len(path) > level:
                key = path[level]
                groups[key].append((chapter, path, titles))

        # Build TOC for this level
        toc = []
        for key in sorted(groups.keys()):
            group = groups[key]

            # Find the first chapter in this group (representative)
            first_chapter, first_path, first_titles = group[0]

            if level == len(hierarchy_levels) - 1:
                # Leaf level - add all chapters directly
                for ch, _, _ in group:
                    toc.append(ch)
            else:
                # Non-leaf level - create section
                section_title = (
                    first_titles[level]
                    if level < len(first_titles)
                    else f"{hierarchy_levels[level]}{key}"
                )

                # Get children
                children = build_toc_recursive(group, level + 1)

                if children:
                    # Create section linking to first chapter
                    section = epub.Section(section_title, href=first_chapter.file_name)
                    toc.append((section, children))
                else:
                    toc.append(first_chapter)

        return toc

    # Build TOC
    chapters_with_paths = [
        (ch, path, titles) for ch, (path, titles) in chapter_info.items()
    ]
    hierarchical_toc = build_toc_recursive(chapters_with_paths, level=0)

    book.toc = hierarchical_toc

    # Add navigation file
    book.add_item(epub.EpubNcx())

    # Create custom CSS to disable TOC numbering
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=b"""
/* Disable automatic numbering in table of contents */
nav ol {
    list-style-type: none;
}
nav ul {
    list-style-type: none;
}
""",
    )
    book.add_item(nav_css)

    # Add the navigation with the custom CSS
    nav = epub.EpubNav()
    nav.add_item(nav_css)
    book.add_item(nav)

    # Set spine (reading order)
    book.spine = spine

    logger.info(f"Total chapters: {chapter_counter}")

    return Ok(book)


def create_chapter(
    book: epub.EpubBook,
    images: list[tuple[str, str]],
    chapter_path: list[int],
    hierarchy_levels: list[str],
    custom_title: str | None,
    chapter_index: int,
) -> epub.EpubHtml:
    """Create a chapter containing multiple images"""

    # Format chapter title
    chapter_title = format_chapter_title(chapter_path, hierarchy_levels, custom_title)

    # Generate chapter HTML content
    html_content = f"""<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{chapter_title}</title>
    <style>
        body {{ margin: 0; padding: 0; text-align: center; background-color: #000; }}
        img {{ max-width: 100%; height: auto; margin: 0; padding: 0; display: block; margin: 0 auto; }}
        .page {{ page-break-after: always; }}
    </style>
</head>
<body>
"""

    for img_file, img_path in images:
        html_content += (
            f'    <div class="page"><img src="{img_path}" alt="{img_file}"/></div>\n'
        )

    html_content += """</body>
</html>"""

    # Create chapter
    epub_chapter = epub.EpubHtml(
        title=chapter_title,
        file_name=f"chapter_{chapter_index}.xhtml",
        lang="ja",
    )
    epub_chapter.content = html_content.encode("utf-8")

    book.add_item(epub_chapter)
    return epub_chapter


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert manga images to EPUB format with flexible hierarchy support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
File Naming Format:
  VOL{num}_{page}.ext

  Note: {num} is used for sorting files, not semantic volume numbering

  Examples:
    VOL01_001.jpg  # Sorts first
    VOL01_005.jpg  # Sorts by num=01, page=005
    VOL02_001.jpg  # Sorts by num=02, page=001

Configuration File (TOML) - Nested Structure:

  [metadata]
  title = "My Manga"
  author = "Author Name"
  language = "ja"

  [hierarchy]
  levels = ["卷", "话"]  # Define hierarchy levels

  # For multi-volume (2 levels):
  [[chapters]]  # Volume 1
  chapter = 1
  title = "卷1"  # Optional

    [[chapters.sub]]  # Chapter within volume
    chapter = 0
    start_file = "VOL01_001.jpg"
    title = "第1话"  # Optional

  [[chapters]]  # Volume 2
  chapter = 2

    [[chapters.sub]]
    chapter = 0
    start_file = "VOL02_001.jpg"

  # For single volume (1 level):
  [hierarchy]
  levels = ["话"]

  [[chapters]]
  chapter = 0
  start_file = "VOL01_001.jpg"
  title = "第1话"

Notes:
  - Supports arbitrary hierarchy levels (e.g., 部→卷→话)
  - Leaf nodes (with start_file) define chapter boundaries  - Non-leaf nodes create TOC sections
  - Custom titles are optional

Examples:
  # Basic usage
  python manga_epub.py -i "Manga Folder" -c manga_config.toml

  # With custom output file
  python manga_epub.py -i "Manga Folder" -c manga_config.toml -o output.epub
        """,
    )

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input folder path containing manga images",
    )
    parser.add_argument(
        "-c",
        "--config",
        required=True,
        help="TOML configuration file with metadata and chapter definitions",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output EPUB filename (default: uses config title)",
    )

    args = parser.parse_args()

    input_folder_str = args.input
    config_path = Path(args.config)

    # Check if folder exists
    if not os.path.isdir(input_folder_str):
        logger.error(f"Error: Folder does not exist: {input_folder_str}")
        sys.exit(1)

    # Check if config file exists
    if not config_path.is_file():
        logger.error(f"Error: Config file does not exist: {config_path}")
        sys.exit(1)

    # Load configuration
    try:
        metadata, hierarchy_levels, chapter_roots = load_config(config_path)
    except (ValueError, KeyError, tomllib.TOMLDecodeError) as e:
        logger.error(f"Error loading config file: {e}")
        sys.exit(1)

    # Determine output filename
    if args.output:
        output_file_str = args.output
    else:
        # Use title from config as output filename
        output_file_str = f"{metadata.title}.epub"

    # Ensure output file has .epub extension
    if not output_file_str.lower().endswith(".epub"):
        output_file_str += ".epub"

    # Convert to Path objects
    input_folder = Path(input_folder_str)
    output_file = Path(output_file_str)

    # Count leaf nodes (actual chapters with content)
    def count_leaves(nodes: list[ChapterNode]) -> int:
        count = 0
        for node in nodes:
            if node.is_leaf():
                count += 1
            elif node.children:
                count += count_leaves(node.children)
        return count

    leaf_count = count_leaves(chapter_roots)

    logger.info(f"Input folder: {input_folder}")
    logger.info(f"Output file: {output_file}")
    logger.info(f"Title: {metadata.title}")
    logger.info(f"Author: {metadata.author}")
    logger.info(f"Hierarchy: {' → '.join(hierarchy_levels)}")
    logger.info(f"Chapters defined: {leaf_count}")
    logger.info("")

    result = create_manga_epub(input_folder, metadata, hierarchy_levels, chapter_roots)

    match result:
        case Ok(epub_book):
            # Write EPUB file
            logger.info(f"\nGenerating EPUB file: {output_file}")
            epub.write_epub(str(output_file), epub_book)
            logger.info("\033[92m✓\033[0m Successfully created EPUB file!")
            logger.info(
                f"\n\033[92m✓\033[0m Conversion complete! You can now open {output_file} with an e-book reader"
            )
        case Err(e):
            logger.error(f"Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
