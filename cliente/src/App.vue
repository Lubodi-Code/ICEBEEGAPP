<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import HomeView from "./components/HomeView.vue";
import IcebergEditor from "./components/IcebergEditor.vue";

// Routing mínimo por hash: "#/" (home) y "#/e/{slug}?t={token}&map={id}" (editor).
// "map" abre el editor en modo mapa (solo el iceberg, para la screenshot del video).
const slug = ref(null);
const token = ref(null);
const mapEntryId = ref(null);

function leerHash() {
  const m = window.location.hash.match(/^#\/e\/([^?]+)(?:\?(.*))?$/);
  slug.value = m ? decodeURIComponent(m[1]) : null;
  const params = new URLSearchParams(m && m[2] ? m[2] : "");
  token.value = params.get("t");
  mapEntryId.value = params.get("map");
}

function abrir(nuevoSlug) {
  window.location.hash = `#/e/${encodeURIComponent(nuevoSlug)}`;
}

function volver() {
  window.location.hash = "#/";
}

onMounted(() => {
  leerHash();
  window.addEventListener("hashchange", leerHash);
});
onUnmounted(() => window.removeEventListener("hashchange", leerHash));
</script>

<template>
  <IcebergEditor
    v-if="slug"
    :slug="slug"
    :token="token"
    :map-entry-id="mapEntryId"
    @volver="volver"
  />
  <HomeView v-else @abrir="abrir" />
</template>
