import api from "./client";

export const getClients = (params?: Record<string, unknown>) =>
  api.get("/clients", { params });

export const searchClients = (q: string) =>
  api.get("/clients/search", { params: { q } });

export const getClient = (id: number) => api.get(`/clients/${id}`);

export const updateClient = (id: number, data: Record<string, unknown>) =>
  api.patch(`/clients/${id}`, data);

export const blockClient = (id: number) =>
  api.patch(`/clients/${id}/block`);
