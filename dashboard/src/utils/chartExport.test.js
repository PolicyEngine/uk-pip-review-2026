import { describe, expect, it } from "vitest";
import { chartSvgText } from "./chartExport";

describe("chart export", () => {
  it("wraps the chart's svg with a title on a white background", () => {
    const box = document.createElement("div");
    box.innerHTML = '<svg class="recharts-surface" width="400" height="200"><rect width="10" height="10"/></svg>';
    const built = chartSvgText(box, "Cost & more");
    expect(built.text).toContain("Cost &amp; more");
    expect(built.text).toContain("recharts-surface");
    expect(built.text.startsWith("<svg")).toBe(true);
  });

  it("returns nothing when no chart is drawn", () => {
    expect(chartSvgText(document.createElement("div"), "x")).toBeNull();
  });
});
