import api from "./client";

export const getSettings = () => api.get("/settings");

export const getSetting = (key: string) => api.get(`/settings/${key}`);

export const updateSetting = (key: string, value: string) =>
  api.put(`/settings/${key}`, { value });
