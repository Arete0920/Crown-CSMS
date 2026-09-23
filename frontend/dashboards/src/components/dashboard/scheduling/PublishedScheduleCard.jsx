import { useEffect, useState } from 'react';
import { apiFetch } from '../../../lib/api.js';
import CrownCard from '../../crown/CrownCard.jsx';

export default function PublishedScheduleCard() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    apiFetch('/api/v1/section-scheduler-wizard/sessions/my-schedule/')
      .then(async (response) => {
        if (!response.ok) throw new Error('Your schedule could not be loaded. Please refresh to retry.');
        return response.json();
      })
      .then((data) => { if (active) setRows(data); })
      .catch((exception) => { if (active) setError(exception.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);
  return <CrownCard title="Class schedule">
    {loading && <p role="status">Loading your schedule…</p>}
    {error && <p role="alert">{error}</p>}
    {!loading && !error && !rows.length && <p>No published meetings are available for your account.</p>}
    {!loading && !error && rows.map((section) => <div key={section.section_id}>
      <strong>{section.course.name}</strong>
      <ul>{section.meetings.map((meeting) => <li key={meeting.placement_id}>
        {meeting.template_code} · {meeting.start_time.slice(0, 5)}–{meeting.end_time.slice(0, 5)}
        {meeting.room_code ? ` · Room ${meeting.room_code}` : ''}
      </li>)}</ul>
    </div>)}
  </CrownCard>;
}
