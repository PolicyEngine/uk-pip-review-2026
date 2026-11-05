export default function MethodologyTab({ data }) {
  return (
    <div className="tab-body">
      <section className="panel mb-6">
        <h3 className="m-0 mb-2 text-lg font-semibold">Basis</h3>
        <ul className="m-0 pl-5 text-sm text-slate-700">
          {Object.entries(data.basis).map(([key, text]) => (
            <li key={key}>{text}</li>
          ))}
        </ul>
      </section>
      <section className="panel mb-6">
        <h3 className="m-0 mb-2 text-lg font-semibold">Data limits</h3>
        <ul className="m-0 pl-5 text-sm text-slate-700">
          {data.data_limits.map((limit) => (
            <li key={limit.key}>
              {limit.reason} {limit.issue && <span className="text-slate-500">(#{limit.issue})</span>}
            </li>
          ))}
        </ul>
      </section>
      <section className="panel mb-6">
        <h3 className="m-0 mb-2 text-lg font-semibold">Model limits</h3>
        <ul className="m-0 pl-5 text-sm text-slate-700">
          {data.model_limits.map((limit) => (
            <li key={limit.key}>
              {limit.reason} {limit.issue && <span className="text-slate-500">(#{limit.issue})</span>}
            </li>
          ))}
        </ul>
      </section>
      <p className="text-sm text-slate-500" data-testid="replication-line">
        policyengine {data.engine.policyengine}, policyengine-uk {data.engine.policyengine_uk}, dataset {data.engine.dataset}
        {data.engine.validated_pair ? "" : " (unvalidated under this engine)"}.
      </p>
    </div>
  );
}
