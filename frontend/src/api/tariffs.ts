import api from "./client";

export const getTariffs = () => api.get("/tariffs");

export const getActiveTariffs = () => api.get("/tariffs/active");

export const createTariff = (data: Record<string, unknown>) =>
  api.post("/tariffs", data);

export const updateTariff = (id: number, data: Record<string, unknown>) =>
  api.patch(`/tariffs/${id}`, data);
