import process from "node:process";
import { execSync } from "node:child_process";
import path from "node:path";
import fs from "node:fs/promises";

const argv = process.argv.slice(2);

const isOption = (s) => /^-(([a-zA-Z])|(-[a-zA-Z]\w+))(=.*)?$/.test(s);

function run(command, trim = true) {
  const output = execSync(command, { encoding: "utf-8" });
  return trim ? output.trim() : output;
}

function exit(message, code = 1) {
  process.stderr("error: %s\n", message);
  process.exit(code);
}

function opengh() {
  const args = argv.slice(1).filter((arg) => !isOption(arg));

  try {
    const output = run("git remote get-url origin");
    const RE =
      /^(?:git@github\.com:|https:\/\/github\.com\/|ssh:\/\/git@(?:ssh\.)?github.com(?::443)?\/)([^\/]+)\/([^\/]+)\.git$/;

    const match = RE.exec(output);
    if (match) {
      const [, owner, repo] = match;
      const rev = run("git rev-parse --abbrev-ref HEAD");
      let subpath = undefined;
      if (args.length > 0) {
        const gitRoot = run("git rev-parse --show-toplevel");
        const absPath = path.resolve(process.cwd(), args[0]);
        if (absPath.startsWith(gitRoot)) {
          subpath = path.relative(gitRoot, absPath);
        }
      }

      const url = `https://github.com/${owner}/${repo}/tree/${rev}${subpath ? `/${subpath}` : ""}`;
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
    exit("No package name found in package.json");
  }
  execSync(`open https://www.npmjs.com/package/${packageJson.name}`);
}

async function main() {
  const subcommand = argv[0];
  const subcommands = ["gh", "npm"];
  if (!subcommands.includes(subcommand)) {
    exit("Available subcommands: gh, npm");
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
