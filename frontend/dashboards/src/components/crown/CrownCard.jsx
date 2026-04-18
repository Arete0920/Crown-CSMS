
/**
 * CrownCard – surface card with optional title + right slot.
 *
 * Props:
 *   title     – card section heading
 *   right     – JSX placed top-right (badges, actions)
 *   className – extra CSS classes appended to ".crown-card"
 *   children  – card body
 */
export default function CrownCard({ title, right, children, className = "" }) {
  return (
    <section className={"crown-card " + className}>
      {(title || right) && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 10,
          }}
        >
          {title ? <div style={{ fontWeight: 800 }}>{title}</div> : <div />}
          {right ? <div>{right}</div> : null}
        </div>
      )}
      {children}
    </section>
  );
}
