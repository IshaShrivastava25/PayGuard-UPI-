// Thin client for the PayGuard FastAPI backend.
let baseUrl = import.meta.env?.VITE_API_URL || "http://127.0.0.1:8000";
export const setBaseUrl = (url) => { baseUrl = url; };

// sessionStorage: cleared when the tab closes. Good enough for a demo; a production app
// would use httpOnly cookies so scripts can never read the token.
const TOKEN_KEY = "payguard_token";
export const getToken = () => globalThis.sessionStorage?.getItem(TOKEN_KEY) ?? null;
const setToken = (t) => globalThis.sessionStorage?.setItem(TOKEN_KEY, t);
export const clearToken = () => globalThis.sessionStorage?.removeItem(TOKEN_KEY);

export class ApiError extends Error {
  constructor(status, message, details = null) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

function describeError(data, status) {
  const d = data?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) {
    // FastAPI validation errors: [{ loc: ["body", "amount"], msg: "..." }]
    return d.map((e) => `${(e.loc || []).slice(1).join(".") || "input"}: ${e.msg}`).join("; ");
  }
  return `Request failed (${status})`;
}

async function request(path, { method = "GET", body, form, auth = true } = {}) {
  const headers = {};
  if (auth && getToken()) headers.Authorization = `Bearer ${getToken()}`;

  let payload;
  if (form) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    payload = new URLSearchParams(form).toString();
  } else if (body) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let res;
  try {
    res = await fetch(baseUrl + path, { method, headers, body: payload });
  } catch {
    throw new ApiError(0, `Cannot reach the API at ${baseUrl}. Is the backend running?`);
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, describeError(data, res.status), data);
  return data;
}

export const register = (username, password) =>
  request("/auth/register", { method: "POST", body: { username, password }, auth: false });

export async function login(username, password) {
  const data = await request("/auth/login", { method: "POST", form: { username, password }, auth: false });
  setToken(data.access_token);
  return data;
}

export const logout = clearToken;
export const me = () => request("/auth/me");
export const predict = (tx) => request("/predict", { method: "POST", body: tx });

export function listPredictions({ limit = 10, offset = 0, label } = {}) {
  const q = new URLSearchParams({ limit, offset });
  if (label) q.set("label", label);
  return request(`/predictions?${q}`);
}
