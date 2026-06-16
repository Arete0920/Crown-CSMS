/**
 * DegradationBadge — UI indicator when live data fetch fails and demo data is shown
 * Displays a warning banner at the top of dashboard when `live={false}`
 */
export default function DegradationBadge({ visible = false }) {
  if (!visible) return null;

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      padding: '10px 14px',
      marginBottom: '16px',
      backgroundColor: 'var(--crown-warn-bg, #fff3cd)',
      border: '1px solid var(--crown-warn, #ffc107)',
      borderRadius: '6px',
      fontSize: '13px',
      color: 'var(--crown-ink, #333)',
      fontWeight: 500,
    }}>
      <span style={{ fontSize: '16px' }}>⚠️</span>
      <span>
        <strong>Degraded Mode:</strong> Live data unavailable. Showing cached data. Check browser console for details.
      </span>
    </div>
  );
}
