import process from "node:process";
import { execSync } from "node:child_process";

const argvs = process.argv.slice(2);

const isOption = (s) => s.startsWith("--");
const options = argvs.filter((arg) => isOption(arg));
const args = argvs.filter((arg) => !isOption(arg));

const owner = args[0];
const repo = args[1];

const usage = `Usage: ghu [OPTIONS] <owner> <repo>
OPTIONS:
--https
  Clone URL in HTTPS protocol.
--git
  Clone URL in git protocol. This is default if you don't specify --https.
--clone
  Execute \`git clone\`
`;

if (!owner) {
  console.error(usage);
  process.exit(1);
}

if (!repo) {
  console.error(usage);
  process.exit(1);
}

const https = options.includes("--https");
// Exec `git clone`
const clone = options.includes("--clone");

const url = https
  ? `https://github.com/${owner}/${repo}.git`
  : `git@github.com:${owner}/${repo}.git`;

if (clone) {
  execSync(`git clone ${url}`);
} else {
  process.stdout.write(url);
  process.stderr.write("\n");
}
