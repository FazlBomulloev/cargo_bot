import { create } from "zustand";

export interface StaffUser {
  id: number;
  full_name: string;
  login: string;
  role: "owner" | "admin_china" | "admin_dushanbe";
  avatar_url: string | null;
  permissions: string[];
  warehouse_id: number | null;
  is_active: boolean;
}

interface AuthState {
  token: string | null;
  user: StaffUser | null;
  setAuth: (token: string, user: StaffUser) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem("token"),
  user: JSON.parse(localStorage.getItem("user") || "null"),
  setAuth: (token, user) => {
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(user));
    set({ token, user });
  },
  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    set({ token: null, user: null });
  },
}));
