import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import results from "../../public/data/results.json";
import Dashboard, { VIEWS } from "./Dashboard";

beforeEach(() => window.history.replaceState(null, "", "/"));
afterEach(cleanup);

describe("Dashboard", () => {
  it("shows the placeholder banner", () => {
    render(<Dashboard data={results} />);
    expect(screen.getByTestId("status-banner")).toHaveTextContent("placeholder figures");
  });

  it.each([
    ["mock", "MOCK: drill figures"],
    ["provisional", "Provisional: figures are being checked"],
  ])("shows the banner on a %s page", (status, banner) => {
    render(<Dashboard data={{ ...results, status, banner }} />);
    const el = screen.getByTestId("status-banner");
    expect(el).toHaveAttribute("data-status", status);
    expect(el).toHaveTextContent(banner);
  });

  it("shows no banner on a final page", () => {
    render(<Dashboard data={{ ...results, status: "final", banner: "" }} />);
    expect(screen.queryByTestId("status-banner")).toBeNull();
  });

  it("asks for a measure, and shows no net cost, when none is selected", () => {
    render(<Dashboard data={results} />);
    const group = screen.getByRole("group", { name: "Measures" });
    for (const button of within(group).getAllByRole("button", { pressed: true })) fireEvent.click(button);
    expect(screen.getByTestId("select-measure")).toBeInTheDocument();
    expect(screen.getByTestId("stat-tiles").textContent).not.toMatch(/Net cost/);
  });

  it("shows a withheld decile as withheld, never as £0", () => {
    const measures = results.measures.map((m) =>
      m.decile
        ? { ...m, decile: m.decile.map((r, i) => (i === 0 ? { ...r, avg_change_gbp: null, pct_change: null, suppressed: true } : r)) }
        : m,
    );
    window.history.replaceState(null, "", "/?tab=impact&sub=deciles");
    render(<Dashboard data={{ ...results, measures }} />);
    expect(screen.getByTestId("withheld-note")).toHaveTextContent("decile 1");
  });

  it("shows people affected for one measure", () => {
    const one = results.measures.find((m) => m.people_affected);
    window.history.replaceState(null, "", `/?policies=${one.id}`);
    render(<Dashboard data={results} />);
    expect(screen.getByTestId("stat-tiles")).toHaveTextContent("People affected");
    expect(screen.getByTestId("stat-tiles")).toHaveTextContent("gain");
  });

  it("has the five AB2026 views", () => {
    render(<Dashboard data={results} />);
    const tabs = within(screen.getByRole("tablist", { name: "Views" })).getAllByRole("tab");
    expect(tabs.map((t) => t.textContent)).toEqual(VIEWS.map((v) => v.label));
  });

  it("keeps the tab in the address", () => {
    render(<Dashboard data={results} />);
    fireEvent.click(screen.getByRole("tab", { name: "Methodology" }));
    expect(window.location.search).toContain("tab=method");
    expect(screen.getByTestId("replication-line")).toHaveTextContent(
      "build uk-frs-calibration-attempt-20261110T204756Z-9e18f010, policyengine-uk 2.177.7, not in a policyengine.py release",
    );
  });

  it("opens the tab named in the address", () => {
    window.history.replaceState(null, "", "/?tab=policies");
    render(<Dashboard data={results} />);
    expect(screen.getByRole("tab", { name: "Policies" })).toHaveAttribute("aria-selected", "true");
  });

  it("shows a reason, never a figure, for measures without figures", () => {
    window.history.replaceState(null, "", "/?tab=policies");
    render(<Dashboard data={results} />);
    for (const m of results.measures.filter((x) => !x.budgetary_impact)) {
      const card = screen.getByTestId(`policy-${m.id}`);
      expect(within(card).getByTestId("route-reason")).toHaveTextContent(m.route_reason);
      expect(card.textContent).not.toMatch(/£0\b/);
    }
  });

  it("reads the measure list from results.json, not a fixed list", () => {
    const extra = {
      ...results,
      measures: [...results.measures, { ...results.measures[0], id: "added_measure", name: "Added measure" }],
    };
    window.history.replaceState(null, "", "/?tab=policies");
    render(<Dashboard data={extra} />);
    expect(screen.getByTestId("policy-added_measure")).toBeInTheDocument();
  });

  it("drops unknown policies from the address", () => {
    window.history.replaceState(null, "", "/?policies=nope");
    render(<Dashboard data={results} />);
    const chips = within(screen.getByRole("group", { name: "Measures" })).getAllByRole("button", { pressed: true });
    expect(chips.length).toBe(results.measures.filter((m) => m.budgetary_impact).length);
  });
});
