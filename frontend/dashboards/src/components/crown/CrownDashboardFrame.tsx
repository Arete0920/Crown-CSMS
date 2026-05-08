import React from "react";
import { CrownPageHeader } from "./CrownPageHeader";

type CrownDashboardFrameProps = {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
};

export function CrownDashboardFrame({
  eyebrow = "CROWN",
  title,
  subtitle,
  action,
  children,
}: CrownDashboardFrameProps) {
  return (
    <main className="crown-page">
      <div className="crown-shell">
        <CrownPageHeader eyebrow={eyebrow} title={title} subtitle={subtitle} action={action} />
        {children}
      </div>
    </main>
  );
}
