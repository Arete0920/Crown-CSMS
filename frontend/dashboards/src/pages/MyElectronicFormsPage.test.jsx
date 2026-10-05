import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";

import MyElectronicFormsPage from "./MyElectronicFormsPage.jsx";
import { apiFetch } from "../lib/api.js";

vi.mock("../lib/api.js", () => ({ apiFetch: vi.fn() }));
vi.mock("../components/crown/CrownLayout.jsx", () => ({
  default: ({ children, title }) => <main aria-label={title}>{children}</main>,
}));
vi.mock("../components/ui/ErrorBanner.jsx", () => ({
  default: ({ message }) => <div role="alert">{message}</div>,
}));

afterEach(cleanup);

function response(body, ok = true, status = ok ? 200 : 400) {
  return {
    ok,
    status,
    text: async () => JSON.stringify(body),
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  let signerStatus = "PENDING";

  apiFetch.mockImplementation(async (url, options = {}) => {
    if (url === "/api/v1/forms/consent-disclosure/") {
      return response({
        version: "crown-electronic-consent-v1",
        text: "Consent disclosure",
        paper_copy_fee: "0.00",
        hardware_software_requirements: "Current browser",
      });
    }

    if (url === "/api/v1/forms/envelopes/my/") {
      return response([
        {
          id: "11111111-1111-1111-1111-111111111111",
          title: "Enrollment Agreement",
          document_sha256: "abcdef0123456789",
          status: "SENT",
          current_signer: {
            display_name: "Pat Reed",
            status: signerStatus,
            signed_at: null,
          },
        },
      ]);
    }

    if (url === "/api/v1/forms/envelopes/11111111-1111-1111-1111-111111111111/") {
      return response({
        id: "11111111-1111-1111-1111-111111111111",
        title: "Enrollment Agreement",
        document_sha256: "abcdef0123456789",
        status: signerStatus === "SIGNED" ? "COMPLETED" : "SENT",
        document_snapshot: {
          template: { title: "Enrollment Agreement", body: "Agreement body" },
          data: { student_name: "Jordan Reed" },
        },
        current_signer: {
          display_name: "Pat Reed",
          status: signerStatus,
          signed_at: signerStatus === "SIGNED" ? "2026-10-05T12:00:00Z" : null,
        },
      });
    }

    if (url.endsWith("/consent/") && options.method === "POST") {
      const payload = JSON.parse(options.body);
      expect(payload).toEqual({
        disclosure_version: "crown-electronic-consent-v1",
        hardware_software_ack: true,
      });
      signerStatus = "CONSENTED";
      return response({ status: "CONSENTED" });
    }

    if (url.endsWith("/sign/") && options.method === "POST") {
      const payload = JSON.parse(options.body);
      expect(payload).toEqual({
        signed_name: "Pat Reed",
        intent_to_sign: true,
      });
      signerStatus = "SIGNED";
      return response({ envelope_status: "COMPLETED" });
    }

    return response({ detail: "Unexpected request" }, false, 404);
  });
});

it("requires consent and explicit signing intent before completing an assigned form", async () => {
  render(<MyElectronicFormsPage />);

  const formButton = await screen.findByRole("button", { name: /Enrollment Agreement/i });
  fireEvent.click(formButton);

  await screen.findByText("Agreement body");
  expect(screen.getByText(/Document SHA-256/i).textContent).toContain("abcdef0123456789");

  const consentButton = screen.getByRole("button", { name: "Consent to electronic records" });
  expect(consentButton.disabled).toBe(true);

  fireEvent.click(screen.getByRole("checkbox", { name: /access, save, or print/i }));
  expect(consentButton.disabled).toBe(false);
  fireEvent.click(consentButton);

  const signatureInput = await screen.findByLabelText("Typed signature");
  expect(signatureInput.value).toBe("Pat Reed");

  const signButton = screen.getByRole("button", { name: "Sign this record" });
  expect(signButton.disabled).toBe(true);
  fireEvent.click(screen.getByRole("checkbox", { name: /intend to sign/i }));
  expect(signButton.disabled).toBe(false);
  fireEvent.click(signButton);

  await waitFor(() => {
    expect(screen.getByText(/Signed/)).toBeTruthy();
  });
});
