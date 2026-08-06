/**
 * KpiFlipCard — role-specific KPI metric tile with CSS flip.
 *
 * Front (Crown Blue):  label · large value · optional trend delta
 * Back  (Crown Gold):  KPI definition text · clickable data-source link
 *
 * Click anywhere on the card to flip. Link on the back uses stopPropagation
 * so it navigates instead of flipping again.
 *
 * Usage:
 *   <KpiFlipCard
 *     label="Tuition Collected"
 *     value="93.1%"
 *     trend="+6.0% vs last yr"
 *     trendUp
 *     definition="Percentage of billed tuition received as of today, across all active households."
 *     dataSource="Billing Module"
 *     dataHref="/billing"
 *   />
 *
 * Or use the KpiStrip helper for a full row of cards:
 *   <KpiStrip cards={[{ label, value, trend, trendUp, definition, dataSource, dataHref }, ...]} />
 */
import { useState } from 'react';

/* ── Card height (px) — consistent across all dashboards ───────────── */
const H = 138;

export default function KpiFlipCard({
  label,
  value,
  trend,
  trendUp,
  definition,
  dataSource,
  dataHref,
}) {
  const [flipped, setFlipped] = useState(false);

  return (
    <div
      onClick={() => setFlipped((v) => !v)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && setFlipped((v) => !v)}
      aria-pressed={flipped}
      aria-label={`${label}: ${value}. Click to ${flipped ? 'see metric' : 'see definition'}.`}
      style={{
        cursor: 'pointer',
        height: H,
        perspective: 900,
        userSelect: 'none',
        outline: 'none',
      }}
    >
      {/* ── Flip container ────────────────────────────────────────────── */}
      <div
        style={{
          position: 'relative',
          height: '100%',
          transformStyle: 'preserve-3d',
          transition: 'transform 0.42s cubic-bezier(0.4,0.2,0.2,1)',
          transform: flipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
        }}
      >

        {/* ── FRONT — Crown Blue ──────────────────────────────────────── */}
        <div
          aria-hidden={flipped}
          style={{
            backfaceVisibility: 'hidden',
            WebkitBackfaceVisibility: 'hidden',
            position: 'absolute',
            inset: 0,
            background: 'var(--crown-brand)',
            borderRadius: 10,
            padding: '14px 16px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxShadow: '0 2px 8px var(--crown-compat-color-9588d47ed9)',
          }}
        >
          {/* Label */}
          <div style={{
            fontSize: 10,
            fontWeight: 700,
            color: 'var(--crown-compat-color-26eaf932d3)',
            textTransform: 'uppercase',
            letterSpacing: 0.9,
          }}>
            {label}
          </div>

          {/* Value */}
          <div style={{
            fontSize: 34,
            fontWeight: 900,
            color: 'var(--crown-compat-color-f2074b6cef)',
            lineHeight: 1,
            letterSpacing: -0.5,
          }}>
            {value}
          </div>

          {/* Trend + flip hint */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            {trend ? (
              <span style={{
                fontSize: 11,
                fontWeight: 600,
                color: trendUp ? 'var(--crown-compat-color-52cca7c6db)' : 'var(--crown-compat-color-42705fa9a6)',
              }}>
                {trendUp ? '▲' : '▼'} {trend}
              </span>
            ) : <span />}
            <span style={{
              fontSize: 9,
              color: 'var(--crown-compat-color-3d92bff672)',
              letterSpacing: 0.6,
              textTransform: 'uppercase',
            }}>
              TAP ◑
            </span>
          </div>
        </div>

        {/* ── BACK — Crown Gold ───────────────────────────────────────── */}
        <div
          aria-hidden={!flipped}
          style={{
            backfaceVisibility: 'hidden',
            WebkitBackfaceVisibility: 'hidden',
            transform: 'rotateY(180deg)',
            position: 'absolute',
            inset: 0,
            background: 'var(--crown-gold)',
            borderRadius: 10,
            padding: '13px 15px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxShadow: '0 2px 8px var(--crown-compat-color-9588d47ed9)',
          }}
        >
          {/* Label (repeated for orientation) */}
          <div style={{
            fontSize: 10,
            fontWeight: 700,
            color: 'var(--crown-compat-color-7e73c8b211)',
            textTransform: 'uppercase',
            letterSpacing: 0.9,
          }}>
            {label}
          </div>

          {/* Definition */}
          <div style={{
            fontSize: 11,
            color: 'var(--crown-compat-color-f2074b6cef)',
            lineHeight: 1.55,
            flex: 1,
            overflow: 'hidden',
            padding: '6px 0 4px',
          }}>
            {definition}
          </div>

          {/* Data source link */}
          {dataHref ? (
            <a
              href={dataHref}
              onClick={(e) => e.stopPropagation()}
              style={{
                fontSize: 11,
                fontWeight: 700,
                color: 'var(--crown-compat-color-f2074b6cef)',
                textDecoration: 'underline',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 3,
              }}
            >
              → {dataSource || 'View source'}
            </a>
          ) : dataSource ? (
            <div style={{
              fontSize: 10,
              color: 'var(--crown-compat-color-b287e65b63)',
              letterSpacing: 0.3,
            }}>
              Source: {dataSource}
            </div>
          ) : null}
        </div>

      </div>
    </div>
  );
}

/* ── KpiStrip ─────────────────────────────────────────────────────────
 * Convenience row of KpiFlipCard tiles.
 * Accepts an array of card-prop objects; renders them in a responsive grid.
 *
 * Props:
 *   cards   – array of KpiFlipCard prop objects
 *   columns – integer to fix column count (optional; defaults to auto-fit)
 */
export function KpiStrip({ cards = [], columns }) {
  const gridCols = columns
    ? `repeat(${columns}, 1fr)`
    : 'repeat(auto-fit, minmax(148px, 1fr))';

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: gridCols,
      gap: 14,
      marginBottom: 22,
    }}>
      {cards.map((card, i) => (
        <KpiFlipCard key={i} {...card} />
      ))}
    </div>
  );
}
