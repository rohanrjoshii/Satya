import axios from "axios";
import { getToken } from "./auth";

export const api = axios.create({
  timeout: 120_000,
});

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

