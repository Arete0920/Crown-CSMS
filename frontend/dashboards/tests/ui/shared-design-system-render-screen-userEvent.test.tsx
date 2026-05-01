// @vitest-environment jsdom
import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CrownDashboardFrame } from "../../src/components/crown/CrownDashboardFrame";
import { CrownKpiCard } from "../../src/components/crown/CrownKpiCard";

describe("shared design system smoke", () => {
	it("renders the shared CROWN dashboard frame and KPI content", () => {
		render(
			<CrownDashboardFrame
				eyebrow="CROWN"
				title="Shared Design System"
				subtitle="Smoke coverage for the shared dashboard shell."
			>
				<section className="crown-grid crown-grid-2">
					<CrownKpiCard label="Readiness" value="1" context="Smoke test" status="pass" />
				</section>
			</CrownDashboardFrame>
		);

		expect(screen.getByText("Shared Design System")).toBeTruthy();
		expect(screen.getByText("Smoke coverage for the shared dashboard shell.")).toBeTruthy();
		expect(screen.getByText("Readiness")).toBeTruthy();
		expect(screen.getByText("On Track")).toBeTruthy();
	});
});

