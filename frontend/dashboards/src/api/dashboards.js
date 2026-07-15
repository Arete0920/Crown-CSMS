/**
 * dashboards.js — API client for the Crown unified dashboard API.
 * Uses the canonical authenticated client for API-base resolution, credentials,
 * tenant context, bearer authentication, and structured failures.
 */
import { authenticatedFetch } from "../utils/authClient.js";

async function jsonRequest(path, init = {}) {
  try {
    const response = await authenticatedFetch(path, {
      credentials: "include",
      ...init,
    });
    const