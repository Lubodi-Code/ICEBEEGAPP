<script setup>
import { ref, computed, onMounted, watch } from "vue";
import {
  Share2,
  Plus,
  X,
  Image as ImageIcon,
  Video,
  Play,
  Layers,
  Edit3,
  Eye,
  EyeOff,
  ArrowLeft,
  Trash2,
  Pencil,
  ExternalLink,
  UploadCloud,
  ChevronUp,
  ChevronDown,
  Check,
} from "lucide-vue-next";
import { api, generarVideo, enlacePublico } from "../api.js";
import { recordarReciente, olvidarReciente } from "../recientes.js";

const props = defineProps({ slug: { type: String, required: true } });
const emit = defineEmits(["volver"]);

// Mismo límite que DESCRIPCION_MAX en el backend (lo que el TTS narra).
const MAX_DESC = 500;

import ICEBERG_BG_URL from "../assets/iceberg-bg.svg";

const DEPTH_COLORS = [
  "bg-blue-300/10",
  "bg-blue-500/20",
  "bg-blue-700/40",
  "bg-blue-900/60",
  "bg-slate-900/80",
];

const iceberg = ref(null);
const error = ref("");
const toast = ref("");
const showContainers = ref(true);
const panelAbierto = ref(false);

const editandoTitulo = ref(false);
const tituloDraft = ref("");

// Modal de detalle: { entry, nivel }
const seleccion = ref(null);
const editandoEntrada = ref(false);
const entradaDraft = ref({ titulo: "", descripcion: "" });
const generando = ref(false);
const subiendo = ref(false);

// Formulario "Nueva curiosidad"
const nueva = ref({ titulo: "", descripcion: "", level_id: null, file: null });
const creandoEntrada = ref(false);
const nuevoNivelNombre = ref("");

const niveles = computed(() =>
  iceberg.value
    ? [...iceberg.value.levels].sort((a, b) => a.orden - b.orden || a.numero - b.numero)
    : []
);

const totalEntradas = computed(() =>
  niveles.value.reduce((n, l) => n + l.entries.length, 0)
);

function depthColor(i) {
  return DEPTH_COLORS[Math.min(i, DEPTH_COLORS.length - 1)];
}

function avisar(msg) {
  toast.value = msg;
  setTimeout(() => (toast.value = ""), 2800);
}

async function cargar() {
  error.value = "";
  try {
    iceberg.value = await api.obtenerIceberg(props.slug);
    recordarReciente(iceberg.value.slug, iceberg.value.titulo);
    if (!nueva.value.level_id && niveles.value.length) {
      nueva.value.level_id = niveles.value[0].id;
    }
    // Mantiene el modal sincronizado tras recargar.
    if (seleccion.value) {
      for (const lvl of niveles.value) {
        const e = lvl.entries.find((x) => x.id === seleccion.value.entry.id);
        if (e) {
          seleccion.value = { entry: e, nivel: lvl };
          return;
        }
      }
      seleccion.value = null;
    }
  } catch (e) {
    error.value = e.message;
  }
}

async function guardarTitulo() {
  const t = tituloDraft.value.trim();
  if (t && t !== iceberg.value.titulo) {
    await api.editarIceberg(iceberg.value.id, { titulo: t });
    await cargar();
  }
  editandoTitulo.value = false;
}

async function compartir() {
  await navigator.clipboard.writeText(enlacePublico(iceberg.value.slug));
  avisar("🔗 Enlace copiado al portapapeles");
}

async function borrarIceberg() {
  if (!confirm(`¿Eliminar "${iceberg.value.titulo}" y todo su contenido?`)) return;
  await api.borrarIceberg(iceberg.value.id);
  olvidarReciente(iceberg.value.slug);
  emit("volver");
}

// --- niveles -----------------------------------------------------------
async function agregarNivel() {
  const numero = niveles.value.length
    ? Math.max(...niveles.value.map((l) => l.numero)) + 1
    : 1;
  await api.crearNivel(iceberg.value.id, {
    numero,
    nombre: nuevoNivelNombre.value.trim() || null,
    orden: niveles.value.length,
  });
  nuevoNivelNombre.value = "";
  await cargar();
}

