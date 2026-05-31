// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { RouterProvider, createMemoryRouter } from "react-router-dom";

import { router } from "../routes/router.jsx";

vi.mock("../components/brand/CrownLogo", () => ({
  default: () => <div>CROWN</div>,
}));

beforeEach(() => {
  vi.restoreAllMocks();
  sessionStorage.clear();
  localStorage.clear();
});

afterEach(() => {
  cleanup();
});

describe("sandbox routes", () => {
  it("renders the sandbox landing page at /sandbox", () => {
    const memoryRouter = createMemoryRouter(router.routes, {
      initialEntries: ["/sandbox"],
    });

    render(<RouterProvider router={memoryRouter} />);

    expect(screen.getAllByRole("heading", { name: "Guided Proof Sandbox" }).length).toBeGreaterThan(0);
  });

  it("renders the sandbox command center at /sandbox/command-center", () => {
    const memoryRouter = createMemoryRouter(router.routes, {
      initialEntries: ["/sandbox/command-center"],
    });

    render(<RouterProvider router={memoryRouter} />);

    expect(screen.getByRole("heading", { name: /Guided proof path|Self-guided sandbox/ })).toBeTruthy();
  });
});