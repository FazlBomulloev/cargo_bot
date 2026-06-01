import api from "./client";

export const createIssuance = (data: {
  client_id: number;
  parcel_ids: number[];
  payment_method: string | null;
  payment_status: string;
}) => api.post("/issuance", data);

export const getIssuances = (params?: Record<string, unknown>) =>
  api.get("/issuance", { params });

export const getIssuance = (id: number) => api.get(`/issuance/${id}`);
