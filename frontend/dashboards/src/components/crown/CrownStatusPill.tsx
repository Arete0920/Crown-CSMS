import React from "react";

type CrownStatusPillProps = {
  status: "pass" | "review" | "fail";
  children: React.ReactNode;
};

export function CrownStatusPill({ status, children }: CrownStatusPillProps) {
  return <span className={`crown-status crown-status-${status}`}>{children}</span>;
}
