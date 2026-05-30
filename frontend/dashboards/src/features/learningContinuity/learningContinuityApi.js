import {
  CROWN_AUTHORITY_RULES,
  getLearningContinuityTruth,
} from "./learningContinuityTruth.js";

const API_BASE = "/api/v1/learning-continuity/pages";

function normalizePagePayload(pageKey, payload) {
  const fallback = getLearningContinuityTruth(pageKey);

  if (!payload || typeof payload !== "object") {
    return fallback;
  }

  return {
    ...fallback,
    ...payload,
    pageKey,
  };
}

export async function loadLearningContinuityPage(pageKey) {
  try {
    const response = await globalThis.fetch(`${API_BASE}/${pageKey}/`, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      credentials: "include",
    });

    if (!response.ok) {
      throw new Error(`Learning continuity API unavailable: ${response.status}`);
    }

    const payload = await response.json();
    const { authorityRules, ...pagePayload } = payload;

    return {
      mode: "api",
      authorityRules: Array.isArray(authorityRules)
        ? authorityRules
        : CROWN_AUTHORITY_RULES,
      page: normalizePagePayload(pageKey, pagePayload),
      statusDetail: "Live contract loaded from CROWN backend.",
    };
  } catch (error) {
    console.warn("Learning continuity API fallback engaged", {
      pageKey,
      message: error instanceof Error ? error.message : String(error),
    });

    return {
      mode: "fixture",
      authorityRules: CROWN_AUTHORITY_RULES,
      page: getLearningContinuityTruth(pageKey),
      statusDetail: error instanceof Error
        ? `Backend unavailable; showing fixture fallback. ${error.message}`
        : "Backend unavailable; showing fixture fallback.",
    };
  }
}
