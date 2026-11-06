// The one home of the basis, the limits and the replication line.
export default function MethodologyTab({ data }) {
  const e = data.engine;
  return (
    <div className="tab-body">
      <section className="panel mb-6" id="basis">
        <h3 className="m-0 mb-2 text-lg font-semibold">Basis</h3>
        <ul className="bulleted m-0 pl-5 text-sm text-slate-700" data-testid="basis-list">
          {Object.entries(data.basis).map(([key, text]) => (
            <li key={key}>{text}</li>
          ))}
        </ul>
      </section>
      <section className="panel mb-6">
        <h3 className="m-0 mb-2 text-lg font-semibold">What the data cannot show</h3>
        <ul className="bulleted m-0 pl-5 text-sm text-slate-700">
          {data.data_limits.map((limit) => (
            <li key={limit.key}>{limit.reason}</li>
          ))}
        </ul>
      </section>
      <section className="panel mb-6">
        <h3 className="m-0 mb-2 text-lg font-semibold">What the model cannot show</h3>
        <ul className="bulleted m-0 pl-5 text-sm text-slate-700">
          {data.model_limits.map((limit) => (
            <li key={limit.key}>{limit.reason}</li>
          ))}
        </ul>
      </section>
      <p className="text-sm text-slate-500" data-testid="replication-line">
        policyengine {e.policyengine}, policyengine-uk {e.policyengine_uk}, dataset {e.dataset}
        {e.certified_pair ? ` (certified bundle pair; PIP-specific checks ${e.pip_validation})` : " (not a certified pair)"}.
      </p>
    </div>
  );
}
