/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useState } from 'react';
import { CROWN_BRAND, getCrownLogoPath, getCrownUiLogoPath } from '../../brand/crownBrandAssets';

export default function CrownLogo({
  variant = 'horizontal',
  placement,
  className = '',
  showTextFallback = true,
  alt = `${CROWN_BRAND.name} - ${CROWN_BRAND.descriptor}`,
}) {
  const src = placement ? getCrownUiLogoPath(placement) : getCrownLogoPath(variant);
  const [imgFailed, setImgFailed] = useState(false);

  useEffect(() => {
    setImgFailed(false);
  }, [src]);

  if ((!src || imgFailed) && showTextFallback) {
    return (
      <span className={`crown-brand-text-fallback ${className}`.trim()}>
        <strong>{CROWN_BRAND.name}</strong>
        <span>{CROWN_BRAND.descriptor}</span>
      </span>
    );
  }

  if (!src || imgFailed) return null;

  return (
    <img
      src={src}
      alt={alt}
      className={`crown-logo crown-logo-${placement || variant} ${className}`.trim()}
      loading="eager"
      decoding="async"
      onError={() => setImgFailed(true)}
    />
  );
}

