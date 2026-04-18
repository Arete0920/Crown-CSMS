import { describe, expect, it } from "vitest";
import SchemaStatusWidget from "../src/components/release/SchemaStatusWidget";

describe("SchemaStatusWidget", () => {
  it("exports a component", () => {
    expect(SchemaStatusWidget).toBeTruthy();
  });
});