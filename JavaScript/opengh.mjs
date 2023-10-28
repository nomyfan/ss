import { execSync } from "node:child_process";

try {
  const output = execSync("git remote get-url origin", {
    encoding: "utf-8",
    stdio: ["ignore", "pipe", "pipe"],
  }).trim();
  const RE =
    /^(?:git@github\.com:|https:\/\/github\.com\/)([^\/]+)\/([^\/]+)\.git$/;

  const match = RE.exec(output);
  if (match) {
    const [, owner, repo] = match;
    execSync(`open https://github.com/${owner}/${repo}`);
  }
} catch (e) {
  const stderr = e.stderr.toString().trim();
  if (stderr) {
    if (stderr.includes("fatal: not a git repository")) {
      execSync(`open https://github.com`);
    } else {
      console.error(stderr);
    }
  }
}
