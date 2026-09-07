export function Spinner({ label = "Loading" }: { label?: string }) {
  return (
    <div role="status" aria-live="polite" style={{ padding: "24px", color: "var(--text-faint)" }}>
      {label}…
    </div>
  );
}
