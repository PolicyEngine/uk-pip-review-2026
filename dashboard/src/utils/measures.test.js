import { describe, expect, it } from "vitest";
import results from "../../public/data/results.json";
import { waterfallRows } from "../components/WaterfallChart";
import { catalogue, formatMillions, toCsv, totalByYear } from "./measures";

describe("measure utils", () => {
  it("gives a colour to computable measures only", () => {
    for (const m of catalogue(results)) expect(Boolean(m.colour)).toBe(m.computable);
  });

  it("formats a missing figure as not computable, not £0", () => {
    expect(formatMillions(null)).toBe("Not computable");
    expect(formatMillions(1500)).toBe("£1.5bn");
    expect(formatMillions(-250)).toBe("-£250m");
  });

  it("totals by year", () => {
    const computable = results.measures.filter((m) => m.computable);
    const rows = totalByYear(computable, results.years);
    expect(rows).toHaveLength(results.years.length);
    expect(rows[0].total).toBeCloseTo(computable.reduce((s, m) => s + m.budgetary_impact[0].value_m, 0));
  });

  it("ends the waterfall at the net total", () => {
    const computable = results.measures.filter((m) => m.computable);
    const rows = waterfallRows(computable, 2030);
    const net = rows.at(-1);
    expect(net.net).toBe(true);
    expect(net.value).toBeCloseTo(rows.slice(0, -1).reduce((s, r) => s + r.value, 0));
  });

  it("writes CSV with escaping", () => {
    expect(toCsv([{ a: "x,y", b: 1 }])).toBe('a,b\n"x,y",1');
  });
});
