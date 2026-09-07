export function ErrorBanner({ message }: { message: string }) {
  return (
    <div
      role="alert"
      style={{
        background: "var(--danger-soft)",
        color: "var(--danger)",
        border: "1px solid var(--danger)",
        borderRadius: "var(--radius)",
        padding: "10px 14px",
        fontSize: "13.5px",
      }}
    >
      {message}
    </div>
  );
}
