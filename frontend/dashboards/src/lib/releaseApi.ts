import axios from "axios";

const releaseApi = axios.create({
  timeout: 30000,
});

releaseApi.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  const schoolId = localStorage.getItem("school_id");

  config.headers = config.headers ?? {};
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  if (schoolId) {
    config.headers["X-School-Id"] = schoolId;
  }
  return config;
});

export default releaseApi;