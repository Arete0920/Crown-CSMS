const DISPLAY_MOJIBAKE_PREFIX = '\u00e2\u20ac';

const DISPLAY_TEXT_REPLACEMENTS = [
  [/\u00e2\u20ac\u201d/g, '\u2014'], // â€” -> —
  [/\u00e2\u20ac\u201c/g, '\u2013'], // â€“ -> –
  [/\u00e2\u20ac\u2122/g, '\u2019'], // â€™ -> ’
  [/\u00e2\u20ac\u0153/g, '\u201c'], // â€œ -> “
  [/\u00e2\u20ac\u00a6/g, '\u2026'], // â€¦ -> …
];

export function normalizeDisplayText(value) {
  if (typeof value !== 'string' || value.length === 0) return value;
  if (!value.includes(DISPLAY_MOJIBAKE_PREFIX)) return value;

  return DISPLAY_TEXT_REPLACEMENTS.reduce(
    (text, [pattern, replacement]) => text.replace(pattern, replacement),
    value,
  );
}

export function containsKnownDisplayMojibake(value) {
  if (typeof value !== 'string' || value.length === 0) return false;
  if (!value.includes(DISPLAY_MOJIBAKE_PREFIX)) return false;

  return DISPLAY_TEXT_REPLACEMENTS.some(([pattern]) => {
    pattern.lastIndex = 0;
    return pattern.test(value);
  });
}
