export const CAMP_SETUP_KEYS = [
  "camp_name", "default_capacity", "default_staff_ratio",
  "public_registration_enabled", "billing_policy",
];

export const CAMP_WIZARD_STEPS = ["Program", "Registration", "Operations", "Review"];

export function readCampWizardState(payload) {
  const wizard = payload?.wizard;
  if (!wizard || !Array.isArray(wizard.completed_steps) ||
      typeof wizard.is_completed !== "boolean" ||
      wizard.completed_steps.length > CAMP_WIZARD_STEPS.length ||
      wizard.completed_steps.some((step, index) => step !== CAMP_WIZARD_STEPS[index]) ||
      (wizard.is_completed && wizard.completed_steps.length !== CAMP_WIZARD_STEPS.length)) {
    throw new Error("Camp setup progress could not be verified. Reload before editing.");
  }
  return {
    completed_steps: [...wizard.completed_steps],
    is_completed: wizard.is_completed,
  };
}

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
  const wizard = readCampWizardState(payload);
  if (CAMP_SETUP_KEYS.some((key) => config[key] !== submitted.config[key]) ||
      wizard.is_completed !== submitted.is_completed ||
      JSON.stringify(wizard.completed_steps) !== JSON.stringify(submitted.completed_steps)) {
    throw new Error("Saved setup does not match the server readback. Reload and reconcile before retrying.");
  }
  return config;
}
