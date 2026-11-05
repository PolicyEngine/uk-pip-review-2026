import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import results from "../../public/data/results.json";
import Dashboard, { VIEWS } from "./Dashboard";

beforeEach(() => window.history.replaceState(null, "", "/"));
afterEach(cleanup);

describe("Dashboard", () => {
  it("shows the placeholder banner", () => {
    render(<Dashboard data={results} />);
    expect(screen.getByTestId("placeholder-banner")).toHaveTextContent("placeholder figures");
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
    expect(screen.getByTestId("replication-line")).toHaveTextContent("unvalidated");
  });

  it("opens the tab named in the address", () => {
    window.history.replaceState(null, "", "/?tab=policies");
    render(<Dashboard data={results} />);
    expect(screen.getByRole("tab", { name: "Policies" })).toHaveAttribute("aria-selected", "true");
  });

  it("shows a reason, never a figure, for measures that are not computable", () => {
    window.history.replaceState(null, "", "/?tab=policies");
    render(<Dashboard data={results} />);
    for (const m of results.measures.filter((x) => !x.computable)) {
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
    const pressed = screen.getAllByRole("button", { pressed: true });
    expect(pressed.length).toBe(results.measures.filter((m) => m.computable).length);
  });
});
