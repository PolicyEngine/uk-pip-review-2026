import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("pre-release page", () => {
  it("is noindex in the layout metadata", () => {
    const layout = readFileSync(resolve(__dirname, "../app/layout.jsx"), "utf8");
    expect(layout).toMatch(/robots:\s*\{\s*index:\s*false,\s*follow:\s*false/);
  });
});
