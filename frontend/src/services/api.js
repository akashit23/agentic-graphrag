import axios from "axios";

const http = axios.create({ baseURL: "/api", timeout: 180000 });

/** Turns any axios error into a readable message from the backend's {detail}. */
export const errMsg = (e) => e?.response?.data?.detail || (e?.code === "ERR_NETWORK" ? "Backend not reachable. Is it running on port 8000?" : e.message);

export const api = {
  health: () => http.get("/health").then((r) => r.data),
  repos: () => http.get("/repositories").then((r) => r.data),
  repo: (id) => http.get(`/repositories/${id}`).then((r) => r.data),
  upload: (file) => { const f = new FormData(); f.append("file", file); return http.post("/repositories/upload", f).then((r) => r.data); },
  github: (url) => http.post("/repositories/github", { url }).then((r) => r.data),
  sample: () => http.post("/repositories/sample").then((r) => r.data),
  files: (id) => http.get(`/repositories/${id}/files`).then((r) => r.data),
  file: (id, path) => http.get(`/repositories/${id}/file`, { params: { path } }).then((r) => r.data),
  graph: (id, level) => http.get(`/repositories/${id}/graph`, { params: { level } }).then((r) => r.data),
  deps: (id, file) => http.get(`/repositories/${id}/dependencies`, { params: { file } }).then((r) => r.data),
  analyze: (id) => http.post(`/repositories/${id}/analyze`).then((r) => r.data),
  chat: (repository_id, question, history) => http.post("/chat", { repository_id, question, history }).then((r) => r.data),
};
