import { useEffect, useState } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import ErrorBanner from '../components/ui/ErrorBanner.jsx';

async function api(path, opts = {}) {
  const base = import.meta.env.VITE_API_BASE_URL || '';
  const res = await fetch(`${base}${path}`, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      ...(opts.headers || {}),
    },
  });
  const text = await res.text();
  let data = null;
  try { data = JSON.parse(text); } catch { data = text; }
  if (!res.ok) throw new Error(typeof data === 'string' ? data : (data.detail || 'Request failed'));
  return data;
}

export default function ServiceHoursPage() {
  const [pending, setPending] = useState([]);
  const [err, setErr] = useState('');

  const load = async () => {
    setErr('');
    try {
      const data = await api('/api/service/approvals/');
      setPending(Array.isArray(data) ? data : []);
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <CrownLayout
      title="Service Hours"
      subtitle="Pending approvals and student service activity"
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h2 style={{ margin: 0, fontSize: 18, color: 'var(--crown-ink)' }}>Pending Approvals</h2>
        <button className="crown-btn" onClick={load}>Refresh</button>
      </div>

      {err ? <ErrorBanner title="Service hours unavailable" message={err} /> : null}

      <div className="crown-card">
        <div style={{ fontSize: 12, color: 'var(--crown-muted)', marginBottom: 10 }}>Pending approvals</div>
        <div style={{ display: 'grid', gap: 8 }}>
            {pending.slice(0, 30).map((x) => (
              <div key={x.id} style={{ border: '1px solid var(--crown-border)', borderRadius: 10, padding: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <div style={{ fontWeight: 700, color: 'var(--crown-ink)' }}>{x.student_name} - {x.hours}h</div>
                  <div style={{ fontSize: 11, color: 'var(--crown-muted)' }}>{x.status}</div>
                </div>
                <div style={{ fontSize: 12, color: 'var(--crown-muted)', marginTop: 4 }}>{x.category} - {x.organization}</div>
                <div style={{ fontSize: 11, color: 'var(--crown-muted)', marginTop: 2 }}>{x.date}</div>
              </div>
            ))}
            {pending.length === 0 ? <div style={{ fontSize: 12, color: 'var(--crown-muted)' }}>No pending items.</div> : null}
        </div>
      </div>
    </CrownLayout>
  );
}
