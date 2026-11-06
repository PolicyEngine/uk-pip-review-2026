export default function EmptyState({ children, testId = "empty-state" }) {
  return (
    <div className="empty-state" data-testid={testId}>
      {children}
    </div>
  );
}
