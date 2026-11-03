// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import JirehSGOLoginPage from "./JirehSGOLoginPage.jsx";
import { clearBrowserAuthState, jwtLogin, setAccessToken } from "../utils/authClient.js";
vi.mock("../components/crown/CrownLayout.jsx", () => ({
  default: ({ children, title }) => <main aria-label={title}>{children}</main>,
}));
vi.mock("../utils/authClient.js", () => ({
  clearBrowserAuthState: vi.fn(),
  jwtLogin: vi.fn(),
  setAccessToken: vi.fn(),
}));
beforeEach(() => {
  vi.stubEnv("VITE_LOCAL_DEMO", "1");
});
afterEach(() => {
  cleanup();
  vi.resetAllMocks();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});
describe("SGO separate local fictional login", () => {
  it("does not issue a JWT login before nonempty credentials", () => {
    render(<JirehSGOLoginPage />);
    expect(screen.getByRole("button", { name: "Sign in to fictional SGO" }).disabled).toBe(true);
    expect(jwtLogin).not.toHaveBeenCalled();
  });
  it("uses established JWT login and drops all previous school session context", async () => {
    const assign = vi.fn();
    vi.stubGlobal("location", { assign });
    jwtLogin.mockResolvedValue({ access: "synthetic-family-access" });
    render(<JirehSGOLoginPage />);
    fireEvent.change(screen.getByLabelText("Synthetic account username"), {
      target: { value: "sgo_demo_de_family" },
    });
    fireEvent.change(screen.getByLabelText("Synthetic account password"), {
      target: { value: "fictional-private-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign in to fictional SGO" }));
    await waitFor(() => expect(jwtLogin).toHaveBeenCalledWith({
      username: "sgo_demo_de_family", password: "fictional-private-password",
    }));
    expect(clearBrowserAuthState).toHaveBeenCalledOnce();
    expect(setAccessToken).toHaveBeenCalledWith("synthetic-family-access");
    expect(assign).toHaveBeenCalledWith("/jireh-sgo/intake");
  });
  it("rejects bad credentials without exposing password or new session", async () => {
    jwtLogin.mockRejectedValue(new Error("invalid protected auth response"));
    render(<JirehSGOLoginPage />);
    fireEvent.change(screen.getByLabelText("Synthetic account username"), {
      target: { value: "sgo_demo_pa_processor" },
    });
    fireEvent.change(screen.getByLabelText("Synthetic account password"), {
      target: { value: "secret-synthetic" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign in to fictional SGO" }));
    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(screen.getByRole("alert").textContent).not.toContain("secret-synthetic");
    expect(clearBrowserAuthState).not.toHaveBeenCalled();
    expect(setAccessToken).not.toHaveBeenCalled();
  });
});
