import React from "react";

type CrownPageHeaderProps = {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
};

export function CrownPageHeader({
  eyebrow = "CROWN",
  title,
  subtitle,
  action,
}: CrownPageHeaderProps) {
  return (
    <header className="crown-page-header">
      <div>
        <div className="crown-eyebrow">{eyebrow}</div>
        <h1 className="crown-title">{title}</h1>
        {subtitle ? <p className="crown-subtitle">{subtitle}</p> : null}
      </div>
      {action ? <div>{action}</div> : null}
    </header>
  );
}
