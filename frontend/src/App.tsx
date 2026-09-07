import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { Spinner } from "./components/common/Spinner";
import { useAuth } from "./hooks/useAuth";
import { LoginPage } from "./pages/LoginPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { DocumentEditorPage } from "./pages/DocumentEditorPage";

export function App() {
  const { user, checking, pending, error, login, logout, checkSession } = useAuth();

  useEffect(() => {
    void checkSession();
  }, [checkSession]);

  if (checking) {
    return <Spinner label="Loading DocEngine" />;
  }

  if (!user) {
    return <LoginPage onLogin={login} pending={pending} error={error} />;
  }

  return (
    <AppShell user={user} onLogout={logout}>
      <Routes>
        <Route path="/" element={<DocumentsPage />} />
        <Route path="/d/:id" element={<DocumentEditorPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}
