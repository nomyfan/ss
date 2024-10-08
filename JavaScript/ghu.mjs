import process from "node:process";
import { execSync } from "node:child_process";

const argv = process.argv.slice(2);

const isOption = (s) => s.startsWith("--");
const options = argv.filter((arg) => isOption(arg));
const args = argv.filter((arg) => !isOption(arg));

function parseOwnerRepo(args) {
  const first = args[0];

  const GIT_RE =
    /^(?:(?:ssh:\/\/git@ssh\.github\.com\/)|(?:git@github\.com:)|(?:https:\/\/github\.com\/))([^\/]+)\/([^\/]+)\.git$/;
  const URL_RE = /^https:\/\/github.com\/([^\/]+)\/([^\/]+)(?:\/|$)/;

  const match = GIT_RE.exec(first) || URL_RE.exec(first);
  if (match) {
    return [match[1], match[2]];
  }

  return [args[0], args[1]];
}

const usage = `Usage: ghu [OPTIONS] <owner> <repo> / ghu [OPTIONS] <URL>
OPTIONS:
--protocol
  Values: https | ssh | soh(Default)
--clone
  Execute \`git clone\`
`;

const [owner, repo] = parseOwnerRepo(args);

if (!owner || !repo) {
  process.stderr.write(usage);
  process.exit(1);
}

const protocol = options
  .find((opt) => opt.startsWith("--protocol="))
  ?.split("=")[1];

// Exec `git clone`
const clone = options.includes("--clone");

const url =
  protocol === "https"
    ? `https://github.com/${owner}/${repo}.git`
    : protocol === "ssh"
      ? `git@github.com:${owner}/${repo}.git`
      : `ssh://git@ssh.github.com/${owner}/${repo}.git`;

if (clone) {
  process.stderr.write(`${url}\n`);
  execSync(`git clone ${url}`, { stdio: "inherit" });
} else {
  process.stdout.write(url);
}
