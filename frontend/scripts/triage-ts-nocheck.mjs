// Removes every `// @ts-nocheck` line, runs tsc --noEmit once, then restores
// the working tree. Reports tsc error count per file so we can plan PR slicing.
import { spawnSync } from "node:child_process";
import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const NOCHECK_RE = /^\s*\/\/\s*@ts-nocheck\s*\r?\n/m;
const SRC_DIRS = ["app", "components", "lib"];
const SRC_EXT = /\.(ts|tsx|mts|cts)$/;

function walk(dir, out = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, entry.name);
    if (entry.isDirectory()) walk(p, out);
    else if (SRC_EXT.test(entry.name)) out.push(p);
  }
  return out;
}

const candidates = SRC_DIRS.flatMap((d) => walk(d));
const files = candidates.filter((f) =>
  readFileSync(f, "utf8").includes("@ts-nocheck"),
);

console.error(`Found ${files.length} files with @ts-nocheck. Stripping...`);

const originals = new Map();
for (const f of files) {
  const content = readFileSync(f, "utf8");
  originals.set(f, content);
  writeFileSync(f, content.replace(NOCHECK_RE, ""));
}

let tscOutput = "";
try {
  console.error("Running tsc --noEmit (may take ~30s)...");
  const r = spawnSync(
    process.execPath,
    ["./node_modules/typescript/bin/tsc", "--noEmit", "--pretty", "false"],
    { encoding: "utf8", maxBuffer: 50 * 1024 * 1024 },
  );
  tscOutput = (r.stdout || "") + (r.stderr || "");
} finally {
  console.error("Restoring files...");
  for (const [f, content] of originals) writeFileSync(f, content);
}

const errorsByFile = {};
const lineRe = /^(.+?)\((\d+),(\d+)\):\s+error\s+TS\d+:/;
for (const line of tscOutput.split(/\r?\n/)) {
  const m = lineRe.exec(line);
  if (!m) continue;
  const file = m[1].replace(/\\/g, "/").replace(/^.*?\/frontend\//, "");
  errorsByFile[file] = (errorsByFile[file] || 0) + 1;
}

const tracked = new Set(files.map((f) => f.replace(/\\/g, "/")));
const buckets = { zero: [], small: [], medium: [], large: [] };
for (const f of tracked) {
  const n = errorsByFile[f] || 0;
  if (n === 0) buckets.zero.push([f, n]);
  else if (n <= 3) buckets.small.push([f, n]);
  else if (n <= 10) buckets.medium.push([f, n]);
  else buckets.large.push([f, n]);
}
for (const k of Object.keys(buckets)) buckets[k].sort((a, b) => a[1] - b[1]);

const untracked = Object.keys(errorsByFile).filter((f) => !tracked.has(f));
const totalErr = Object.values(errorsByFile).reduce((a, b) => a + b, 0);

console.log(`\n=== Triage summary ===`);
console.log(`@ts-nocheck files: ${files.length}`);
console.log(`Total TS errors after removal: ${totalErr}\n`);
console.log(`zero  (0)     : ${buckets.zero.length}`);
console.log(`small (1-3)   : ${buckets.small.length}`);
console.log(`medium (4-10) : ${buckets.medium.length}`);
console.log(`large (>10)   : ${buckets.large.length}`);

if (untracked.length) {
  console.log(
    `\nErrors in files WITHOUT @ts-nocheck (real regressions to look at): ${untracked.length}`,
  );
  for (const f of untracked) console.log(`  ${errorsByFile[f]}  ${f}`);
}

console.log(`\n--- ZERO-error files (immediate PR candidates) ---`);
for (const [f] of buckets.zero) console.log(`  ${f}`);
console.log(`\n--- SMALL (1-3 errors) ---`);
for (const [f, n] of buckets.small) console.log(`  ${n}  ${f}`);
console.log(`\n--- MEDIUM (4-10 errors) ---`);
for (const [f, n] of buckets.medium) console.log(`  ${n}  ${f}`);
console.log(`\n--- LARGE (>10 errors) ---`);
for (const [f, n] of buckets.large) console.log(`  ${n}  ${f}`);

writeFileSync(
  "triage-report.json",
  JSON.stringify({ buckets, errorsByFile, untracked }, null, 2),
);
console.log(`\nFull report written to triage-report.json`);
