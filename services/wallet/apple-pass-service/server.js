import { createHash, X509Certificate } from "node:crypto";
import { execFileSync } from "node:child_process";
import os from "node:os";
import path from "node:path";
import { zipSync } from "fflate";

// Apple PassKit: SHA-1 file manifest, detached DER CMS signature, ZIP package.
// Signing uses maintained system OpenSSL; passwords never enter command arguments.
export function createPass(options) {
  const { template, certP12, certPass, wwdr, passTypeId, teamId, serial,
    eventName, purchaserEmail, seatLabel, qrValue } = options;
  const files = Object.create(null);
  function collect(directory, prefix = "") {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      const name = prefix + entry.name;
      if (entry.name.startsWith(".") || ["manifest.json", "signature", "README.md"].includes(name)) continue;
      if (entry.isSymbolicLink()) throw new Error("Template symlinks are forbidden");
      const target = path.join(directory, entry.name);
      if (entry.isDirectory()) collect(target, name + "/");
      else if (entry.isFile() && (name === "pass.json" || /\.(png|strings)$/.test(name))) files[name] = fs.readFileSync(target);
    }
  }
  collect(template);
  if (!files["icon.png"] || !files["icon@2x.png"]) throw new Error("Pass icons are required");
  const pass = JSON.parse(files["pass.json"].toString());
  if (pass.formatVersion !== 1 || !pass.eventTicket) throw new Error("Event ticket template required");
  Object.assign(pass, { serialNumber: serial, description: `Ticket – ${eventName}`,
    organizationName: "Crown", teamIdentifier: teamId, passTypeIdentifier: passTypeId });
  pass.barcodes = [{ format: "PKBarcodeFormatQR", message: String(qrValue || serial), messageEncoding: "utf-8" }];
  Object.assign(pass.eventTicket, {
    headerFields: [{ key: "event", label: "Event", value: eventName }],
    primaryFields: [{ key: "seat", label: "Seat", value: seatLabel || "See ticket" }],
    secondaryFields: [{ key: "email", label: "Email", value: purchaserEmail }],
    auxiliaryFields: [{ key: "ticket", label: "Ticket ID", value: serial.slice(0, 8).toUpperCase() }],
  });
  files["pass.json"] = Buffer.from(JSON.stringify(pass));
  files["manifest.json"] = Buffer.from(JSON.stringify(Object.fromEntries(
    Object.entries(files).map(([name, bytes]) => [name, createHash("sha1").update(bytes).digest("hex")]),
  )));
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "crown-pass-"));
  const target = name => path.join(directory, name);
  const write = (name, bytes) => fs.writeFileSync(target(name), bytes, { mode: 0o600 });
  const openssl = (args, input) => execFileSync("openssl", args, {
    input, timeout: 10_000, maxBuffer: 4 * 1024 * 1024, stdio: ["pipe", "pipe", "pipe"],
  });
  try {
    if (/[\r\n]/.test(certPass)) throw new Error("Invalid certificate password");
    write("signer.p12", certP12);
    write("wwdr.pem", wwdr);
    openssl(["pkcs12", "-in", target("signer.p12"), "-clcerts", "-nokeys",
      "-out", target("cert.pem"), "-passin", "stdin"], certPass + "\n");
    openssl(["pkcs12", "-in", target("signer.p12"), "-nocerts", "-nodes",
      "-out", target("key.pem"), "-passin", "stdin"], certPass + "\n");
    fs.chmodSync(target("key.pem"), 0o600);
    const certificate = new X509Certificate(fs.readFileSync(target("cert.pem")));
    const subject = Object.fromEntries(certificate.subject.split("\n").map(line => {
      const separator = line.indexOf("="); return [line.slice(0, separator), line.slice(separator + 1)];
    }));
    if (subject.UID !== passTypeId || subject.OU !== teamId) throw new Error("Certificate identity mismatch");
    openssl(["verify", "-partial_chain", "-trusted", target("wwdr.pem"), target("cert.pem")]);
    write("manifest.json", files["manifest.json"]);
    files.signature = openssl(["cms", "-sign", "-binary", "-in", target("manifest.json"),
      "-signer", target("cert.pem"), "-inkey", target("key.pem"), "-certfile", target("wwdr.pem"),
      "-outform", "DER", "-md", "sha256", "-nosmimecap"]);
    return Buffer.from(zipSync(files));
  } catch {
    throw new Error("Pass signing failed; check certificate, identity and OpenSSL configuration");
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
}

