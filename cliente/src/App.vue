<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import HomeView from "./components/HomeView.vue";
import IcebergEditor from "./components/IcebergEditor.vue";

// Routing mínimo por hash: "#/" (home) y "#/e/{slug}?t={token}" (editor).
const slug = ref(null);
const token = ref(null);

function leerHash() {
  const m = window.location.hash.match(/^#\/e\/([^?]+)(?:\?t=(.+))?$/);
  slug.value = m ? decodeURIComponent(m[1]) : null;
  token.value = m && m[2] ? decodeURIComponent(m[2]) : null;
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
  <IcebergEditor v-if="slug" :slug="slug" :token="token" @volver="volver" />
  <HomeView v-else @abrir="abrir" />
</template>
