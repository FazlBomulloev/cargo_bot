import { useAuthStore } from "../store/authStore";

export function useAuth() {
  const { token, user, setAuth, logout } = useAuthStore();
  return { token, user, setAuth, logout, isAuthenticated: !!token && !!user };
}
