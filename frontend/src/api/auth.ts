import api from "./client";

export const login = (login: string, password: string) =>
  api.post("/auth/login", { login, password });

export const getMe = () => api.get("/auth/me");
