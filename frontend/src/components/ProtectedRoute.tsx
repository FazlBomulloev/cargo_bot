import { useEffect, useRef } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { getMe } from "../api/auth";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, setAuth, token } = useAuth();
  const refreshed = useRef(false);

  useEffect(() => {
    if (isAuthenticated && !refreshed.current) {
      refreshed.current = true;
      getMe()
        .then(({ data }) => setAuth(token!, data))
        .catch(() => {});
    }
  }, [isAuthenticated]);

  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
