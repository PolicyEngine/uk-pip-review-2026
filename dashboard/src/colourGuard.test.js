import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { describe, expect, it } from "vitest";

// One colour template (docs/COLOURS.md): colour literals live only in
// src/utils/chartTheme.js and the :root tokens of app/globals.css.
const ROOT = resolve(__dirname, "..");
const ALLOWED = new Set(["src/utils/chartTheme.js", "app/globals.css"]);
const HEX = /#[0-9a-fA-F]{3,8}\b/g;

function files(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (name === "node_modules" || name === ".next") return [];
    return statSync(path).isDirectory() ? files(path) : [path];
  });
}

describe("colour guard", () => {
  it("finds no hex colour outside the token files", () => {
    const violations = [];
    for (const path of [...files(join(ROOT, "src")), ...files(join(ROOT, "app"))]) {
      const rel = relative(ROOT, path);
      if (ALLOWED.has(rel) || !/\.(jsx?|css)$/.test(rel) || rel.endsWith(".test.js")) continue;
      const text = readFileSync(path, "utf8").replace(/\/\/.*$/gm, "");
      for (const match of text.match(HEX) ?? []) violations.push(`${rel}: ${match}`);
    }
    expect(violations).toEqual([]);
  });
});
