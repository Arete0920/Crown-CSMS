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
import { PKPass } from "passkit-generator";

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

    const serial = String(serialNumber || ticketId);

    // Load cert material (fail fast if not configured)
    const certP12 = fs.readFileSync(requireEnv("APPLE_PASS_CERT_P12_PATH"));
    const certPass = requireEnv("APPLE_PASS_CERT_P12_PASSWORD");
    const wwdr    = fs.readFileSync(requireEnv("APPLE_WWDR_PEM_PATH"));
    const template = requireEnv("APPLE_PASS_TEMPLATE_PATH");
    const passTypeId = requireEnv("APPLE_PASS_TYPE_IDENTIFIER");
    const teamId     = requireEnv("APPLE_TEAM_IDENTIFIER");

    const pass = await PKPass.from(
      { model: template },
      {
        signerCert: certP12,
        signerKeyPassphrase: certPass,
        wwdr,
      }
    );

    // Core identity
    pass.type = "eventTicket";
    pass.serialNumber = serial;
    pass.description = `Ticket – ${eventName}`;
    pass.organizationName = "Crown";
    pass.teamIdentifier = teamId;
    pass.passTypeIdentifier = passTypeId;

    // Barcode (QR)
    pass.setBarcodes(qrValue || serial);

    // Pass fields
    pass.headerFields.push({ key: "event", label: "Event", value: eventName });
    pass.primaryFields.push({ key: "seat",  label: "Seat",  value: seatLabel || "See ticket" });
    pass.secondaryFields.push({
      key:   "email",
      label: "Email",
      value: purchaserEmail,
    });
    pass.auxiliaryFields.push({
      key:   "ticket",
      label: "Ticket ID",
      value: serial.slice(0, 8).toUpperCase(),
    });

    const buffer = pass.getAsBuffer();

    res.setHeader("Content-Type", "application/vnd-apple.pkpass");
    res.setHeader(
      "Content-Disposition",
      `attachment; filename="ticket-${serial.slice(0, 8)}.pkpass"`
    );
    res.send(buffer);
  } catch (err) {
    console.error("[apple-pass-service]", err);
    res.status(500).json({ ok: false, message: "Internal server error" });
  }
});

const PORT = Number(process.env.PORT || 7071);
app.listen(PORT, () => {
  console.log(`[apple-pass-service] listening on :${PORT}`);
});