async function renombrarNivel(nivel) {
  const nombre = prompt("Nombre del nivel:", nivel.nombre || "");
  if (nombre === null) return;
  await api.editarNivel(nivel.id, { nombre: nombre.trim() || null });
  await cargar();
}

async function borrarNivel(nivel) {
  if (!confirm(`¿Eliminar el nivel ${nivel.numero} y sus entradas?`)) return;
  await api.borrarNivel(nivel.id);
  await cargar();
}

async function moverNivel(nivel, delta) {
  const ids = niveles.value.map((l) => l.id);
  const i = ids.indexOf(nivel.id);
  const j = i + delta;
  if (j < 0 || j >= ids.length) return;
  [ids[i], ids[j]] = [ids[j], ids[i]];
  await api.reordenarNiveles(ids);
  await cargar();
}

// --- entradas ----------------------------------------------------------
async function crearEntrada() {
  if (!nueva.value.titulo.trim() || !nueva.value.level_id) return;
  creandoEntrada.value = true;
  try {
    const nivel = niveles.value.find((l) => l.id === nueva.value.level_id);
    const entry = await api.crearEntrada(nueva.value.level_id, {
      titulo: nueva.value.titulo.trim(),
      descripcion: nueva.value.descripcion.trim(),
      orden: nivel ? nivel.entries.length : 0,
    });
    if (nueva.value.file) {
      await api.subirMedia(entry.id, nueva.value.file);
    }
    nueva.value = { titulo: "", descripcion: "", level_id: nueva.value.level_id, file: null };
    await cargar();
    avisar("✅ Curiosidad añadida al iceberg");
  } catch (e) {
    avisar(`Error: ${e.message}`);
  } finally {
    creandoEntrada.value = false;
  }
}

function abrirEntrada(entry, nivel) {
  seleccion.value = { entry, nivel };
  editandoEntrada.value = false;
}

function empezarEdicionEntrada() {
  entradaDraft.value = {
    titulo: seleccion.value.entry.titulo,
    descripcion: seleccion.value.entry.descripcion,
  };
  editandoEntrada.value = true;
}

async function guardarEntrada() {
  await api.editarEntrada(seleccion.value.entry.id, {
    titulo: entradaDraft.value.titulo.trim() || seleccion.value.entry.titulo,
    descripcion: entradaDraft.value.descripcion.trim(),
  });
  editandoEntrada.value = false;
  await cargar();
}

async function borrarEntrada() {
  if (!confirm(`¿Eliminar "${seleccion.value.entry.titulo}"?`)) return;
  await api.borrarEntrada(seleccion.value.entry.id);
  seleccion.value = null;
  await cargar();
}

async function subirArchivoModal(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  subiendo.value = true;
  try {
    await api.subirMedia(seleccion.value.entry.id, file);
    await cargar();
    avisar("📷 Archivo subido");
  } catch (e) {
    avisar(`Error al subir: ${e.message}`);
  } finally {
    subiendo.value = false;
    event.target.value = "";
  }
}

