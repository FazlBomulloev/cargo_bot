import api from "./client";

export const getStaff = () => api.get("/staff");

export const createStaff = (data: Record<string, unknown>) =>
  api.post("/staff", data);

export const updateStaff = (id: number, data: Record<string, unknown>) =>
  api.patch(`/staff/${id}`, data);

export const deleteStaff = (id: number) => api.delete(`/staff/${id}`);

export const resetPassword = (id: number, new_password: string) =>
  api.post(`/staff/${id}/reset-password`, { new_password });

export const updatePermissions = (id: number, permissions: string[]) =>
  api.patch(`/staff/${id}/permissions`, { permissions });
