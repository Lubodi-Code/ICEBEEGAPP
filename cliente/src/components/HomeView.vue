<script setup>
import { ref } from "vue";
import { Plus, ArrowRight, X, FolderLock, Eye } from "lucide-vue-next";
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
  <div class="relative min-h-screen text-slate-200 overflow-hidden" style="background: radial-gradient(ellipse at top, rgba(20,40,32,0.45), transparent 55%), #04070c;">
    <div class="grain" />
    <div class="scanlines" />

    <div class="relative z-10 max-w-2xl mx-auto px-4 py-14">
      <!-- Cabecera de archivo -->
      <header class="mb-10">
        <div class="flex items-center justify-between mb-6">
          <span class="dossier-label">Archivo Central · Acceso restringido</span>
          <span class="stamp text-[10px]">Clasificado</span>
        </div>
        <h1 class="mono text-4xl md:text-5xl font-bold tracking-tight text-slate-100">
          PROYECTO <span class="phosphor">ICEBERG</span><span class="blink"></span>
        </h1>
        <p class="mono text-sm text-slate-400 mt-3 leading-relaxed">
          &gt; Catálogo de expedientes por niveles de profundidad.<br />
          &gt; Lo que ves en la superficie es solo el 10&nbsp;%.
        </p>
        <div class="red-thread mt-6" />
      </header>

      <!-- Abrir nuevo expediente -->
      <section class="dossier-card rounded-lg p-6 mb-6">
        <h2 class="dossier-label mb-4 flex items-center gap-2">
          <Plus :size="14" class="text-[#56d68a]" /> Abrir nuevo expediente
        </h2>
        <form class="flex gap-3" @submit.prevent="crear">
          <input
            v-model="titulo"
            maxlength="120"
            placeholder="Asunto del expediente, ej: Misterios de Internet"
            class="mono flex-1 bg-black/60 border border-[#d8b15a]/25 rounded px-4 py-3 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-[#56d68a]/70 focus:ring-1 focus:ring-[#56d68a]/40 transition-all"
          />
          <button
            :disabled="creando || !titulo.trim()"
            class="mono uppercase tracking-widest text-xs bg-[#56d68a]/15 hover:bg-[#56d68a]/25 disabled:opacity-40 disabled:cursor-not-allowed text-[#56d68a] border border-[#56d68a]/40 font-bold px-5 rounded transition-all"
          >
            {{ creando ? "…" : "Abrir" }}
          </button>
        </form>
        <p v-if="error" class="mono text-red-400 text-sm mt-3">⚠ {{ error }}</p>
      </section>

      <!-- Acceder a un expediente existente -->
      <section class="dossier-card rounded-lg p-6 mb-6">
        <h3 class="dossier-label mb-3 flex items-center gap-2">
          <Eye :size="14" class="text-[#d8b15a]" /> Acceder con clave de expediente
        </h3>
        <form class="flex gap-3" @submit.prevent="abrirPorSlug">
          <input
            v-model="slugAbrir"
            placeholder="Slug o enlace interceptado"
            class="mono flex-1 bg-black/60 border border-[#d8b15a]/25 rounded px-4 py-2.5 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-[#56d68a]/70 transition-all"
          />
          <button
            :disabled="!slugAbrir.trim()"
            class="bg-white/5 hover:bg-white/10 disabled:opacity-40 border border-[#d8b15a]/25 px-4 rounded transition-all"
          >
            <ArrowRight :size="18" />
          </button>
        </form>
      </section>

      <!-- Expedientes recientes -->
      <section v-if="recientes.length" class="dossier-card rounded-lg p-6">
        <h3 class="dossier-label mb-3 flex items-center gap-2">
          <FolderLock :size="14" /> Expedientes consultados
        </h3>
        <div
          v-for="r in recientes"
          :key="r.slug"
          class="flex items-center gap-3 py-2 border-b border-white/5 last:border-0"
        >
          <a
            href="#"
            class="mono flex-1 text-[#56d68a] hover:text-[#8aedb4] font-medium truncate"
            @click.prevent="emit('abrir', r.slug)"
          >
            ▸ {{ r.titulo }}
          </a>
          <span class="mono text-xs text-slate-600 truncate hidden sm:block redacted px-1">{{ r.slug }}</span>
          <button
            class="text-slate-600 hover:text-red-400 p-1 rounded transition-colors"
            title="Destruir registro de consulta"
            @click="olvidarReciente(r.slug)"
          >
            <X :size="14" />
          </button>
        </div>
      </section>

      <footer class="py-10 text-center">
        <p class="mono text-[10px] uppercase tracking-[0.3em] text-slate-600">
          Iceberg Web · Nada de esto es coincidencia
        </p>
      </footer>
    </div>
  </div>
</template>
