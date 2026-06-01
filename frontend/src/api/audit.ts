import api from "./client";

export const getAuditLogs = (params?: Record<string, unknown>) =>
  api.get("/audit-logs", { params });
