export function validateDashboardRegistry(registry) {
  if (!Array.isArray(registry)) {
    throw new Error('DASHBOARD_REGISTRY must be an array.');
  }

  const seenKeys = new Set();
  const seenPaths = new Set();
  const seenLabels = new Set();

  registry.forEach((item, index) => {
    const prefix = `Dashboard registry item at index ${index}`;

    if (!item || typeof item !== 'object') {
      throw new Error(`${prefix} is not a valid object.`);
    }

    if (!item.key || typeof item.key !== 'string') {
      throw new Error(`${prefix} is missing a valid "key".`);
    }

    if (!item.label || typeof item.label !== 'string') {
      throw new Error(`${prefix} is missing a valid "label".`);
    }

    if (!item.path || typeof item.path !== 'string' || !item.path.startsWith('/')) {
      throw new Error(`${prefix} is missing a valid "path" starting with "/".`);
    }

    if (!item.section || typeof item.section !== 'string') {
      throw new Error(`${prefix} is missing a valid "section".`);
    }

    if (!Number.isInteger(item.tier) || item.tier < 1) {
      throw new Error(`${prefix} is missing a valid integer "tier".`);
    }

    if (!Array.isArray(item.allowedRoles) || item.allowedRoles.length === 0) {
      throw new Error(`${prefix} must define at least one allowed role.`);
    }

    if (typeof item.component !== 'function') {
      throw new Error(`${prefix} must provide a valid React component reference.`);
    }

    if (seenKeys.has(item.key)) {
      throw new Error(`Duplicate dashboard key detected: "${item.key}"`);
    }

    if (seenPaths.has(item.path)) {
      throw new Error(`Duplicate dashboard path detected: "${item.path}"`);
    }

    if (seenLabels.has(item.label)) {
      throw new Error(`Duplicate dashboard label detected: "${item.label}"`);
    }

    seenKeys.add(item.key);
    seenPaths.add(item.path);
    seenLabels.add(item.label);
  });

  return true;
}
