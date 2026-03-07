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
import { PKPass } from "passkit-generator";

const app = express();
app.use(express.json({ limit: "1mb" }));

function requireEnv(name) {
  const v = process.env[name];
  if (!v) throw new Error(`Missing required env var: ${name}`);
  return v;
}

// Health check
app.get("/health", (_req, res) => res.json({ ok: true, service: "crown-apple-pass" }));

app.post("/pkpass", async (req, res) => {
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
    res.status(500).json({ ok: false, message: String(err?.message || err) });
  }
});

const PORT = Number(process.env.PORT || 7071);
app.listen(PORT, () => {
  console.log(`[apple-pass-service] listening on :${PORT}`);
});
