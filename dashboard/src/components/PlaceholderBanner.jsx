// Shown on every page while results.json has status "placeholder". The page
// also carries noindex (app/layout.jsx). Check both on the protected preview,
// not only on a local build.
export default function PlaceholderBanner({ text }) {
  return (
    <div role="alert" className="placeholder-banner" data-testid="placeholder-banner">
      <strong>{text}</strong>
    </div>
  );
}