// --- video narrado ------------------------------------------------------
async function generarVideoNarrado() {
  const { entry, nivel } = seleccion.value;
  generando.value = true;
  try {
    const blob = await generarVideo({
      iceberg_title: iceberg.value.titulo,
      level_number: nivel.numero,
      level_name: nivel.nombre,
      entry_title: entry.titulo,
      description: entry.descripcion,
      media: entry.media.map((m) => ({ url: m.url, tipo: m.tipo })),
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `iceberg-${entry.titulo.toLowerCase().replace(/\s+/g, "-")}.mp4`;
    a.click();
    URL.revokeObjectURL(url);
    avisar("🎬 Video narrado descargado");
  } catch (e) {
    avisar(`Error al generar video: ${e.message}`);
  } finally {
    generando.value = false;
  }
}

onMounted(cargar);
watch(() => props.slug, cargar);
</script>

<template>
  <div class="relative min-h-screen bg-slate-950 text-slate-100 overflow-x-hidden">
    <!-- Fondo iceberg fijo -->
    <div
      class="fixed inset-0 z-0 bg-cover bg-top bg-no-repeat"
      :style="{ backgroundImage: `url(${ICEBERG_BG_URL})` }"
    />
    <div class="fixed inset-0 z-0 bg-slate-950/30" />

    <div class="relative z-10 flex flex-col min-h-screen">
      <!-- Header -->
      <header
        class="p-4 md:p-6 flex justify-between items-center gap-3 bg-gradient-to-b from-slate-900/80 to-transparent sticky top-0 z-20 backdrop-blur-sm"
      >
        <div class="flex items-center gap-3 min-w-0">
          <button
            class="p-2 bg-white/10 hover:bg-white/20 rounded-full border border-white/10 transition-all shrink-0"
            title="Volver"
            @click="emit('volver')"
          >
            <ArrowLeft :size="18" />
          </button>
          <div class="min-w-0">
            <div v-if="editandoTitulo" class="flex items-center gap-2">
              <input
                v-model="tituloDraft"
                maxlength="120"
                class="bg-slate-950/80 border border-slate-600 rounded-lg px-3 py-1.5 text-xl font-bold text-white focus:outline-none focus:border-blue-500 w-64 md:w-96"
                @keyup.enter="guardarTitulo"
                @keyup.esc="editandoTitulo = false"
              />
              <button
                class="p-2 bg-blue-600 hover:bg-blue-500 rounded-full transition-all"
                @click="guardarTitulo"
              >
                <Check :size="16" />
              </button>
            </div>
            <h1
              v-else
              class="text-2xl md:text-3xl font-extrabold tracking-tight text-white drop-shadow-lg truncate cursor-pointer group flex items-center gap-2"
              title="Clic para editar el título"
              @click="
                tituloDraft = iceberg?.titulo || '';
                editandoTitulo = true;
              "
            >
              {{ iceberg?.titulo || "…" }}
              <Pencil
                :size="16"
                class="opacity-0 group-hover:opacity-60 transition-opacity shrink-0"
              />
            </h1>
            <p class="text-xs md:text-sm text-slate-300 font-medium drop-shadow mt-0.5">
              {{ niveles.length }} nivel(es) • {{ totalEntradas }} entrada(s)
              <a
                :href="iceberg ? enlacePublico(iceberg.slug) : '#'"
                target="_blank"
                rel="noopener"
                class="inline-flex items-center gap-1 text-blue-300 hover:text-blue-200 ml-2"
              >
                <ExternalLink :size="12" /> página pública
              </a>
            </p>
          </div>
        </div>

        <div class="flex gap-2 md:gap-3 shrink-0">
          <button
            class="flex items-center gap-2 px-3 md:px-4 py-2 bg-white/10 hover:bg-white/20 backdrop-blur-md rounded-full text-sm font-semibold transition-all border border-white/10"
            @click="showContainers = !showContainers"
          >
            <EyeOff v-if="showContainers" :size="18" />
            <Eye v-else :size="18" />
            <span class="hidden md:inline">{{
              showContainers ? "Ocultar Capas" : "Mostrar Capas"
            }}</span>
          </button>
          <button
            class="flex items-center gap-2 px-3 md:px-4 py-2 bg-white/10 hover:bg-white/20 backdrop-blur-md rounded-full text-sm font-semibold transition-all border border-white/10"
            @click="panelAbierto = !panelAbierto"
          >
            <X v-if="panelAbierto" :size="18" />
            <Edit3 v-else :size="18" />
            <span class="hidden md:inline">{{
              panelAbierto ? "Cerrar Edición" : "Editar Iceberg"
            }}</span>
          </button>
          <button
            class="flex items-center gap-2 px-3 md:px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-full text-sm font-semibold shadow-lg shadow-blue-500/30 transition-all"
            @click="compartir"
          >
            <Share2 :size="18" />
            <span class="hidden md:inline">Compartir</span>
          </button>
        </div>
      </header>

      <p v-if="error" class="text-center text-red-400 mt-8">
        {{ error }} —
        <a href="#" class="underline" @click.prevent="emit('volver')">volver</a>
      </p>

      <!-- Capas del iceberg -->
      <main class="flex-grow flex flex-col w-full max-w-6xl mx-auto px-4 py-8 gap-4">
        <div
          v-for="(nivel, i) in niveles"
          :key="nivel.id"
          :class="[
            'relative min-h-[160px] transition-all duration-500 group flex flex-col',
            showContainers
              ? `rounded-2xl border border-white/5 overflow-hidden backdrop-blur-sm hover:border-white/20 ${depthColor(i)}`
              : 'py-2',
          ]"
        >
          <!-- Etiqueta del nivel -->
          <div
            :class="[
              'absolute top-0 left-0 text-xs font-bold px-3 py-1 z-10 flex items-center gap-2 transition-colors',
              showContainers
                ? 'bg-black/40 text-white/80 rounded-br-lg backdrop-blur-md'
                : 'text-white/70 drop-shadow-lg bg-black/30 rounded-lg ml-2 mt-2 backdrop-blur-sm',
            ]"
          >
            <Layers :size="12" />
            Nivel {{ nivel.numero }}{{ nivel.nombre ? `: ${nivel.nombre}` : "" }}
          </div>

          <!-- Entradas -->
          <div class="flex-grow flex flex-wrap items-center justify-center gap-4 p-8 pt-10">
            <span
              v-if="!nivel.entries.length"
              class="text-white/30 text-sm italic drop-shadow-md"
              >Vacío</span
            >
            <button
              v-for="entry in nivel.entries"
              :key="entry.id"
              :class="[
                'relative px-5 py-3 rounded-xl shadow-xl transition-all duration-300 hover:scale-105 hover:-translate-y-1',
                showContainers
                  ? 'bg-white/10 hover:bg-white/20 backdrop-blur-md border border-white/10'
                  : 'bg-black/40 hover:bg-black/50 backdrop-blur-md border border-white/10 shadow-black/50',
              ]"
              @click="abrirEntrada(entry, nivel)"
            >
              <span class="font-semibold text-white drop-shadow-md">{{ entry.titulo }}</span>
              <span
                v-if="entry.media.length"
                class="absolute -top-2 -right-2 bg-blue-500 text-white p-1.5 rounded-full shadow-lg"
              >
                <ImageIcon v-if="entry.media[0].tipo === 'image'" :size="12" />
                <Video v-else :size="12" />
              </span>
            </button>
          </div>
        </div>
      </main>

      <footer class="py-6 text-center text-white/50 text-xs backdrop-blur-sm bg-slate-950/50">
        Iceberg Web • Costo Cero
      </footer>
    </div>

    <!-- ============ MODAL DE ENTRADA ============ -->
    <div
      v-if="seleccion"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-lg"
      @click.self="seleccion = null"
    >
      <div
        class="bg-slate-900 border border-slate-700 w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl shadow-2xl anim-modal"
      >
        <!-- Header del modal -->
        <div class="flex justify-between items-center p-5 border-b border-slate-800">
          <div class="flex items-center gap-3 min-w-0">
            <div
              class="bg-blue-500/20 text-blue-400 px-3 py-1 rounded-full text-xs font-bold border border-blue-500/30 shrink-0"
            >
              Nivel {{ seleccion.nivel.numero }}
            </div>
            <h2 class="text-xl font-bold text-white truncate">
              {{ seleccion.entry.titulo }}
            </h2>
          </div>
          <button
            class="text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 p-2 rounded-full transition-colors shrink-0"
            @click="seleccion = null"
          >
            <X :size="20" />
          </button>
        </div>

        <div class="p-6">
          <!-- Media -->
          <div v-if="seleccion.entry.media.length" class="flex flex-wrap gap-3 mb-6">
            <template v-for="m in seleccion.entry.media" :key="m.id">
              <video
                v-if="m.tipo === 'video'"
                :src="m.url"
                controls
                class="h-48 rounded-xl border border-slate-700 bg-slate-800"
              />
              <img
                v-else
                :src="m.url"
                alt=""
                class="h-48 rounded-xl border border-slate-700 object-cover"
              />
            </template>
          </div>

          <!-- Descripción / edición -->
          <template v-if="editandoEntrada">
            <input
              v-model="entradaDraft.titulo"
              maxlength="160"
              class="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-3 text-white mb-3 focus:outline-none focus:border-blue-500"
            />
            <textarea
              v-model="entradaDraft.descripcion"
              :maxlength="MAX_DESC"
              class="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-3 text-white h-32 resize-none focus:outline-none focus:border-blue-500"
            />
            <p class="text-right text-xs text-slate-500 mt-1">
              {{ entradaDraft.descripcion.length }}/{{ MAX_DESC }}
            </p>
            <div class="flex gap-3 mt-2">
              <button
                class="flex-1 bg-blue-600 hover:bg-blue-500 text-white font-bold py-2.5 rounded-xl transition-all"
                @click="guardarEntrada"
              >
                Guardar
              </button>
              <button
                class="px-4 bg-slate-800 hover:bg-slate-700 rounded-xl transition-all"
                @click="editandoEntrada = false"
              >
                Cancelar
              </button>
            </div>
          </template>
          <p v-else class="text-slate-300 text-lg leading-relaxed mb-6 whitespace-pre-wrap">
            {{ seleccion.entry.descripcion || "Sin descripción." }}
          </p>

          <!-- Acciones -->
          <div
            v-if="!editandoEntrada"
            class="flex flex-col sm:flex-row gap-3 pt-4 border-t border-slate-800"
          >
            <button
              :disabled="generando"
              :class="[
                'flex-1 flex items-center justify-center gap-2 py-3 rounded-xl font-bold text-white transition-all shadow-lg',
                generando
                  ? 'bg-slate-700 cursor-not-allowed'
                  : 'bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 shadow-emerald-500/20',
              ]"
              @click="generarVideoNarrado"
            >
              <template v-if="generando">
                <span
                  class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"
                />
                Sintetizando voz y renderizando…
              </template>
              <template v-else>
                <Play :size="18" />
                Generar Video Narrado
              </template>
            </button>

            <label
              class="flex items-center justify-center gap-2 px-4 py-3 bg-slate-800 hover:bg-slate-700 rounded-xl cursor-pointer transition-all text-sm font-semibold"
            >
              <UploadCloud :size="18" />
              {{ subiendo ? "Subiendo…" : "Subir media" }}
              <input
                type="file"
                accept="image/*,video/*"
                class="hidden"
                @change="subirArchivoModal"
              />
            </label>
            <button
              class="px-4 py-3 bg-slate-800 hover:bg-slate-700 rounded-xl transition-all"
              title="Editar"
              @click="empezarEdicionEntrada"
            >
              <Pencil :size="18" />
            </button>
            <button
              class="px-4 py-3 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 rounded-xl transition-all"
              title="Eliminar"
              @click="borrarEntrada"
            >
              <Trash2 :size="18" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ============ PANEL DE EDICIÓN ============ -->
    <div
      v-if="panelAbierto"
      class="fixed top-0 right-0 h-full w-full md:w-96 bg-slate-900/95 backdrop-blur-2xl border-l border-slate-700 z-40 p-6 shadow-2xl flex flex-col gap-8 overflow-y-auto anim-panel"
    >
      <div class="flex justify-between items-center mt-16 md:mt-20">
        <h3 class="text-xl font-bold flex items-center gap-2">
          <Plus :size="20" class="text-blue-500" />
          Nueva Curiosidad
        </h3>
        <button class="md:hidden" @click="panelAbierto = false">
          <X :size="24" class="text-slate-400" />
        </button>
      </div>

      <form class="flex flex-col gap-5" @submit.prevent="crearEntrada">
        <div>
          <label class="block text-sm font-medium text-slate-400 mb-1">Título</label>
          <input
            v-model="nueva.titulo"
            required
            maxlength="160"
            placeholder="Ej. El incidente Max Headroom"
            class="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-400 mb-1"
            >Profundidad (Nivel)</label
          >
          <select
            v-model="nueva.level_id"
            class="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-blue-500 transition-all appearance-none"
          >
            <option v-for="l in niveles" :key="l.id" :value="l.id">
              Nivel {{ l.numero }}{{ l.nombre ? `: ${l.nombre}` : "" }}
            </option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-400 mb-1">
            Descripción
            <span class="text-slate-500 font-normal">(la voz narra este texto)</span>
          </label>
          <textarea
            v-model="nueva.descripcion"
            :maxlength="MAX_DESC"
            placeholder="Cuenta la historia o contexto…"
            class="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all resize-none h-32"
          />
          <p
            class="text-right text-xs mt-1"
            :class="nueva.descripcion.length >= MAX_DESC ? 'text-amber-400' : 'text-slate-500'"
          >
            {{ nueva.descripcion.length }}/{{ MAX_DESC }}
          </p>
        </div>

        <label
          class="p-4 bg-slate-800/50 border border-slate-700 border-dashed rounded-lg text-center cursor-pointer hover:bg-slate-800 transition-colors block"
        >
          <UploadCloud :size="24" class="mx-auto text-slate-400 mb-2" />
          <span class="text-sm text-slate-400 block">
            {{ nueva.file ? nueva.file.name : "Clic para subir imagen/video" }}
          </span>
          <span class="text-xs text-slate-500">Se comprime a WebP / máx. 25 MB video</span>
          <input
            type="file"
            accept="image/*,video/*"
            class="hidden"
            @change="nueva.file = $event.target.files?.[0] || null"
          />
        </label>

        <button
          type="submit"
          :disabled="creandoEntrada || !nueva.titulo.trim() || !niveles.length"
          class="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded-xl shadow-lg shadow-blue-600/20 transition-all"
        >
          {{ creandoEntrada ? "Añadiendo…" : "Añadir al Iceberg" }}
        </button>
        <p v-if="!niveles.length" class="text-xs text-amber-400 -mt-3">
          Primero crea un nivel abajo. ↓
        </p>
      </form>

      <!-- Gestión de niveles -->
      <div class="border-t border-slate-800 pt-6">
        <h4 class="text-sm font-bold text-slate-400 mb-3 flex items-center gap-2">
          <Layers :size="16" /> Niveles
        </h4>
        <div
          v-for="(nivel, i) in niveles"
          :key="nivel.id"
          class="flex items-center gap-2 py-2 border-b border-slate-800/60 text-sm"
        >
          <span class="text-blue-400 font-bold shrink-0">N{{ nivel.numero }}</span>
          <span class="flex-1 truncate text-slate-300">{{ nivel.nombre || "(sin nombre)" }}</span>
          <button
            class="p-1 text-slate-500 hover:text-white disabled:opacity-30"
            :disabled="i === 0"
            @click="moverNivel(nivel, -1)"
          >
            <ChevronUp :size="16" />
          </button>
          <button
            class="p-1 text-slate-500 hover:text-white disabled:opacity-30"
            :disabled="i === niveles.length - 1"
            @click="moverNivel(nivel, 1)"
          >
            <ChevronDown :size="16" />
          </button>
          <button class="p-1 text-slate-500 hover:text-white" @click="renombrarNivel(nivel)">
            <Pencil :size="14" />
          </button>
          <button class="p-1 text-slate-500 hover:text-red-400" @click="borrarNivel(nivel)">
            <Trash2 :size="14" />
          </button>
        </div>
        <form class="flex gap-2 mt-3" @submit.prevent="agregarNivel">
          <input
            v-model="nuevoNivelNombre"
            placeholder="Nombre del nuevo nivel (opcional)"
            class="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
          />
          <button
            class="px-3 bg-white/10 hover:bg-white/20 border border-white/10 rounded-lg transition-all"
          >
            <Plus :size="16" />
          </button>
        </form>
      </div>

      <!-- Zona de peligro -->
      <div class="border-t border-slate-800 pt-6 mt-auto">
        <button
          class="w-full flex items-center justify-center gap-2 py-2.5 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 rounded-xl text-sm font-semibold transition-all"
          @click="borrarIceberg"
        >
          <Trash2 :size="16" /> Eliminar este iceberg
        </button>
      </div>
    </div>

    <!-- Toast -->
    <div
      v-if="toast"
      class="fixed bottom-6 left-1/2 -translate-x-1/2 bg-slate-800 border border-slate-600 rounded-xl px-5 py-3 text-sm shadow-2xl z-[60]"
    >
      {{ toast }}
    </div>
  </div>
</template>
