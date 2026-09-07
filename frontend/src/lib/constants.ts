export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

/** Debounce window for autosave after the last keystroke (PRD §4.2). */
export const AUTOSAVE_DEBOUNCE_MS = 800;

export const MAX_UPLOAD_BYTES = 5 * 1024 * 1024;

export const SEEDED_ACCOUNTS = [
  { email: "alice@ajaia.test", label: "Alice — has a shared doc" },
  { email: "bob@ajaia.test", label: "Bob — was granted editor access" },
  { email: "carol@ajaia.test", label: "Carol" },
  { email: "dave@ajaia.test", label: "Dave" },
] as const;

export const SEEDED_PASSWORD = "demo1234";
