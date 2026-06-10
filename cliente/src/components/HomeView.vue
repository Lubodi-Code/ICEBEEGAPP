<script setup>
import { ref } from "vue";
import { Plus, ArrowRight, X, Layers } from "lucide-vue-next";
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
  <div
    class="min-h-screen bg-slate-950 text-slate-100 bg-[radial-gradient(ellipse_at_top,rgba(30,64,175,0.25),transparent_60%)]"
  >
    <div class="max-w-2xl mx-auto px-4 py-16">
      <header class="text-center mb-12">
        <h1 class="text-5xl font-extrabold tracking-tight drop-shadow-lg">🧊 Iceberg</h1>
        <p class="text-slate-400 mt-3">
          Crea, comparte y narra icebergs de curiosidades con tus amigos.
        </p>
      </header>

      <section
        class="bg-white/5 border border-white/10 backdrop-blur-md rounded-2xl p-6 mb-6 shadow-xl"
      >
        <h2 class="text-lg font-bold mb-4 flex items-center gap-2">
          <Plus :size="20" class="text-blue-500" /> Crear un iceberg
        </h2>
        <form class="flex gap-3" @submit.prevent="crear">
          <input
            v-model="titulo"
            maxlength="120"
            placeholder="Título, ej: Misterios de Internet"
            class="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
          />
          <button
            :disabled="creando || !titulo.trim()"
            class="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold px-6 rounded-lg shadow-lg shadow-blue-600/20 transition-all"
          >
            Crear
          </button>
        </form>
        <p v-if="error" class="text-red-400 text-sm mt-3">{{ error }}</p>
      </section>

      <section
        class="bg-white/5 border border-white/10 backdrop-blur-md rounded-2xl p-6 mb-6 shadow-xl"
      >
        <h3 class="text-sm font-semibold text-slate-400 mb-3">Abrir uno existente</h3>
        <form class="flex gap-3" @submit.prevent="abrirPorSlug">
          <input
            v-model="slugAbrir"
            placeholder="Slug o enlace compartido"
            class="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-blue-500 transition-all"
          />
          <button
            :disabled="!slugAbrir.trim()"
            class="bg-white/10 hover:bg-white/20 disabled:opacity-50 border border-white/10 px-4 rounded-lg transition-all"
          >
            <ArrowRight :size="18" />
          </button>
        </form>
      </section>

      <section
        v-if="recientes.length"
        class="bg-white/5 border border-white/10 backdrop-blur-md rounded-2xl p-6 shadow-xl"
      >
        <h3 class="text-sm font-semibold text-slate-400 mb-3 flex items-center gap-2">
          <Layers :size="16" /> Recientes
        </h3>
        <div
          v-for="r in recientes"
          :key="r.slug"
          class="flex items-center gap-3 py-2 border-b border-white/5 last:border-0"
        >
          <a
            href="#"
            class="flex-1 text-blue-400 hover:text-blue-300 font-medium truncate"
            @click.prevent="emit('abrir', r.slug)"
          >
            {{ r.titulo }}
          </a>
          <span class="text-xs text-slate-500 truncate hidden sm:block">{{ r.slug }}</span>
          <button
            class="text-slate-500 hover:text-white p-1 rounded transition-colors"
            title="Quitar de recientes"
            @click="olvidarReciente(r.slug)"
          >
            <X :size="14" />
          </button>
        </div>
      </section>

      <footer class="py-10 text-center text-white/40 text-xs">
        Iceberg Web • Costo Cero
      </footer>
    </div>
  </div>
</template>
