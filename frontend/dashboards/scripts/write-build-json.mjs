/* global process, console */

import fs from "fs";
import path from "path";
import { execSync } from "child_process";

const root = process.cwd();
const dist = path.join(root, "dist");
if (!fs.existsSync(dist)) {
  fs.mkdirSync(dist, { recursive: true });
}

function safe(cmd, fallback = "") {
  try {
    return execSync(cmd, { encoding: "utf8" }).trim();
  } catch {
    return fallback;
  }
}

const build = {
  app: "crown-dashboard",
  build_sha: process.env.GITHUB_SHA || safe("git rev-parse HEAD"),
  build_sha_short: process.env.GITHUB_SHA
    ? process.env.GITHUB_SHA.substring(0, 7)
    : safe("git rev-parse --short HEAD"),
  branch: process.env.GITHUB_REF_NAME || safe("git branch --show-current"),
  deploy_tag: process.env.CROWN_DEPLOY_TAG || process.env.DEPLOY_TAG || "",
  built_at_utc: new Date().toISOString(),
};

fs.writeFileSync(
  path.join(dist, "build.json"),
  JSON.stringify(build, null, 2) + "\n",
  "utf8"
);

console.log("Wrote dist/build.json");
