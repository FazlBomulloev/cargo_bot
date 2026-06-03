import api from "./client";

export const getChinaParcels = (params?: Record<string, unknown>) =>
  api.get("/parcels/china", { params });

export const addChinaParcel = (track_id: string) =>
  api.post("/parcels/china", { track_id });

export const addChinaBulk = (track_ids: string[]) =>
  api.post("/parcels/china/bulk", { track_ids });

export const getAllParcels = (params?: Record<string, unknown>) =>
  api.get("/parcels/all", { params });

export const addDushanbeParcel = (data: Record<string, unknown>) =>
  api.post("/parcels/dushanbe", data);

export const getParcels = (params?: Record<string, unknown>) =>
  api.get("/parcels", { params });

export const getParcel = (id: number) => api.get(`/parcels/${id}`);

export const searchTrack = (track_id: string) =>
  api.get(`/parcels/track/${track_id}`);

export const updateParcelStatus = (id: number, status: string) =>
  api.patch(`/parcels/${id}/status`, { status });

export const updateParcel = (id: number, data: Record<string, unknown>) =>
  api.patch(`/parcels/${id}`, data);
