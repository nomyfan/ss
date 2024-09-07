import process from "node:process";
const argv = process.argv.slice(2);

const packageName = argv[0];

function exit(message, code = 1) {
  process.stderr.write(message);
  process.exit(code);
}

if (!packageName) {
  exit("Usage: sync-npmmirror <package-name>\n");
}

process.stderr.write(`Syncing ${packageName}...\n`);
/**
 * @type {{ ok: boolean, logId: string }}
 */
const syncResp = await fetch(
  `https://registry-direct.npmmirror.com/${packageName}/sync`,
  {
    method: "PUT",
  },
).then((res) => res.json());

if (!syncResp.ok) {
  exit(`Failed to sync: ${syncResp}`);
}

process.stderr.write(`Sync started: ${syncResp.logId}\n`);

const MAX_PULL = 10;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

for (let i = 0; i < MAX_PULL; i++) {
  process.stderr.write(`Checking status... (${i + 1}/${MAX_PULL})\n`);
  /**
   * @type {{ ok: boolean; syncDone: boolean; logUrl: string }}
   */
  const status = await fetch(
    `https://registry-direct.npmmirror.com/express/sync/log/${syncResp.logId}`,
    {
      redirect: "follow",
    },
  ).then((resp) => resp.json());
  if (status.ok && status.syncDone) {
    const log = await fetch(status.logUrl, {
      redirect: "follow",
    }).then((resp) => resp.text());
    process.stdout.write(log);
    break;
  }

  await sleep(5000);
}
