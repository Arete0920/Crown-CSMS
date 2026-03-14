import { describe, expect, it } from "vitest";
import {
  getDuplicateReadyModuleKeys,
  getFakeReadyRoutes,
  getReadyRoutesMissingRequiredFields,
  getReadyRoutesMissingRequiredFlags,
  getReadyRoutesWithFalseReadinessFlags,
  getReadyRoutesWithPlaceholderSignals,
  getReadyRoutesWithoutConcreteComponent,
} from "./moduleReadiness";

describe("moduleReadiness", () => {
  it("requires every ready route to declare required metadata", () => {
    expect(getReadyRoutesMissingRequiredFields()).toEqual([]);
  });

  it("requires every ready route to have a concrete named component", () => {
    expect(getReadyRoutesWithoutConcreteComponent()).toEqual([]);
  });

  it("requires every ready route to declare all readiness flags", () => {
    expect(getReadyRoutesMissingRequiredFlags()).toEqual([]);
  });

  it("requires every ready route to pass all readiness flags", () => {
    expect(getReadyRoutesWithFalseReadinessFlags()).toEqual([]);
  });

  it("prevents placeholder signals on routes marked ready", () => {
    expect(getReadyRoutesWithPlaceholderSignals()).toEqual([]);
  });

  it("prevents duplicate module keys across ready routes", () => {
    expect(getDuplicateReadyModuleKeys()).toEqual([]);
  });

  it("hard-fails any fake ready route", () => {
    expect(getFakeReadyRoutes()).toEqual([]);
  });
});
