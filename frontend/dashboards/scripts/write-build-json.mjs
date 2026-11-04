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
    return execSync(cmd, { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
  } catch {
    return fallback;
  }
}

const ownGit = fs.existsSync(path.resolve(root, "../..", ".git"));
const buildSha = process.env.VITE_BUILD_SHA || process.env.BUILD_SHA || process.env.GITHUB_SHA || (ownGit ? safe("git rev-parse HEAD") : "");
if (!/^[0-9a-f]{40}$/i.test(buildSha)) throw new Error("Build provenance requires an exact 40-character source SHA");
const build = {
  app: "crown-dashboard",
  build_sha: buildSha,
  build_sha_short: buildSha.substring(0, 7),
  branch: process.env.GITHUB_REF_NAME || (ownGit ? safe("git branch --show-current") : ""),
  deploy_tag: process.env.CROWN_DEPLOY_TAG || process.env.DEPLOY_TAG || "",
  built_at_utc: new Date().toISOString(),
};

fs.writeFileSync(
  path.join(dist, "build.json"),
  JSON.stringify(build, null, 2) + "\n",
  "utf8"
);

console.log("Wrote dist/build.json");
