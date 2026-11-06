import { IN_REPORT_LABELS, ROUTE_GROUPS, ROUTE_LABELS } from "../utils/measures";
import { detailsFor } from "../utils/policyDetails";

// One card per candidate recommendation, grouped by how it is handled. A
// measure without figures shows its reason, never a figure.
export default function PoliciesTab({ measures }) {
  return (
    <div className="tab-body">
      {ROUTE_GROUPS.map((group) => {
        const cards = measures.filter((m) => group.routes.includes(m.route));
        if (!cards.length) return null;
        return (
          <section key={group.label} className="mb-8">
            <h2 className="m-0 mb-3 text-xl font-semibold text-slate-800">{group.label}</h2>
            <div className="grid gap-4 md:grid-cols-2">
              {cards.map((m) => {
                const details = detailsFor(m);
                return (
                  <article key={m.id} className="panel" data-testid={`policy-${m.id}`}>
                    <p className="eyebrow m-0 text-slate-500">{ROUTE_LABELS[m.route]}</p>
                    <h3 className="m-0 mt-1 text-lg font-semibold">{m.name}</h3>
                    <p className="m-0 mt-2 text-sm text-slate-700">{m.description}</p>
                    <p className="m-0 mt-2 text-sm text-slate-500">
                      Recommendation: {m.recommendation}. In the report: {IN_REPORT_LABELS[m.in_report] ?? "Not yet published"}.
                    </p>
                    {details && <p className="m-0 mt-2 text-sm text-slate-600">{details.howItWorks}</p>}
                    {m.status === "withdrawn" && (
                      <p className="caveat-card m-0 mt-3 pl-3 text-sm" data-testid="withdrawn-reason">
                        Withdrawn: {m.withdrawn_reason}
                      </p>
                    )}
                    {(!m.hasFigures || m.route === "dashboard-structural") && m.status !== "withdrawn" && (
                      <p className="caveat-card m-0 mt-3 pl-3 text-sm" data-testid="route-reason">
                        {m.route_reason}
                        {m.computable && !m.hasFigures ? " Figures come from a model run." : ""}
                      </p>
                    )}
                  </article>
                );
              })}
            </div>
          </section>
        );
      })}
    </div>
  );
}
