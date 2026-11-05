import ChartDownloadMenu from "./ChartDownloadMenu";

export default function ChartPanel({ title, subtitle, rows, filename, children, moreInfo }) {
  return (
    <section className="panel mb-6">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="m-0 text-lg font-semibold text-slate-800">{title}</h3>
          {subtitle && <p className="m-0 mt-1 text-sm text-slate-500">{subtitle}</p>}
        </div>
        {rows && <ChartDownloadMenu rows={rows} filename={filename} />}
      </div>
      {children}
      {moreInfo && (
        <details className="mt-4 text-sm text-slate-600">
          <summary className="cursor-pointer">More on this chart</summary>
          <p className="mt-2">{moreInfo}</p>
        </details>
      )}
    </section>
  );
}
