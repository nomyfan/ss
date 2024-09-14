import process from "node:process";
import { execSync } from "node:child_process";
import path from "node:path";
import fs from "node:fs/promises";

const argv = process.argv.slice(2);

const isOption = (s) => /^-(([a-zA-Z])|(-[a-zA-Z]\w+))(=.*)?$/.test(s);

/**
 * @param {string} cmd
 * @param {boolean} trim
 * @returns
 */
function sh(cmd, trim = true) {
  const output = execSync(cmd, { encoding: "utf-8" });
  if (trim) {
    return output.trim();
  }
  return output;
}

function die(message, code = 1) {
  process.stderr("error: %s\n", message);
  process.exit(code);
}

function opengh() {
  const options = argv.slice(1).filter((arg) => isOption(arg));

  try {
    const output = sh("git remote get-url origin");
    const RE =
      /^(?:git@github\.com:|https:\/\/github\.com\/|ssh:\/\/git@(?:ssh\.)?github.com(?::443)?\/)([^\/]+)\/([^\/]+)\.git$/;

    const match = RE.exec(output);
    if (match) {
      const [, owner, repo] = match;
      const rev = sh("git rev-parse --abbrev-ref HEAD");

      let url = `https://github.com/${owner}/${repo}/tree/${rev}`;
      if (options.includes("-p")) {
        const p = sh("git rev-parse --show-prefix").slice(0, -1);
        url += `/${p}`;
      }
      execSync(`open ${url}`);
    }
  } catch (err) {
    const stderr = err.stderr.toString().trim();
    if (stderr) {
      if (stderr.includes("fatal: not a git repository")) {
        execSync("open https://github.com");
      } else if (stderr.includes("No such remote")) {
        execSync("open https://github.com/new");
      } else {
        process.stderr(stderr);
      }
    }
  }
}

async function opennpm() {
  const packageJson = JSON.parse(
    await fs.readFile(
      path.resolve(process.cwd(), argv[1] || ".", "package.json"),
      "utf-8",
    ),
  );
  if (!packageJson.name) {
    die("No package name found in package.json");
  }
  execSync(`open https://www.npmjs.com/package/${packageJson.name}`);
}

async function main() {
  const subcommand = argv[0];
  const subcommands = ["gh", "npm"];
  if (!subcommands.includes(subcommand)) {
    die("Available subcommands: gh, npm");
  }

  switch (subcommand) {
    case "gh":
      opengh();
      break;
    case "npm":
      await opennpm();
      break;
  }
}

await main();
