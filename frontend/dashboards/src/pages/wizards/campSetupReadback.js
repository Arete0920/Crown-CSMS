export const CAMP_SETUP_KEYS = [
  "camp_name", "default_capacity", "default_staff_ratio",
  "public_registration_enabled", "billing_policy",
];

export function readCampSetup(payload) {
  const config = payload?.config;
  if (!config || typeof config.camp_name !== "string" || !config.camp_name.trim() ||
      !Number.isSafeInteger(config.default_capacity) || config.default_capacity < 1 ||
      !Number.isSafeInteger(config.default_staff_ratio) || config.default_staff_ratio < 1 ||
      typeof config.public_registration_enabled !== "boolean" ||
      !["PER_SESSION", "PER_WEEK", "FULL_CAMP"].includes(config.billing_policy)) {
    throw new Error("Camp setup could not be verified. Reload before editing.");
  }
  return Object.fromEntries(CAMP_SETUP_KEYS.map((key) => [key, config[key]]));
}

export function verifyCampSetupReadback(payload, submitted) {
  const config = readCampSetup(payload);
  if (CAMP_SETUP_KEYS.some((key) => config[key] !== submitted.config[key]) ||
      payload.wizard?.is_completed !== submitted.is_completed ||
      JSON.stringify(payload.wizard?.completed_steps) !== JSON.stringify(submitted.completed_steps)) {
    throw new Error("Saved setup does not match the server readback. Reload and reconcile before retrying.");
  }
  return config;
}
