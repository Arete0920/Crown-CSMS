import { useState, useCallback } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import { apiFetch } from '../lib/api.js';

const BASE_URL = 'api/v1/enrollment-period-wizard/sessions/';

const GRADE_OPTIONS = [
  { code: 'PK', label: 'Pre-K' },
  { code: 'K',  label: 'Kindergarten' },
  { code: '1',  label: 'Grade 1' },
  { code: '2',  label: 'Grade 2' },
  { code: '3',  label: 'Grade 3' },
  { code: '4',  label: 'Grade 4' },
  { code: '5',  label: 'Grade 5' },
  { code: '6',  label: 'Grade 6' },
  { code: '7',  label: 'Grade 7' },
  { code: '8',  label: 'Grade 8' },
  { code: '9',  label: 'Grade 9' },
  { code: '10', label: 'Grade 10' },
  { code: '11', label: 'Grade 11' },
  { code: '12', label: 'Grade 12' },
];

const USED_CODES = (rows) => new Set(rows.map((r) => r.grade_code));

function emptyCapRow() {
  return { grade_code: '', target_seats: 0, new_students_allowed: true };
}

export default function EnrollmentPeriodWizard() {
  // -- Phase: 'configure' | 'capacities' | 'done'
  const [phase, setPhase] = useState('configure');

  // -- Session
  const [sessionId, setSessionId] = useState(null);

  // -- Configure phase fields
  const [academicYearId, setAcademicYearId] = useState('');
  const [openDate, setOpenDate]             = useState('');
  const [closeDate, setCloseDate]           = useState('');
  const [reenrollCloseDate, setReenrollCloseDate] = useState('');
  const [reenrollFirst, setReenrollFirst]   = useState(false);

  // -- Capacities phase
  const [capRows, setCapRows] = useState([emptyCapRow()]);

  // -- Done phase
  const [result, setResult] = useState(null);

  // -- Error/loading
  const [error, setError]     = useState('');
  const [loading, setLoading] = useState(false);

  // -----------------------------------------
  // PHASE 1 — CONFIGURE
  // -----------------------------------------

  const handleConfigure = useCallback(async () => {
    setError('');
    setLoading(true);
    try {
      // 1a. Create session
      const createRes = await apiFetch(BASE_URL, { method: 'POST' });
      if (!createRes.ok) {
        const body = await createRes.json().catch(() => ({}));
        throw new Error(body.error || `Create failed (${createRes.status})`);
      }
      const { session_id } = await createRes.json();
      setSessionId(session_id);

      // 1b. Configure
      const payload = {
        academic_year_id: academicYearId.trim(),
        open_date:        openDate,
        close_date:       closeDate,
        reenroll_first:   reenrollFirst,
      };
      if (reenrollCloseDate) payload.reenroll_close_date = reenrollCloseDate;

      const cfgRes = await apiFetch(`${BASE_URL}${session_id}/configure/`, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      const cfgBody = await cfgRes.json();
      if (!cfgRes.ok) {
        const msgs = cfgBody.errors || [cfgBody.error] || ['Configure failed'];
        throw new Error(Array.isArray(msgs) ? msgs.join(' · ') : msgs);
      }

      setPhase('capacities');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [academicYearId, openDate, closeDate, reenrollCloseDate, reenrollFirst]);

  // -----------------------------------------
  // PHASE 2 — CAPACITIES
  // -----------------------------------------

  const addCapRow = () => setCapRows((prev) => [...prev, emptyCapRow()]);

  const removeCapRow = (idx) =>
    setCapRows((prev) => prev.filter((_, i) => i !== idx));

  const updateCapRow = (idx, field, value) =>
    setCapRows((prev) =>
      prev.map((row, i) => (i === idx ? { ...row, [field]: value } : row)),
    );

  const handleSetCapacities = useCallback(async () => {
    setError('');
    setLoading(true);
    try {
      // POST capacities
      const capsRes = await apiFetch(`${BASE_URL}${sessionId}/capacities/`, {
        method: 'POST',
        body: JSON.stringify({
          capacities: capRows.map((r) => ({
            grade_code:           r.grade_code,
            target_seats:         parseInt(r.target_seats, 10) || 0,
            new_students_allowed: r.new_students_allowed,
          })),
        }),
      });
      const capsBody = await capsRes.json();
      if (!capsRes.ok) {
        const msgs = capsBody.errors || [capsBody.error] || ['Capacities failed'];
        throw new Error(Array.isArray(msgs) ? msgs.join(' · ') : msgs);
      }

      // Commit
      const commitRes = await apiFetch(`${BASE_URL}${sessionId}/commit/`, { method: 'POST' });
      const commitBody = await commitRes.json();
      if (!commitRes.ok) {
        throw new Error(commitBody.error || `Commit failed (${commitRes.status})`);
      }

      // Verify
      await apiFetch(`${BASE_URL}${sessionId}/verify/`);

      setResult(commitBody.result);
      setPhase('done');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [sessionId, capRows]);

  // -----------------------------------------
  // RENDER
  // -----------------------------------------

  const usedCodes = USED_CODES(capRows);

  return (
    <CrownLayout
      title="Enrollment Period Setup"
      subtitle="Wizard #16 — Define the enrollment window and grade-level capacity targets for an academic year."
    >
      {/* -- PHASE: configure -- */}
      {phase === 'configure' && (
        <div style={{ maxWidth: 560 }}>
          <h2 style={{ marginBottom: 24 }}>Step 1: Configure Enrollment Window</h2>

          <label style={labelStyle}>
            Academic Year ID
            <input
              type="text"
              value={academicYearId}
              onChange={(e) => setAcademicYearId(e.target.value)}
              placeholder="Paste the UUID from Wizard #15"
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Enrollment Opens
            <input
              type="date"
              value={openDate}
              onChange={(e) => setOpenDate(e.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Enrollment Closes
            <input
              type="date"
              value={closeDate}
              onChange={(e) => setCloseDate(e.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Re-enrollment Close Date <span style={{ color: 'var(--crown-muted)', fontWeight: 400 }}>(optional)</span>
            <input
              type="date"
              value={reenrollCloseDate}
              onChange={(e) => setReenrollCloseDate(e.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={{ ...labelStyle, flexDirection: 'row', alignItems: 'center', gap: 12 }}>
            <input
              type="checkbox"
              checked={reenrollFirst}
              onChange={(e) => setReenrollFirst(e.target.checked)}
            />
            Re-enrollment opens first (before new students)
          </label>

          {error && <p style={errorStyle}>{error}</p>}

          <button
            onClick={handleConfigure}
            disabled={loading || !academicYearId || !openDate || !closeDate}
            style={btnStyle}
          >
            {loading ? 'Saving…' : 'Next: Set Capacities ?'}
          </button>
        </div>
      )}

      {/* -- PHASE: capacities -- */}
      {phase === 'capacities' && (
        <div style={{ maxWidth: 720 }}>
          <h2 style={{ marginBottom: 8 }}>Step 2: Grade Capacities</h2>
          <p style={{ color: 'var(--crown-muted)', marginBottom: 24 }}>
            Set target seat counts per grade. Each grade code may only appear once.
          </p>

          <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: 16 }}>
            <thead>
              <tr style={{ background: 'var(--crown-surface-2)' }}>
                <th style={thStyle}>Grade</th>
                <th style={thStyle}>Target Seats</th>
                <th style={thStyle}>New Students Allowed</th>
                <th style={thStyle}></th>
              </tr>
            </thead>
            <tbody>
              {capRows.map((row, idx) => (
                <tr key={idx}>
                  <td style={tdStyle}>
                    <select
                      value={row.grade_code}
                      onChange={(e) => updateCapRow(idx, 'grade_code', e.target.value)}
                      style={{ ...inputStyle, margin: 0 }}
                    >
                      <option value="">— select —</option>
                      {GRADE_OPTIONS.map((g) => (
                        <option
                          key={g.code}
                          value={g.code}
                          disabled={usedCodes.has(g.code) && g.code !== row.grade_code}
                        >
                          {g.label}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td style={tdStyle}>
                    <input
                      type="number"
                      min={0}
                      value={row.target_seats}
                      onChange={(e) => updateCapRow(idx, 'target_seats', e.target.value)}
                      style={{ ...inputStyle, margin: 0, width: 90 }}
                    />
                  </td>
                  <td style={{ ...tdStyle, textAlign: 'center' }}>
                    <input
                      type="checkbox"
                      checked={row.new_students_allowed}
                      onChange={(e) => updateCapRow(idx, 'new_students_allowed', e.target.checked)}
                    />
                  </td>
                  <td style={tdStyle}>
                    {capRows.length > 1 && (
                      <button
                        onClick={() => removeCapRow(idx)}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--crown-danger)', fontSize: 18 }}
                      >
                        ?
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <button onClick={addCapRow} style={{ ...btnStyle, background: 'var(--crown-muted)', marginRight: 12 }}>
            + Add Grade
          </button>

          {error && <p style={errorStyle}>{error}</p>}

          <button
            onClick={handleSetCapacities}
            disabled={loading || capRows.some((r) => !r.grade_code)}
            style={btnStyle}
          >
            {loading ? 'Committing…' : 'Commit Enrollment Period ?'}
          </button>
        </div>
      )}

      {/* -- PHASE: done -- */}
      {phase === 'done' && result && (
        <div style={{ maxWidth: 560 }}>
          <h2 style={{ color: 'var(--crown-ok)', marginBottom: 16 }}>? Enrollment Period Committed</h2>
          <p>{result.message}</p>

          <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 20 }}>
            <tbody>
              {[
                ['Academic Year',     result.academic_year_name],
                ['Open Date',         result.open_date],
                ['Close Date',        result.close_date],
                ['Re-enroll Closes',  result.reenroll_close_date || '—'],
                ['Re-enroll First',   result.reenroll_first ? 'Yes' : 'No'],
                ['Grades Created',    result.capacities_created],
                ['Grades Updated',    result.capacities_updated],
                ['Period ID',         result.enrollment_period_id],
              ].map(([label, val]) => (
                <tr key={label}>
                  <td style={{ padding: '6px 12px', fontWeight: 600, background: 'var(--crown-surface-2)', width: '40%' }}>{label}</td>
                  <td style={{ padding: '6px 12px', fontFamily: 'monospace' }}>{val}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <button
            onClick={() => {
              setPhase('configure');
              setSessionId(null);
              setAcademicYearId('');
              setOpenDate('');
              setCloseDate('');
              setReenrollCloseDate('');
              setReenrollFirst(false);
              setCapRows([emptyCapRow()]);
              setResult(null);
              setError('');
            }}
            style={{ ...btnStyle, marginTop: 24, background: 'var(--crown-muted)' }}
          >
            Start Another Enrollment Period
          </button>
        </div>
      )}
    </CrownLayout>
  );
}

// -- Styles --
const labelStyle = {
  display: 'flex',
  flexDirection: 'column',
  fontWeight: 600,
  marginBottom: 16,
  fontSize: 14,
  gap: 4,
};
const inputStyle = {
  padding: '8px 10px',
  fontSize: 14,
  border: '1px solid var(--crown-border)',
  borderRadius: 4,
  marginTop: 4,
  width: '100%',
  boxSizing: 'border-box',
};
const btnStyle = {
  padding: '10px 22px',
  background: 'var(--crown-brand)',
  color: 'var(--crown-surface)',
  border: 'none',
  borderRadius: 4,
  cursor: 'pointer',
  fontSize: 15,
  fontWeight: 600,
  marginTop: 8,
};
const errorStyle = { color: 'var(--crown-danger)', marginTop: 8, fontSize: 14 };
const thStyle = { padding: '8px 10px', textAlign: 'left', borderBottom: '2px solid var(--crown-border)', fontSize: 13 };
const tdStyle = { padding: '6px 8px', borderBottom: '1px solid var(--crown-border)' };

