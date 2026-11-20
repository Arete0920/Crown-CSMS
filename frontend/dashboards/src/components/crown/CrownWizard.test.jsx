// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import CrownWizard from "./CrownWizard.jsx";

afterEach(() => cleanup());

function FirstStep({ goNext }) {
  return (
    <section>
      <h2>Aid Year</h2>
      <button type="button" onClick={goNext}>Continue</button>
    </section>
  );
}

function BucketsStep({ goPrev }) {
  return (
    <section>
      <h2>Aid Buckets</h2>
      <button type="button" onClick={goPrev}>Back</button>
    </section>
  );
}

function LegacyStep({ goBack }) {
  return (
    <section>
      <h2>Legacy Step</h2>
      <button type="button" onClick={goBack}>Back</button>
    </section>
  );
}

describe("CrownWizard back navigation", () => {
  it("returns to Aid Year from an aid step using the goPrev contract", () => {
    render(
      <CrownWizard
        stepComponents={[FirstStep, BucketsStep]}
        stepLabels={["Aid Year", "Aid Buckets"]}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(screen.getByRole("heading", { name: "Aid Buckets" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Back" }));
    expect(screen.getByRole("heading", { name: "Aid Year" })).toBeTruthy();
  });

  it("retains existing goBack support", () => {
    render(
      <CrownWizard
        stepComponents={[FirstStep, LegacyStep]}
        stepLabels={["Aid Year", "Legacy"]}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    fireEvent.click(screen.getByRole("button", { name: "Back" }));
    expect(screen.getByRole("heading", { name: "Aid Year" })).toBeTruthy();
  });
});
