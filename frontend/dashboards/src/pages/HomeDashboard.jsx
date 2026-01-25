import React from 'react';

export function HomeDashboard() {
  return (
    <div style={{ padding: 24, fontFamily: 'system-ui, sans-serif' }}>
      <h1>Crown Dashboards</h1>
      <p>
        Routes:
        <ul>
          <li>
            <a href="/billing">Billing</a>
          </li>
        </ul>
      </p>
    </div>
  );
}
