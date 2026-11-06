import ChartDownloadMenu from "./ChartDownloadMenu";

// The basis is stated once, on the Methodology tab; a chart's subtitle is a
// short unit line with a link to it.
export default function ChartPanel({ title, subtitle, rows, filename, children, moreInfo, onMethod }) {
  return (
    <section className="panel mb-6">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="m-0 text-lg font-semibold text-slate-800">{title}</h3>
          {subtitle && (
            <p className="m-0 mt-1 text-sm text-slate-500">
              {subtitle}
              {onMethod && (
                <>
                  {"; "}
                  <button type="button" className="underline" onClick={onMethod}>
                    see method
                  </button>
                </>
              )}
            </p>
          )}
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
