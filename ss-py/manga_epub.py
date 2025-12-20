import argparse
import io
import logging
import os
import re
import sys
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
class ParsedImage:
    """Parsed manga image filename"""

    filename: str  # Original filename
    prefix: str  # CH, VOL, etc.
    chapter_num: int  # Chapter/volume number
    page_num: int  # Page number within chapter


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)


def parse_and_validate_images(
    image_files: list[str],
) -> Result[list[ParsedImage], str]:
    """
    Parse and validate image filenames.
    Expected format: PREFIX_NUMBER.ext (e.g., CH01_05.jpg, VOL1_74.jpg)
    Returns sorted list of parsed images or error message.
    """
    if not image_files:
        return Err("No image files to parse")

    # Pattern: (letters)(numbers)_(numbers).extension
    pattern = re.compile(r"^([A-Za-z]+)(\d+)_(\d+)\.")

    parsed_images: list[ParsedImage] = []
    prefixes = set()

    for filename in image_files:
        match = pattern.match(filename)
        if not match:
            return Err(
                f"Invalid filename format: {filename}\nExpected format: PREFIX_NUMBER.ext (e.g., CH01_05.jpg)"
            )

        prefix = match.group(1).upper()
        chapter_num = int(match.group(2))
        page_num = int(match.group(3))

        parsed_images.append(
            ParsedImage(
                filename=filename,
                prefix=prefix,
                chapter_num=chapter_num,
                page_num=page_num,
            )
        )
        prefixes.add(prefix)

    if len(prefixes) > 1:
        return Err(
            f"Mixed prefixes found: {', '.join(sorted(prefixes))}. All files must use the same prefix"
        )

    # Sort by chapter number, then page number
    parsed_images.sort(key=lambda x: (x.chapter_num, x.page_num))

    return Ok(parsed_images)


def format_chapter_title(chapter_name: str | None, chapter_num: int) -> str:
    """
    Format chapter title based on prefix.
    VOL prefix -> "卷{number}" (Volume)
    CH prefix -> "话{number}" (Chapter)
    Other -> "Chapter {name}"
    """
    if not chapter_name:
        return f"Chapter {chapter_num}"

    match = re.match(r"([A-Za-z]+)(\d+)", chapter_name)
    if match:
        prefix, number = match.groups()
        prefix_upper = prefix.upper()

        if prefix_upper == "VOL":
            return f"卷{int(number)}"
        elif prefix_upper == "CH":
            return f"话{int(number)}"

    return f"Chapter {chapter_name}"


def create_manga_epub(
    input_folder: Path, output_file: Path, metadata: Metadata
) -> Result[epub.EpubBook, str]:
    """
    Convert manga image folder to EPUB

    Args:
        input_folder: Folder path containing images
        output_file: Output EPUB file path
        metadata: Book metadata
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

    # Parse and validate images
    parse_result = parse_and_validate_images(image_files)
    match parse_result:
        case Err(error):
            return Err(error)
        case Ok(parsed_images):
            logger.info(f"Validated: All files use {parsed_images[0].prefix} prefix")

    # Store all chapters
    chapters: list[epub.EpubHtml] = []
    spine: list[str | epub.EpubHtml] = ["nav"]

    # Group by chapter/volume
    chapter_images: list[tuple[str, str]] = []
    last_chapter_num: int | None = None
    cover_set = False  # Track if cover has been set

    for idx, parsed_img in enumerate(parsed_images, 1):
        img_file = parsed_img.filename
        chapter_num = parsed_img.chapter_num

        # If new chapter, save the previous chapter
        if chapter_num != last_chapter_num and last_chapter_num is not None:
            # Format chapter name with prefix and number
            chapter_name = f"{parsed_images[idx - 2].prefix}{last_chapter_num:02d}"
            chapter = create_chapter(
                book, chapter_images, chapter_name, len(chapters) + 1
            )
            chapters.append(chapter)
            spine.append(chapter)
            chapter_images = []

        # Read and add image
        img_path = os.path.join(input_folder, img_file)
        with Image.open(img_path) as img:
            # Convert to RGB (if needed)
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Optimize image size (optional, reduce file size)
            max_size = (1200, 1600)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Save as byte stream
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
            # Update progress on the same line
            sys.stderr.write(f"\rProcessed {idx}/{len(parsed_images)} images...")
            sys.stderr.flush()

        last_chapter_num = chapter_num

    # Show final progress
    sys.stderr.write(
        f"\rProcessed {len(parsed_images)}/{len(parsed_images)} images...\n"
    )
    sys.stderr.flush()

    # Add the last chapter
    if chapter_images and last_chapter_num is not None:
        chapter_name = f"{parsed_images[-1].prefix}{last_chapter_num:02d}"
        chapter = create_chapter(book, chapter_images, chapter_name, len(chapters) + 1)
        chapters.append(chapter)
        spine.append(chapter)

    # Add table of contents
    book.toc = chapters

    # Add navigation file
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Set spine (reading order)
    book.spine = spine

    logger.info(f"Chapters: {len(chapters)}")

    return Ok(book)


def create_chapter(
    book: epub.EpubBook,
    images: list[tuple[str, str]],
    chapter_name: str | None,
    chapter_num: int,
) -> epub.EpubHtml:
    """Create a chapter containing multiple images"""

    # Generate chapter HTML content
    html_content = f"""<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{chapter_name}</title>
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

    # Create chapter with formatted title
    chapter_title = format_chapter_title(chapter_name, chapter_num)
    chapter = epub.EpubHtml(
        title=chapter_title,
        file_name=f"chapter_{chapter_num}.xhtml",
        lang="ja",
    )
    chapter.content = html_content.encode("utf-8")

    book.add_item(chapter)
    return chapter


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert manga images to EPUB format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manga_epub.py -i "Chainsaw Man Vol1" -t "Chainsaw Man" -a "Fujimoto Tatsuki"
  python manga_epub.py --input "Chainsaw Man Vol1" --title "Chainsaw Man" --author "Fujimoto Tatsuki" --output chainsaw_man_vol1.epub
        """,
    )

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input folder path containing manga images",
    )
    parser.add_argument(
        "-t", "--title", required=True, help="Title of the manga/volume"
    )
    parser.add_argument("-a", "--author", required=True, help="Author name")
    parser.add_argument(
        "-o",
        "--output",
        help="Output EPUB filename (default: uses input folder name)",
    )
    parser.add_argument(
        "-l",
        "--language",
        default="ja",
        help="Language code (default: ja)",
    )

    args = parser.parse_args()

    input_folder_str = args.input
    title = args.title
    author = args.author

    # Check if folder exists
    if not os.path.isdir(input_folder_str):
        logger.error(f"Error: Folder does not exist: {input_folder_str}")
        sys.exit(1)

    # Determine output filename
    if args.output:
        output_file_str = args.output
    else:
        # Use folder name as output filename
        folder_name = os.path.basename(input_folder_str.rstrip("/\\"))
        output_file_str = f"{folder_name}.epub"

    # Ensure output file has .epub extension
    if not output_file_str.lower().endswith(".epub"):
        output_file_str += ".epub"

    # Convert to Path objects
    input_folder = Path(input_folder_str)
    output_file = Path(output_file_str)

    # Create metadata
    metadata = Metadata(
        title=title,
        author=author,
        identifier=f"manga-{title}",
        language=args.language,
    )

    logger.info(f"Input folder: {input_folder}")
    logger.info(f"Output file: {output_file}")
    logger.info(f"Title: {title}")
    logger.info("")

    result = create_manga_epub(input_folder, output_file, metadata)

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
