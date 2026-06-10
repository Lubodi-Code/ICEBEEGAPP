// Icebergs visitados recientemente (no hay endpoint de listado: se guardan en localStorage).
import { reactive } from "vue";

const KEY = "iceberg_recientes";

function cargar() {
  try {
    return JSON.parse(localStorage.getItem(KEY)) || [];
  } catch {
    return [];
  }
}

export const recientes = reactive(cargar());

function persistir() {
  localStorage.setItem(KEY, JSON.stringify(recientes));
}

export function recordarReciente(slug, titulo) {
  const i = recientes.findIndex((r) => r.slug === slug);
  if (i >= 0) recientes.splice(i, 1);
  recientes.unshift({ slug, titulo });
  recientes.splice(12); // máximo 12 recientes
  persistir();
}

export function olvidarReciente(slug) {
  const i = recientes.findIndex((r) => r.slug === slug);
  if (i >= 0) recientes.splice(i, 1);
  persistir();
}
