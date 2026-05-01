import React from "react";

type CrownEmptyStateProps = {
  title: string;
  message: string;
  action?: React.ReactNode;
};

export function CrownEmptyState({ title, message, action }: CrownEmptyStateProps) {
  return (
    <section className="crown-empty-state">
      <h2 className="text-xl font-bold text-slate-900">{title}</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-600">{message}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </section>
  );
}
