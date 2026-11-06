export default function ViewTabs({ views, active, onChange, label = "Views", sub = false }) {
  return (
    <div role="tablist" aria-label={label} className="mb-6 flex flex-wrap border-b border-slate-200">
      {views.map((view) => (
        <button
          key={view.value}
          type="button"
          role="tab"
          aria-selected={active === view.value}
          className={`tab-button ${sub ? "sub-tab-button" : ""} ${active === view.value ? "active" : ""}`}
          onClick={() => onChange(view.value)}
        >
          {view.label}
        </button>
      ))}
    </div>
  );
}
