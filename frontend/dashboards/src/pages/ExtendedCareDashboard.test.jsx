// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router";
import ExtendedCareDashboard from "./ExtendedCareDashboard.jsx";
import { PATHS } from "../routes/paths.js";

vi.mock("../components/crown/CrownLayout.jsx", () => ({
  default: ({ title, children }) => <main aria-label={title}>{children}</main>,
}));

afterEach(() => cleanup());

function careRoutes() {
  return createMemoryRouter([
    { path: PATHS.EXTENDED_CARE_DASHBOARD, element: <ExtendedCareDashboard /> },
    { path: PATHS.BEFORECARE_DIRECTOR, element: <div>Before Care route reached</div> },
    { path: PATHS.AFTERCARE_DIRECTOR, element: <div>After Care route reached</div> },
  ], { initialEntries: [PATHS.EXTENDED_CARE_DASHBOARD] });
}

describe("Extended Care dashboard presentation and navigation", () => {
  it("uses shared responsive cards for its distinct AM and PM operations", () => {
    const router = careRoutes();
    const { container } = render(<RouterProvider router={router} />);
    expect(screen.getByRole("heading", { name: "Before Care" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "After Care" })).toBeTruthy();
    expect(container.querySelectorAll(".crown-grid > .crown-col-6 .crown-card")).toHaveLength(2);
  });

  it.each([
    ["Open Before Care Director", PATHS.BEFORECARE_DIRECTOR, "Before Care route reached"],
    ["Open After Care Director", PATHS.AFTERCARE_DIRECTOR, "After Care route reached"],
  ])("navigates %s through its actual route link", (label, expectedPath, destination) => {
    const router = careRoutes();
    render(<RouterProvider router={router} />);
    const link = screen.getByRole("link", { name: label });
    expect(link.getAttribute("href")).toBe(expectedPath);
    fireEvent.click(link);
    expect(router.state.location.pathname).toBe(expectedPath);
    expect(screen.getByText(destination)).toBeTruthy();
  });
});
