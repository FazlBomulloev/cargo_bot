import api from "./client";

export const getUnresolved = () => api.get("/unresolved");

export const resolveParcel = (id: number, tps_code: string) =>
  api.post(`/unresolved/${id}/resolve`, { tps_code });

export const deleteUnresolved = (id: number) =>
  api.delete(`/unresolved/${id}`);