/**
 * Crown Apple Wallet Pass Microservice
 *
 * POST /pkpass   { serialNumber, eventName, ticketId, purchaserEmail,
 *                  seatLabel, qrValue }
 *   → streams a signed .pkpass file
 *
 * Required env vars (mount via Docker secrets / env file, never committed):
 *   APPLE_PASS_TYPE_IDENTIFIER   e.g. pass.com.yourorg.crown
 *   APPLE_TEAM_IDENTIFIER        e.g. A1B2C3D4E5
 *   APPLE_PASS_CERT_P12_PATH     absolute path to the p12 signing cert
 *   APPLE_PASS_CERT_P12_PASSWORD passphrase for the p12 file
 *   APPLE_WWDR_PEM_PATH          absolute path to Apple WWDR G4 (or G3) pem
 *   APPLE_PASS_TEMPLATE_PATH     absolute path to the pass template folder
 *   PORT                         (optional, default 7071)
 */

import express from "express";
import fs from "fs";
import rateLimit from "express-rate-limit";
import { pathToFileURL } from "node:url";

const app = express();
app.use(express.json({ limit: "1mb" }));
app.set("trust proxy", 1);

const configuredWindowMs = Number(process.env.PKPASS_RATE_WINDOW_MS);
const configuredMax = Number(process.env.PKPASS_RATE_MAX_REQUESTS);
const RATE_WINDOW_MS = Number.isFinite(configuredWindowMs) && configuredWindowMs > 0
  ? configuredWindowMs
  : 60_000;
const RATE_MAX_REQUESTS = Number.isFinite(configuredMax) && configuredMax > 0
  ? configuredMax
  : 30;

function requireEnv(name) {
  const v = process.env[name];
  if (!v) throw new Error(`Missing required env var: ${name}`);
  return v;
}

// Health check
app.get("/health", (_req, res) => res.json({ ok: true, service: "crown-apple-pass" }));

const pkpassRateLimiter = rateLimit({
  windowMs: RATE_WINDOW_MS,
  limit: RATE_MAX_REQUESTS,
  standardHeaders: true,
  legacyHeaders: false,
  message: { ok: false, message: "Too many requests" },
});

app.post("/pkpass", pkpassRateLimiter, async (req, res) => {
  try {
    const {
      serialNumber,
      eventName = "Crown Event",
      ticketId,
      purchaserEmail = "",
      seatLabel = "",
      qrValue,
    } = req.body;

    if (!ticketId && !serialNumber) {
      return res.status(400).json({ ok: false, message: "ticketId is required" });
    }

    if ([eventName, purchaserEmail, seatLabel].some(value => typeof value !== "string") ||
        (qrValue != null && typeof qrValue !== "string")) {
      return res.status(400).json({ ok: false, message: "Ticket fields must be strings" });
    }
    const serial = String(serialNumber || ticketId);

    // Load cert material (fail fast if not configured)
    const certP12 = fs.readFileSync(requireEnv("APPLE_PASS_CERT_P12_PATH"));
    const certPass = requireEnv("APPLE_PASS_CERT_P12_PASSWORD");
    const wwdr    = fs.readFileSync(requireEnv("APPLE_WWDR_PEM_PATH"));
    const template = requireEnv("APPLE_PASS_TEMPLATE_PATH");
    const passTypeId = requireEnv("APPLE_PASS_TYPE_IDENTIFIER");
    const teamId     = requireEnv("APPLE_TEAM_IDENTIFIER");

    const buffer = createPass({
      template, certP12, certPass, wwdr, passTypeId, teamId,
      serial, eventName, purchaserEmail, seatLabel, qrValue,
    });

    res.setHeader("Content-Type", "application/vnd-apple.pkpass");
    res.setHeader(
      "Content-Disposition",
      `attachment; filename="ticket-${serial.slice(0, 8)}.pkpass"`
    );
    res.send(buffer);
  } catch (err) {
    console.error("[apple-pass-service] pass generation failed");
    res.status(500).json({ ok: false, message: "Internal server error" });
  }
});

const PORT = Number(process.env.PORT || 7071);
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) app.listen(PORT, () => {
  console.log(`[apple-pass-service] listening on :${PORT}`);
});
