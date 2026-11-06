import { describe, expect, it } from "vitest";
import results from "../../public/data/results.json";
import { waterfallRows } from "../components/WaterfallChart";
import { CHART_COLOURS, MEASURE_RAMP } from "./chartTheme";
import { catalogue, formatMillions, millionsAxis, toCsv, totalByYear } from "./measures";

describe("measure utils", () => {
  it("gives a colour to measures with figures only", () => {
    for (const m of catalogue(results)) expect(Boolean(m.colour)).toBe(Array.isArray(m.budgetary_impact));
  });

  it("never uses a gain or loss colour for a measure", () => {
    const roles = [CHART_COLOURS.gain, CHART_COLOURS.gainLight, CHART_COLOURS.loss, CHART_COLOURS.lossLight, CHART_COLOURS.highlight];
    for (const colour of MEASURE_RAMP) expect(roles).not.toContain(colour);
  });

  it("keeps a missing cell null in the totals", () => {
    const rows = totalByYear([{ id: "a", budgetary_impact: [] }], [2027]);
    expect(rows[0].a).toBeNull();
    expect(rows[0].total).toBeNull();
  });

  it("uses one unit per axis", () => {
    const tick = millionsAxis([450, 1800]);
    expect(tick(450)).toBe("£0.5bn");
    expect(millionsAxis([450])(450)).toBe("£450m");
  });

  it("formats a missing figure as not available, not £0", () => {
    expect(formatMillions(null)).toBe("Not available");
    expect(formatMillions(1500)).toBe("£1.5bn");
    expect(formatMillions(-250)).toBe("-£250m");
  });

  it("totals by year", () => {
    const computable = results.measures.filter((m) => m.budgetary_impact);
    const rows = totalByYear(computable, results.years);
    expect(rows).toHaveLength(results.years.length);
    expect(rows[0].total).toBeCloseTo(computable.reduce((s, m) => s + m.budgetary_impact[0].value_m, 0));
  });

  it("ends the waterfall at the net total", () => {
    const computable = results.measures.filter((m) => m.budgetary_impact);
    const rows = waterfallRows(computable, 2030);
    const net = rows.at(-1);
    expect(net.net).toBe(true);
    expect(net.value).toBeCloseTo(rows.slice(0, -1).reduce((s, r) => s + r.value, 0));
  });

  it("writes CSV with escaping", () => {
    expect(toCsv([{ a: "x,y", b: 1 }])).toBe('a,b\n"x,y",1');
  });
});
