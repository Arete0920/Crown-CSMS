// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { apiJson } from "../../lib/api";
import ParentRightsPanel from "./ParentRightsPanel";

vi.mock("../../lib/api", () => ({ apiJson: vi.fn() }));

describe("ParentRightsPanel request receipts", () => {
  beforeEach(() => vi.resetAllMocks());
  afterEach(cleanup);

  it.each([
    ["Request Student Data Export", "export"],
    ["Request Data Correction", "correction"],
    ["Request Data Deletion", "deletion"],
  ])("submits %s as JSON and shows its pending receipt", async (label, requestType) => {
    apiJson.mockResolvedValue({
      status: "received",
      request_type: requestType,
      request_id: "42",
    });
    render(<ParentRightsPanel />);
    fireEvent.click(screen.getByRole("button", { name: label }));
    await waitFor(() => {
      expect(screen.getByRole("status").textContent).toContain("reference 42");
    });
    expect(apiJson).toHaveBeenCalledWith("/api/compliance/parent-rights/", {
      method: "POST",
      body: JSON.stringify({ request_type: requestType }),
    });
    expect(screen.getByRole("status").textContent).toContain("School review");
    expect(screen.queryByText("Download My Student Data")).toBeNull();
  });

  it("blocks overlapping submissions until the first receipt arrives", async () => {
    let resolveRequest;
    apiJson.mockReturnValue(new Promise((resolve) => { resolveRequest = resolve; }));
    render(<ParentRightsPanel />);
    fireEvent.click(screen.getByRole("button", { name: "Request Data Deletion" }));
    const exportButton = screen.getByRole("button", { name: "Request Student Data Export" });
    expect(exportButton.disabled).toBe(true);
    fireEvent.click(exportButton);
    expect(apiJson).toHaveBeenCalledTimes(1);
    resolveRequest({ status: "received", request_type: "deletion", request_id: "43" });
    await waitFor(() => expect(exportButton.disabled).toBe(false));
  });

  it("does not claim receipt when the request fails", async () => {
    apiJson.mockRejectedValue(new Error("HTTP 403"));
    render(<ParentRightsPanel />);
    fireEvent.click(screen.getByRole("button", { name: "Request Data Correction" }));
    await waitFor(() => {
      expect(screen.getByRole("status").textContent).toContain("could not be confirmed");
    });
    expect(screen.getByRole("status").textContent).not.toContain("Request received");
  });

  it.each([
    null,
    {},
    { status: "accepted", request_type: "export", request_id: "44" },
    { status: "received", request_type: "deletion", request_id: "44" },
    { status: "received", request_type: "export", request_id: "" },
  ])("rejects an invalid receipt: %j", async (receipt) => {
    apiJson.mockResolvedValue(receipt);
    render(<ParentRightsPanel />);
    fireEvent.click(screen.getByRole("button", { name: "Request Student Data Export" }));
    await waitFor(() => {
      expect(screen.getByRole("status").textContent).toContain("could not be confirmed");
    });
    expect(screen.getByRole("status").textContent).not.toContain("Request received");
  });
});
