import { useState } from 'react';
import { getMicrosoftLogoPath, MICROSOFT_ASSET_POLICY } from '../../brand/microsoftBrandAssets';

const FALLBACK_GLYPHS = {
  teams: 'T',
  outlook: 'O',
  microsoft365: 'C',
  word: 'W',
  excel: 'X',
  onedrive: 'D',
};

export default function MicrosoftProductLogo({
  product,
  label,
  className = '',
  showTextWhenMissing = true,
}) {
  const src = getMicrosoftLogoPath(product);
  const displayLabel = label || product;
  const fallbackGlyph = FALLBACK_GLYPHS[product] || String(displayLabel).trim().charAt(0).toUpperCase();
  const [failedSrc, setFailedSrc] = useState(null);
  const imgFailed = failedSrc === src;

  if ((!src || imgFailed) && showTextWhenMissing) {
    return (
      <span
        className={`microsoft-product-text-label ${className}`.trim()}
        title={MICROSOFT_ASSET_POLICY}
        aria-label={displayLabel}
      >
        {fallbackGlyph}
      </span>
    );
  }

  if (!src || imgFailed) return null;

  return (
    <img
      src={src}
      alt={displayLabel}
      className={`microsoft-product-logo microsoft-product-logo-${product} ${className}`.trim()}
      loading="lazy"
      decoding="async"
      title={MICROSOFT_ASSET_POLICY}
      onError={() => setFailedSrc(src)}
    />
  );
}
