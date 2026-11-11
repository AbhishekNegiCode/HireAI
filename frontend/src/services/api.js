import axios from "axios";
export const api = axios.create({ baseURL: "/api", withCredentials: true });
let csrf = "";
export function setCsrf(token) {
  csrf = token || "";
}
api.interceptors.request.use((config) => {
  if (csrf) config.headers["X-CSRF-Token"] = csrf;
  return config;
});
export function errorMessage(error) {
  const data = error.response?.data?.error;
  return (
    data?.details
      ?.map((d) => `${d.field.replace("body.", "")}: ${d.message}`)
      .join("; ") ||
    data?.message ||
    "Unable to connect. Please try again."
  );
}
