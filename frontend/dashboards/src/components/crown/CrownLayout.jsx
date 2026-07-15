import React, { useEffect, useMemo, useState } from "react";
import { authenticatedFetch } from "../../utils/authClient.js";

/**
 * CrownLayout  app shell with permission-derived sidebar + main content area.
 *
 * Props:
 *   title     page heading (h2)
 *   subtitle  secondary line under heading (muted)
 *   right     JSX slotted to the top-right of the page header
 *   children  page body
 */

function getProfile() {
  try {
    const