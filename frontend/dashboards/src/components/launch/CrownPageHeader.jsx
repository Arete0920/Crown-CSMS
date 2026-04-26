export default function CrownPageHeader({ eyebrow, title, subtitle, note }) {
  return (
    <header className="launch-page-header">
      <div>
        {eyebrow ? <div className="launch-page-eyebrow">{eyebrow}</div> : null}
        <h1>{title}</h1>
        {subtitle ? <p>{subtitle}</p> : null}
      </div>
      {note ? <div className="launch-demo-note">{note}</div> : null}
    </header>
  );
}