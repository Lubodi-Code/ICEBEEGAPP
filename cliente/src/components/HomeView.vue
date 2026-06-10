<script setup>
import { ref } from "vue";
import { api } from "../api.js";
import { recientes, recordarReciente, olvidarReciente } from "../recientes.js";

const emit = defineEmits(["abrir"]);

const titulo = ref("");
const slugAbrir = ref("");
const error = ref("");
const creando = ref(false);

async function crear() {
  if (!titulo.value.trim()) return;
  creando.value = true;
  error.value = "";
  try {
    const ice = await api.crearIceberg(titulo.value.trim());
    recordarReciente(ice.slug, ice.titulo);
    emit("abrir", ice.slug);
  } catch (e) {
    error.value = e.message;
  } finally {
    creando.value = false;
  }
}

function abrirPorSlug() {
  const s = slugAbrir.value.trim().replace(/^.*\/i\//, "");
  if (s) emit("abrir", s);
}
</script>

<template>
  <section class="panel">
    <h2 style="margin-top: 0">Crear un iceberg</h2>
    <form class="fila" @submit.prevent="crear">
      <input
        v-model="titulo"
        class="crece"
        placeholder="Título, ej: Curiosidades del océano"
        maxlength="120"
      />
      <button :disabled="creando || !titulo.trim()">Crear</button>
    </form>
    <p v-if="error" class="error">{{ error }}</p>
  </section>

  <section class="panel">
    <h3 style="margin-top: 0">Abrir uno existente</h3>
    <form class="fila" @submit.prevent="abrirPorSlug">
      <input v-model="slugAbrir" class="crece" placeholder="Slug o enlace compartido" />
      <button :disabled="!slugAbrir.trim()">Abrir</button>
    </form>
  </section>

  <section v-if="recientes.length" class="panel">
    <h3 style="margin-top: 0">Recientes</h3>
    <div v-for="r in recientes" :key="r.slug" class="fila" style="padding: 6px 0">
      <a href="#" class="crece" @click.prevent="emit('abrir', r.slug)">{{ r.titulo }}</a>
      <span class="dim">{{ r.slug }}</span>
      <button class="fantasma" title="Quitar de recientes" @click="olvidarReciente(r.slug)">
        ✕
      </button>
    </div>
  </section>
</template>
