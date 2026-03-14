import { describe, expect, it } from "vitest";
import {
  getActiveNavTargetFindings,
  getPlaceholderLikeReadyRoutes,
  getReleaseStateConflicts,
  getUncertifiedOwnedRoutes,
} from "./shellCertification";

describe("shellCertification", () => {
  it("requires every owned route to declare an explicit release state", () => {
    expect(getUncertifiedOwnedRoutes()).toEqual([]);
  });

  it("prevents active nav from targeting unowned or non-ready routes", () => {
    expect(getActiveNavTargetFindings()).toEqual([]);
  });

  it("prevents conflicting release states on the same owned path", () => {
    expect(getReleaseStateConflicts()).toEqual([]);
  });

  it("prevents placeholder-like routes from being marked ready", () => {
    expect(getPlaceholderLikeReadyRoutes()).toEqual([]);
  });
});
