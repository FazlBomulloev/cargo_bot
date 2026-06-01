import api from "./client";

export const getWarehouses = () => api.get("/warehouses");

export const getWarehouse = (id: number) => api.get(`/warehouses/${id}`);

export const createWarehouse = (data: Record<string, unknown>) =>
  api.post("/warehouses", data);

export const updateWarehouse = (id: number, data: Record<string, unknown>) =>
  api.patch(`/warehouses/${id}`, data);

export const deleteWarehouse = (id: number) =>
  api.delete(`/warehouses/${id}`);
