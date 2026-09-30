import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import SchoolStorePanel from "./SchoolStorePanel.jsx";
import { apiJson } from "../../lib/api";

vi.mock("../../lib/api", () => ({ apiJson: vi.fn() }));
const product = { id: 7, name: "School shirt", sku: "SHIRT", price_cents: 1999, stock: 3, active: true };
beforeEach(() => vi.clearAllMocks());
afterEach(cleanup);

describe("school store preparation", () => {
  it("uses server totals and keeps payment unavailable", async () => {
    apiJson.mockResolvedValueOnce({ results: [product], count: 1 })
      .mockResolvedValueOnce({ items: [{ product_id: 7, name: "School shirt", quantity: 1, total_cents: 2119 }], subtotal_cents: 1999, tax_cents: 120, total_cents: 2119 });
    render(<SchoolStorePanel />);
    await screen.findByText(/School shirt \(SHIRT\)/);
    fireEvent.click(screen.getByRole("button", { name: "Add to cart" }));
    fireEvent.click(screen.getByRole("button", { name: "Calculate total" }));
    await screen.findByText(/Total \$21.19/);
    expect(apiJson).toHaveBeenLastCalledWith("/api/v1/payments/store/quote/", { method: "POST", body: JSON.stringify({ items: [{ product_id: 7, quantity: 1 }] }) });
    expect(screen.getByRole("button", { name: "Payment collection unavailable" }).disabled).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Clear cart" }));
    expect(screen.queryByText(/Total \$21.19/)).toBeNull();
  });
  it("shows catalog failure and can retry", async () => {
    apiJson.mockRejectedValueOnce(new Error("Access denied"))
      .mockResolvedValueOnce({ results: [product], count: 1 });
    render(<SchoolStorePanel />);
    expect((await screen.findByRole("alert")).textContent).toContain("Access denied");
    await waitFor(() => expect(screen.getByRole("button", { name: "Refresh catalog" }).disabled).toBe(false));
    fireEvent.click(screen.getByRole("button", { name: "Refresh catalog" }));
    await screen.findByText(/School shirt \(SHIRT\)/);
    expect(screen.queryByRole("alert")).toBeNull();
  });
});
