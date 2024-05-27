import { execSync } from "node:child_process";

try {
  const output = execSync("git remote get-url origin", {
    encoding: "utf-8",
    stdio: ["ignore", "pipe", "pipe"],
  }).trim();
  const RE =
    /^(?:git@github\.com:|https:\/\/github\.com\/|ssh:\/\/git@(?:ssh\.)?github.com(?::443)?\/)([^\/]+)\/([^\/]+)\.git$/;

  const match = RE.exec(output);
  if (match) {
    const [, owner, repo] = match;
    const rev = execSync("git rev-parse --abbrev-ref HEAD", {
      encoding: "utf-8",
      stdio: ["ignore", "pipe", "pipe"],
    }).trim();
    execSync(`open https://github.com/${owner}/${repo}/tree/${rev}`);
  }
} catch (e) {
  const stderr = e.stderr.toString().trim();
  if (stderr) {
    if (stderr.includes("fatal: not a git repository")) {
      execSync("open https://github.com");
    } else if (stderr.includes("No such remote")) {
      execSync("open https://github.com/new");
    } else {
      console.error(stderr);
    }
  }
}
