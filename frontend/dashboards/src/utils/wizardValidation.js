export function getMissingRequiredFields(values, fields) {
  return fields.filter((field) => {
    const value = values?.[field];
    return value == null || String(value).trim() === '';
  });
}

export function validateRequired(values, fields) {
  const missing = getMissingRequiredFields(values, fields);

  return {
    valid: missing.length === 0,
    missing,
  };
}
