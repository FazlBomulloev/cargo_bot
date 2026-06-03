import api from "./client";

export const getOverview = (period = "30d", from_date?: string, to_date?: string) =>
  api.get("/stats/overview", { params: { period, from_date, to_date } });

export const getParcelsByDay = (from_date?: string, to_date?: string) =>
  api.get("/stats/parcels-by-day", { params: { from_date, to_date } });

export const getRevenue = (group_by = "week") =>
  api.get("/stats/revenue", { params: { group_by } });

export const getTopClients = (limit = 10, sort_by = "amount") =>
  api.get("/stats/top-clients", { params: { limit, sort_by } });

export const getStuckParcels = (days = 14) =>
  api.get("/stats/stuck-parcels", { params: { days } });

export const getStaffActivity = (period = "30d") =>
  api.get("/stats/staff-activity", { params: { period } });
