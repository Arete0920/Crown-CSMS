import CrownLogo from './CrownLogo';
import { CROWN_BRAND } from '../../brand/crownBrandAssets';

export default function BrandLockup({
  placement = 'sidebarExpanded',
  compact = false,
  className = '',
}) {
  if (compact) {
    return (
      <div className={`crown-brand-lockup is-compact ${className}`.trim()}>
        <CrownLogo variant="mark" alt={`${CROWN_BRAND.name} mark`} />
      </div>
    );
  }

  return (
    <div className={`crown-brand-lockup ${className}`.trim()}>
      <CrownLogo placement={placement} />
      <span className="crown-brand-sr-only">
        <span>{CROWN_BRAND.name}</span>
        <span>{CROWN_BRAND.descriptor}</span>
      </span>
    </div>
  );
}
