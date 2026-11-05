import { detailsFor } from "../utils/policyDetails";
import { LIKELIHOOD_LABELS, ROUTE_LABELS } from "../utils/measures";

// One card per candidate recommendation. A measure that is not computable
// shows its reason, never a figure.
export default function PoliciesTab({ measures }) {
  return (
    <div className="tab-body grid gap-4 md:grid-cols-2">
      {measures.map((m) => {
        const details = detailsFor(m);
        return (
          <article key={m.id} className="panel" data-testid={`policy-${m.id}`}>
            <p className="eyebrow m-0 text-slate-500">{ROUTE_LABELS[m.route]}</p>
            <h3 className="m-0 mt-1 text-lg font-semibold">{m.name}</h3>
            <p className="m-0 mt-2 text-sm text-slate-700">{m.description}</p>
            <p className="m-0 mt-2 text-sm text-slate-500">
              Recommendation: {m.recommendation}. Likelihood in the report: {LIKELIHOOD_LABELS[m.likelihood]}.
            </p>
            {details && <p className="m-0 mt-2 text-sm text-slate-600">{details.howItWorks}</p>}
            {!m.computable && (
              <p className="caveat-card m-0 mt-3 pl-3 text-sm" data-testid="route-reason">
                {m.route_reason}
              </p>
            )}
            {m.issues.length > 0 && (
              <p className="m-0 mt-2 text-xs text-slate-500">Blocking issues: {m.issues.map((n) => `#${n}`).join(", ")}</p>
            )}
          </article>
        );
      })}
    </div>
  );
}
