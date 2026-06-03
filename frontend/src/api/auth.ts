import api from "./client";

export const login = (login: string, password: string) =>
  api.post("/auth/login", { login, password });

export const getMe = () => api.get("/auth/me");

export const updateProfile = (data: Record<string, unknown>) =>
  api.patch("/auth/profile", data);

export const uploadAvatar = (file: File) => {
  const fd = new FormData();
  fd.append("file", file);
  return api.post("/auth/profile/avatar", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};
