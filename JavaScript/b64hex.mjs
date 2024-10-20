import * as process from "node:process";

let buffer = process.argv.slice(2).shift() ?? "";
if (!buffer) {
  for await (const chunk of process.stdin) {
    buffer += chunk;
  }
}

buffer = buffer.replace(/^sha\d{3}-/i, "");
const hex = Buffer.from(buffer, "base64").toString("hex");
process.stdout.write(hex);
