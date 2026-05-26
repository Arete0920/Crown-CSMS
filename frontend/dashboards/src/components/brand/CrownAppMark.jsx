import CrownLogo from './CrownLogo';

export default function CrownAppMark({ className = '', label = 'CROWN' }) {
  return (
    <span className={`crown-app-mark ${className}`.trim()} aria-label={label}>
      <CrownLogo variant="mark" alt="" className="crown-app-mark-image" />
    </span>
  );
}
