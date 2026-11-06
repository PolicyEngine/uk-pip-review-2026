// Shown on every view unless results.json has status "final": placeholder
// (template), mock (drill branch) or provisional (the real day before G4).
// The page also carries noindex (app/layout.jsx); scripts/smoke-built-site.sh
// checks both in the built HTML.
export default function StatusBanner({ status, text }) {
  if (status === "final") return null;
  return (
    <div role="alert" className="status-banner" data-testid="status-banner" data-status={status}>
      <strong>{text}</strong>
    </div>
  );
}
