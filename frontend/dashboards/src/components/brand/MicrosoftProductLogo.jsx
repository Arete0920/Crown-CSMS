import { useEffect, useState } from 'react';
import CrownIcon from '../icons/CrownIcon.jsx';
import { getMicrosoftLogoPath, MICROSOFT_ASSET_POLICY } from '../../brand/microsoftBrandAssets';

const PRODUCT_ICONS = {
  teams: 'chat',
  outlook: 'mail',
  microsoft365: 'dashboard',
  word: 'document',
  excel: 'spreadsheet',
  onedrive: 'cloud',
};

export default function MicrosoftProductLogo({
  product,
  label,
  className = '',
  showTextWhenMissing = true,
}) {
  const src = getMicrosoftLogoPath(product);
  const displayLabel = label || product;
  const [failedSrc, setFailedSrc] = useState(null);
  const imgFailed = failedSrc === src;

  useEffect(() => {
    setFailedSrc(null);
  }, [src]);

  if ((!src || imgFailed) && showTextWhenMissing) {
    return (
      <span
        className={`microsoft-product-approved-fallback ${className}`.trim()}
        title={MICROSOFT_ASSET_POLICY}
        aria-label={displayLabel}
      >
        <CrownIcon name={PRODUCT_ICONS[product] || 'dashboard'} size={18} />
        <span>{displayLabel}</span>
      </span>
    );
  }

  if (!src || imgFailed) return null;

  return (
    <img
      src={src}
      alt={displayLabel}
      width="24"
      height="24"
      className={`microsoft-product-logo microsoft-product-logo-${product} ${className}`.trim()}
      loading="eager"
      decoding="async"
      title={MICROSOFT_ASSET_POLICY}
      onError={() => setFailedSrc(src)}
    />
  );
}
