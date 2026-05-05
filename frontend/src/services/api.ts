/** Typed API client — thin fetch wrappers, no external HTTP library needed. */

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ── Types ────────────────────────────────────────────────────────────────────

export interface Turtle {
  id: string;
  name: string;
  notes: string | null;
  registered_at: string;
}

export interface Photo {
  id: string;
  turtle_id: string;
  file_path: string;
  uploaded_at: string;
}

export interface Sighting {
  id: string;
  turtle_id: string;
  latitude: number;
  longitude: number;
  sighted_at: string;
  location_name: string | null;
}

export interface MatchResult {
  turtle_id: string;
  name: string;
  similarity_score: number;
  confidence: "high" | "medium" | "low";
}

export interface IdentificationResponse {
  matches: MatchResult[];
  candidates: MatchResult[];
  threshold: number;
  accepted: boolean;
  turtle_detected: boolean;
}

export type GeoJSON = Record<string, unknown>;

// ── Turtles ──────────────────────────────────────────────────────────────────

export const turtleApi = {
  list: (limit = 100, offset = 0) =>
    request<Turtle[]>(`/turtles?limit=${limit}&offset=${offset}`),

  get: (id: string) => request<Turtle>(`/turtles/${id}`),

  create: (name: string, notes?: string) =>
    request<Turtle>("/turtles", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, notes }),
    }),

  update: (id: string, patch: { name?: string; notes?: string }) =>
    request<Turtle>(`/turtles/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    }),

  delete: (id: string) =>
    fetch(`${BASE}/turtles/${id}`, { method: "DELETE" }),
};

// ── Photos ────────────────────────────────────────────────────────────────────

export const photoApi = {
  list: (turtleId: string) =>
    request<Photo[]>(`/turtles/${turtleId}/photos`),

  upload: (turtleId: string, file: File, region = "body") => {
    const form = new FormData();
    form.append("file", file);
    return request<Photo>(`/turtles/${turtleId}/photos?region=${region}`, {
      method: "POST",
      body: form,
    });
  },

  delete: (turtleId: string, photoId: string) =>
    fetch(`${BASE}/turtles/${turtleId}/photos/${photoId}`, { method: "DELETE" }),

  url: (filePath: string): string => {
    // filePath örneği: "uploads/<turtle_id>/<uuid>.jpg"
    // Vite proxy /api → "" dönüşümü yaptığı için /api prefix olmadan kullan
    const normalized = filePath.replace(/\\/g, "/").replace(/^uploads\//, "");
    return `/api/static/uploads/${normalized}`;
  },
};

// ── Sightings ─────────────────────────────────────────────────────────────────

export const sightingApi = {
  list: (turtleId: string) =>
    request<Sighting[]>(`/turtles/${turtleId}/sightings`),

  log: (
    turtleId: string,
    payload: { latitude: number; longitude: number; location_name?: string }
  ) =>
    request<Sighting>(`/turtles/${turtleId}/sightings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  route: (turtleId: string) =>
    request<GeoJSON>(`/turtles/${turtleId}/route`),
};

// ── Identification ────────────────────────────────────────────────────────────

export const identifyApi = {
  identify: (file: File, region = "body", topK = 5) => {
    const form = new FormData();
    form.append("file", file);
    return request<IdentificationResponse>(
      `/identify?region=${region}&top_k=${topK}`,
      { method: "POST", body: form }
    );
  },
};
