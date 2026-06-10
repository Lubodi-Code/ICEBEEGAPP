<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import HomeView from "./components/HomeView.vue";
import IcebergEditor from "./components/IcebergEditor.vue";

// Routing mínimo por hash: "#/" (home) y "#/e/{slug}" (editor).
const slug = ref(null);

function leerHash() {
  const m = window.location.hash.match(/^#\/e\/(.+)$/);
  slug.value = m ? decodeURIComponent(m[1]) : null;
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
  <header style="margin-bottom: 24px">
    <h1 style="margin: 0; cursor: pointer" @click="volver">🧊 Iceberg</h1>
    <p class="dim" style="margin: 4px 0 0">
      Crea, comparte y narra icebergs de curiosidades con tus amigos.
    </p>
  </header>

  <IcebergEditor v-if="slug" :slug="slug" @volver="volver" />
  <HomeView v-else @abrir="abrir" />
</template>
