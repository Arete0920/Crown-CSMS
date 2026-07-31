// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import TicketSuccessPage from "./TicketSuccessPage.jsx";
import {
  PAYMENT_DISABLED_MESSAGE,
  PAYMENT_PROCESSING_ENABLED,
} from "./paymentAvailability.js";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("payment availability", () => {
  it("remains fail-closed until a provider is explicitly authorized", () => {
    expect(PAYMENT_PROCESSING_ENABLED).toBe(false);
  });

  it("renders the disabled state without polling an order", () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockRejectedValue(new Error("must not be called"));

    render(<TicketSuccessPage />);

    screen.getByText("Online payment unavailable");
    screen.getByText(PAYMENT_DISABLED_MESSAGE);
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
