import axios from "axios";
import { useAuthStore } from "../store/authStore";

const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  console.log("Interceptor token:", token);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (error) => {
    console.error("Response error:", error.response?.status, error.response?.data);
    if (error.response?.status === 401 && !window.location.pathname.includes("/login")) {
      useAuthStore.getState().logout();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

export default api;
