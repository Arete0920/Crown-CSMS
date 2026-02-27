/**
 * WidgetDispatcher — routes a DashboardWidget to the right component.
 * This is the single place to add new widget type mappings.
 */
import React from "react";
import StatWidget from "./StatWidget.jsx";
import FlipWidget from "./FlipWidget.jsx";
import TableWidget from "./TableWidget.jsx";
import QuickActionsWidget from "./QuickActionsWidget.jsx";
import FeedWidget from "./FeedWidget.jsx";
import ChartWidget from "./ChartWidget.jsx";

export default function WidgetDispatcher({ widget, onExpand }) {
  const { type } = widget;

  switch (type) {
    case "stat":
      return <StatWidget widget={widget} onExpand={onExpand} />;
    case "flip":
      return <FlipWidget widget={widget} onExpand={onExpand} />;
    case "table":
      return <TableWidget widget={widget} onExpand={onExpand} />;
    case "actions":
      return <QuickActionsWidget widget={widget} />;
    case "feed":
      return <FeedWidget widget={widget} onExpand={onExpand} />;
    case "chart_line":
    case "chart_donut":
      return <ChartWidget widget={widget} onExpand={onExpand} />;
    default:
      return (
        <div className="crown-card" style={{ height: "100%" }}>
          <div style={{ fontWeight: 800, marginBottom: 8 }}>{widget.title}</div>
          <pre style={{ fontSize: 11, color: "var(--crown-muted)", whiteSpace: "pre-wrap", margin: 0 }}>
            {JSON.stringify(widget.data, null, 2)}
          </pre>
        </div>
      );
  }
}
