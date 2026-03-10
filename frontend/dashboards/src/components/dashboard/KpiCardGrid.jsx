export default function KpiCardGrid({ children }) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
        gap: 14,
      }}
    >
      {children}
    </div>
  );
}
