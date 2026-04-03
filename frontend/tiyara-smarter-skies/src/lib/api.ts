import { toast } from "@/hooks/use-toast";

const BASE_URL = "http://localhost:8000";

let accessToken: string | null = localStorage.getItem("access_token");
let refreshToken: string | null = localStorage.getItem("refresh_token");

export function setTokens(access: string, refresh: string) {
  accessToken = access;
  refreshToken = refresh;
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
}

export function clearTokens() {
  accessToken = null;
  refreshToken = null;
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
}

export function getAccessToken() {
  return accessToken;
}

export function setUser(user: any) {
  localStorage.setItem("user", JSON.stringify(user));
}

export function getUser() {
  const u = localStorage.getItem("user");
  return u ? JSON.parse(u) : null;
}

async function refreshAccessToken(): Promise<boolean> {
  if (!refreshToken) return false;
  try {
    const res = await fetch(`${BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    setTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const headers: any = { ...options.headers };

  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  } catch {
    toast({ title: "Connection error", description: "Please check your network", variant: "destructive" });
    throw new Error("Network error");
  }

  if (res.status === 401 && path !== "/auth/signin" && path !== "/auth/refresh") {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      headers["Authorization"] = `Bearer ${accessToken}`;
      res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
    } else {
      clearTokens();
      toast({ title: "Session expired", description: "Please sign in again", variant: "destructive" });
      window.location.href = "/signin";
      throw new Error("Session expired");
    }
  }

  if (res.status === 403) {
    toast({ title: "Permission denied", description: "You do not have permission to perform this action", variant: "destructive" });
  }
  if (res.status === 404) {
    toast({ title: "Not found", description: "Resource not found", variant: "destructive" });
  }

  return res;
}

export function sseStream(path: string, body: any, onToken: (text: string) => void, onDone: () => void) {
  const headers: any = { "Content-Type": "application/json" };
  if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;

  fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  }).then(async (res) => {
    if (!res.ok || !res.body) {
      onDone();
      return;
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const parsed = JSON.parse(line.slice(6));
            if (parsed.type === "content") onToken(parsed.text);
            if (parsed.type === "done") onDone();
          } catch {}
        }
      }
    }
    onDone();
  }).catch(() => onDone());
}
