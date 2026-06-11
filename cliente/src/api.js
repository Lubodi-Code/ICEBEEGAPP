// Cliente HTTP mínimo hacia la API FastAPI. La capa cliente solo habla HTTP.
export const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(
  /\/$/,
  ""
);

async function request(path, options = {}) {
  const resp = await fetch(`${API_URL}${path}`, {
    headers: options.body instanceof FormData ? {} : { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      detail = (await resp.json()).detail || detail;
    } catch {
      /* sin cuerpo JSON */
    }
    throw new Error(detail);
  }
  if (resp.status === 204) return null;
  return resp.json();
}

export const api = {
  crearIceberg: (titulo) =>
    request("/icebergs", { method: "POST", body: JSON.stringify({ titulo }) }),
  obtenerIceberg: (slug) => request(`/icebergs/${slug}`),
  editarIceberg: (id, data) =>
    request(`/icebergs/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  borrarIceberg: (id) => request(`/icebergs/${id}`, { method: "DELETE" }),

  crearNivel: (icebergId, data) =>
    request(`/icebergs/${icebergId}/levels`, { method: "POST", body: JSON.stringify(data) }),
  editarNivel: (id, data) =>
    request(`/levels/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  borrarNivel: (id) => request(`/levels/${id}`, { method: "DELETE" }),
  reordenarNiveles: (levelIds) =>
    request("/levels/reorder", { method: "POST", body: JSON.stringify({ level_ids: levelIds }) }),

  crearEntrada: (levelId, data) =>
    request(`/levels/${levelId}/entries`, { method: "POST", body: JSON.stringify(data) }),
  editarEntrada: (id, data) =>
    request(`/entries/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  borrarEntrada: (id) => request(`/entries/${id}`, { method: "DELETE" }),

  subirMedia: (entryId, file) => {
    const form = new FormData();
    form.append("file", file);
    return request(`/entries/${entryId}/media`, { method: "POST", body: form });
  },

  subirMusica: (levelId, file) => {
    const form = new FormData();
    form.append("file", file);
    return request(`/levels/${levelId}/music`, { method: "POST", body: form });
  },

  crearTokenEdicion: (icebergId) =>
    request(`/icebergs/${icebergId}/edit-token`, { method: "POST" }),
  validarTokenEdicion: (icebergId, token) =>
    request(`/icebergs/${icebergId}/edit-token/validate?token=${encodeURIComponent(token)}`),
};

// POST /video devuelve el .mp4 como blob (descarga efímera).
export async function generarVideo(payload) {
  const resp = await fetch(`${API_URL}/video`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      detail = (await resp.json()).detail || detail;
    } catch {
      /* sin cuerpo JSON */
    }
    throw new Error(detail);
  }
  return resp.blob();
}

export function enlacePublico(slug) {
  return `${API_URL}/i/${slug}`;
}

// Enlace al editor de esta SPA (con token de edición opcional).
export function enlaceEditor(slug, token) {
  const base = `${window.location.origin}${window.location.pathname}#/e/${encodeURIComponent(slug)}`;
  return token ? `${base}?t=${encodeURIComponent(token)}` : base;
}
