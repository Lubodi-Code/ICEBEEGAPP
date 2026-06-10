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
  Music,
  Link2,
} from "lucide-vue-next";
import { api, generarVideo, enlacePublico, enlaceEditor } from "../api.js";
import { recordarReciente, olvidarReciente } from "../recientes.js";
import ICEBERG_BG_URL from "../assets/Iceberg (1).jpg";

const props = defineProps({
  slug: { type: String, required: true },
  token: { type: String, default: null },
});
const emit = defineEmits(["volver"]);

// Mismo límite que DESCRIPCION_MAX en el backend (lo que el TTS narra).
const MAX_DESC = 500;

const iceberg = ref(null);
const error = ref("");
const toast = ref("");
const showContainers = ref(true);
const panelAbierto = ref(false);

const editandoTitulo = ref(false);
const tituloDraft = ref("");

// Acceso por enlace de editor compartido (token en la URL).
const accesoToken = ref(null); // null | "valido" | "invalido"

// Modal de detalle: { entry, nivel }
const seleccion = ref(null);
const editandoEntrada = ref(false);
const entradaDraft = ref({ titulo: "", descripcion: "" });
const generando = ref(false);
const subiendo = ref(false);
const subiendoMusica = ref(false);

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

// Mezcla lineal entre dos colores RGB según t∈[0,1].
function mix(a, b, t) {
  return a.map((c, k) => Math.round(c + (b[k] - c) * t)).join(",");
}

// Fondo de cada capa: se oscurece y "enfría" al descender hacia lo desconocido.
function bandStyle(i, n) {
  const t = n > 1 ? i / (n - 1) : 0;
  const top = mix([24, 64, 56], [4, 12, 14], t); // verde abisal → negro
  const bot = mix([10, 36, 34], [1, 5, 8], t);
  return {
    background: `linear-gradient(180deg, rgba(${top},0.46), rgba(${bot},0.72))`,
  };
}

// Profundidad simbólica de cada nivel (más abajo = más metros).
function depthLabel(i) {
  const m = Math.round((i + 1) * 120 * (1 + i * 0.35));
  return m >= 1000 ? `${(m / 1000).toFixed(1)} km` : `${m} m`;
}

// Nivel de clearance ficticio según profundidad.
function clearanceLabel(i) {
  return `NIVEL DE ACCESO ${"I".repeat(Math.min(i + 1, 5))}`;
}

function nombreMusica(url) {
  try {
    const f = decodeURIComponent(url.split("/").pop() || "");
    return f.length > 36 ? `${f.slice(0, 33)}…` : f;
  } catch {
    return url;
  }
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

async function validarToken() {
  if (!props.token || !iceberg.value) return;
  try {
    const r = await api.validarTokenEdicion(iceberg.value.id, props.token);
    accesoToken.value = r.valid ? "valido" : "invalido";
  } catch {
    accesoToken.value = "invalido";
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
  avisar("🔗 Enlace público copiado");
}

async function compartirEditor() {
  try {
    const r = await api.crearTokenEdicion(iceberg.value.id);
    await navigator.clipboard.writeText(enlaceEditor(iceberg.value.slug, r.token));
    const dias = Math.max(
      1,
      Math.round((new Date(r.expires_at) - Date.now()) / 86400000)
    );
    avisar(`🗝️ Enlace de editor copiado (caduca en ${dias} días)`);
  } catch (e) {
    avisar(`Error: ${e.message}`);
  }
}

async function borrarIceberg() {
  if (!confirm(`¿Destruir el expediente "${iceberg.value.titulo}" y todo su contenido?`)) return;
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

// --- música del nivel ---------------------------------------------------
async function subirMusicaNivel(event, nivel) {
  const file = event.target.files?.[0];
  if (!file) return;
  subiendoMusica.value = true;
  try {
    await api.subirMusica(nivel.id, file);
    await cargar();
    avisar("🎵 Música del nivel configurada");
  } catch (e) {
    avisar(`Error al subir música: ${e.message}`);
  } finally {
    subiendoMusica.value = false;
    event.target.value = "";
  }
}

async function quitarMusicaNivel(nivel) {
  await api.editarNivel(nivel.id, { music_url: "" });
  await cargar();
  avisar("🔇 Música eliminada del nivel");
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
    avisar("✅ Evidencia archivada en el expediente");
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
    avisar("📷 Evidencia adjuntada");
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
      // Todos los niveles, en orden: la intro muestra el mapa y hace zoom al elegido.
      levels: niveles.value.map((l) => ({ numero: l.numero, nombre: l.nombre })),
      music_url: nivel.music_url || null,
      show_url: false,
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

onMounted(async () => {
  await cargar();
  await validarToken();
});
watch(() => props.slug, cargar);
</script>

<template>
  <div class="ocean relative min-h-screen text-slate-100 overflow-x-hidden">
    <!-- Atmósfera de vigilancia -->
    <div class="grain" />
    <div class="scanlines" />
    <div class="light-rays fixed inset-0 z-0 pointer-events-none" />
    <div class="bubbles fixed inset-0 z-0 pointer-events-none" />

    <div class="relative z-10 flex flex-col min-h-screen">
      <!-- Header de expediente -->
      <header
        class="p-4 md:p-6 flex justify-between items-center gap-3 sticky top-0 z-20 backdrop-blur-sm border-b border-[#d8b15a]/15"
        style="background: linear-gradient(180deg, rgba(4,8,10,0.92), rgba(4,8,10,0.55) 75%, transparent);"
      >
        <div class="flex items-center gap-3 min-w-0">
          <button
            class="p-2 bg-white/5 hover:bg-white/15 rounded border border-[#d8b15a]/20 transition-all shrink-0"
            title="Volver al archivo"
            @click="emit('volver')"
          >
            <ArrowLeft :size="18" />
          </button>
          <div class="min-w-0">
            <p class="dossier-label mb-0.5">Expediente Nº {{ iceberg?.slug || "—" }}</p>
            <div v-if="editandoTitulo" class="flex items-center gap-2">
              <input
                v-model="tituloDraft"
                maxlength="120"
                class="mono bg-black/80 border border-[#d8b15a]/30 rounded px-3 py-1.5 text-xl font-bold text-white focus:outline-none focus:border-[#56d68a]/70 w-64 md:w-96"
                @keyup.enter="guardarTitulo"
                @keyup.esc="editandoTitulo = false"
              />
              <button
                class="p-2 bg-[#56d68a]/20 hover:bg-[#56d68a]/30 border border-[#56d68a]/40 text-[#56d68a] rounded transition-all"
                @click="guardarTitulo"
              >
                <Check :size="16" />
              </button>
            </div>
            <h1
              v-else
              class="mono text-xl md:text-2xl font-bold tracking-tight text-white drop-shadow-lg truncate cursor-pointer group flex items-center gap-2 uppercase"
              title="Clic para editar el título"
              @click="
                tituloDraft = iceberg?.titulo || '';
                editandoTitulo = true;
              "
            >
              {{ iceberg?.titulo || "…" }}
              <Pencil
                :size="14"
                class="opacity-0 group-hover:opacity-60 transition-opacity shrink-0"
              />
            </h1>
            <p class="mono text-[11px] text-slate-400 mt-0.5">
              {{ niveles.length }} nivel(es) · {{ totalEntradas }} evidencia(s)
              <a
                :href="iceberg ? enlacePublico(iceberg.slug) : '#'"
                target="_blank"
                rel="noopener"
                class="inline-flex items-center gap-1 text-[#56d68a] hover:text-[#8aedb4] ml-2"
              >
                <ExternalLink :size="11" /> versión pública
              </a>
            </p>
          </div>
        </div>

        <div class="flex gap-2 shrink-0 items-center">
          <span class="stamp hidden lg:inline-block text-[10px]">Top Secret</span>
          <button
            class="flex items-center gap-2 px-3 py-2 bg-white/5 hover:bg-white/15 rounded text-xs mono uppercase tracking-wider transition-all border border-[#d8b15a]/20"
            @click="showContainers = !showContainers"
          >
            <EyeOff v-if="showContainers" :size="16" />
            <Eye v-else :size="16" />
            <span class="hidden md:inline">{{ showContainers ? "Ocultar capas" : "Mostrar capas" }}</span>
          </button>
          <button
            class="flex items-center gap-2 px-3 py-2 bg-white/5 hover:bg-white/15 rounded text-xs mono uppercase tracking-wider transition-all border border-[#d8b15a]/20"
            @click="panelAbierto = !panelAbierto"
          >
            <X v-if="panelAbierto" :size="16" />
            <Edit3 v-else :size="16" />
            <span class="hidden md:inline">{{ panelAbierto ? "Cerrar" : "Editar" }}</span>
          </button>
          <button
            class="flex items-center gap-2 px-3 py-2 bg-[#d8b15a]/15 hover:bg-[#d8b15a]/25 border border-[#d8b15a]/40 text-[#d8b15a] rounded text-xs mono uppercase tracking-wider transition-all"
            title="Copiar enlace de edición con clave temporal"
            @click="compartirEditor"
          >
            <Link2 :size="16" />
            <span class="hidden md:inline">Editor</span>
          </button>
          <button
            class="flex items-center gap-2 px-3 py-2 bg-[#56d68a]/15 hover:bg-[#56d68a]/25 border border-[#56d68a]/40 text-[#56d68a] rounded text-xs mono uppercase tracking-wider transition-all"
            @click="compartir"
          >
            <Share2 :size="16" />
            <span class="hidden md:inline">Compartir</span>
          </button>
        </div>
      </header>

      <!-- Aviso de acceso por enlace de editor -->
      <div
        v-if="accesoToken"
        class="mono text-center text-xs py-2 border-b"
        :class="
          accesoToken === 'valido'
            ? 'text-[#56d68a] border-[#56d68a]/30 bg-[#56d68a]/10'
            : 'text-red-400 border-red-500/30 bg-red-500/10'
        "
      >
        {{
          accesoToken === "valido"
            ? "🗝️ ACCESO CONCEDIDO — estás editando mediante un enlace de editor compartido"
            : "⛔ CLAVE DE EDITOR CADUCADA O INVÁLIDA — el enlace ya no es de fiar"
        }}
      </div>

      <p v-if="error" class="mono text-center text-red-400 mt-8">
        ⚠ {{ error }} —
        <a href="#" class="underline" @click.prevent="emit('volver')">volver</a>
      </p>

      <!-- Zona del iceberg: la imagen está anclada a los niveles, no a la ventana.
           La punta queda arriba (Nivel 1) y el cuerpo desciende junto con las capas. -->
      <div class="relative grow">
        <div class="absolute inset-0 z-0 pointer-events-none select-none overflow-hidden">
          <img
            :src="ICEBERG_BG_URL"
            alt=""
            class="w-full h-full object-cover object-top"
            style="filter: saturate(0.65) brightness(0.7) hue-rotate(25deg);"
          />
          <!-- Degradado que se hunde con los niveles: superficie → abismo -->
          <div
            class="absolute inset-0"
            style="
              background: linear-gradient(
                180deg,
                rgba(4, 10, 12, 0.15)  0%,
                rgba(5, 14, 16, 0.30) 20%,
                rgba(5, 18, 20, 0.55) 45%,
                rgba(4, 13, 15, 0.80) 68%,
                rgba(2,  7,  9, 0.94) 85%,
                #030608               100%
              );
            "
          />
          <!-- Viñeta lateral para enfocar el centro -->
          <div
            class="absolute inset-0"
            style="background: radial-gradient(ellipse 70% 100% at 50% 50%, transparent 55%, rgba(1,5,7,0.65) 100%);"
          />
        </div>

        <!-- Capas del iceberg -->
        <main class="relative z-10 flex flex-col w-full max-w-5xl mx-auto px-4 pb-12 gap-5">
        <!-- La punta del iceberg asoma aquí; el Nivel 1 empieza en la línea de flotación -->
        <div class="h-[34vh] md:h-[40vh] shrink-0" aria-hidden="true" />

        <!-- Línea de flotación / frontera de lo conocido -->
        <div
          v-if="niveles.length"
          class="waterline flex items-center gap-4 text-[10px] uppercase tracking-[0.35em] font-bold mono"
        >
          <span class="h-px flex-1 bg-gradient-to-r from-transparent via-[#56d68a]/50 to-[#56d68a]/70" />
          <span class="text-[#56d68a]/90">⟨ fin de la información pública ⟩</span>
          <span class="h-px flex-1 bg-gradient-to-l from-transparent via-[#56d68a]/50 to-[#56d68a]/70" />
        </div>

        <div
          v-for="(nivel, i) in niveles"
          :key="nivel.id"
          :style="showContainers ? bandStyle(i, niveles.length) : null"
          :class="[
            'relative min-h-40 transition-all duration-500 group flex',
            showContainers
              ? 'rounded-lg border border-[#d8b15a]/15 ring-1 ring-inset ring-white/5 overflow-hidden backdrop-blur-md shadow-xl shadow-black/40 hover:border-[#56d68a]/30'
              : 'py-2',
          ]"
        >
          <!-- Regla de profundidad lateral -->
          <div
            v-if="showContainers"
            class="hidden sm:flex flex-col items-center justify-center w-20 shrink-0 border-r border-[#d8b15a]/15 bg-black/25"
          >
            <span class="mono text-[#56d68a] font-bold text-lg leading-none drop-shadow">{{
              String(nivel.numero).padStart(2, "0")
            }}</span>
            <span class="mono text-[9px] text-[#d8b15a]/60 mt-1">{{ depthLabel(i) }}</span>
            <Music
              v-if="nivel.music_url"
              :size="11"
              class="text-[#56d68a]/70 mt-1.5"
              title="Este nivel tiene música configurada"
            />
          </div>

          <div class="relative flex-1 flex flex-col min-w-0">
            <!-- Etiqueta del nivel -->
            <div
              :class="[
                'mono text-[10px] font-bold px-3 py-1.5 z-10 flex items-center gap-2 transition-colors w-fit uppercase tracking-[0.2em]',
                showContainers
                  ? 'bg-black/40 text-[#d8b15a]/90 rounded-br backdrop-blur-md'
                  : 'text-white/70 drop-shadow-lg bg-black/40 rounded ml-2 mt-2 backdrop-blur-sm',
              ]"
            >
              <Layers :size="11" />
              Nivel {{ nivel.numero }}{{ nivel.nombre ? ` · ${nivel.nombre}` : "" }}
              <span class="text-[#56d68a]/60 normal-case tracking-normal hidden md:inline">— {{ clearanceLabel(i) }}</span>
              <span class="sm:hidden text-[#d8b15a]/50">· {{ depthLabel(i) }}</span>
            </div>

            <!-- Entradas -->
            <div class="grow flex flex-wrap items-center justify-center gap-4 p-8 pt-6">
              <span
                v-if="!nivel.entries.length"
                class="mono text-white/25 text-xs italic drop-shadow-md uppercase tracking-widest"
                >[ sin registros ]</span
              >
              <button
                v-for="entry in nivel.entries"
                :key="entry.id"
                class="evidence relative px-5 py-3 rounded"
                @click="abrirEntrada(entry, nivel)"
              >
                <span class="mono font-semibold text-slate-100 drop-shadow-md text-sm">{{
                  entry.titulo
                }}</span>
                <span
                  v-if="entry.media.length"
                  class="absolute -top-2 -right-2 bg-[#56d68a]/90 text-black p-1.5 rounded-full shadow-lg"
                >
                  <ImageIcon v-if="entry.media[0].tipo === 'image'" :size="11" />
                  <Video v-else :size="11" />
                </span>
              </button>
            </div>
          </div>
        </div>
        </main>
      </div>

      <footer class="py-6 text-center backdrop-blur-sm bg-black/60 border-t border-[#d8b15a]/10">
        <p class="mono text-[10px] uppercase tracking-[0.3em] text-slate-600">
          Iceberg Web · Este documento se autodestruirá… algún día
        </p>
      </footer>
    </div>

    <!-- ============ MODAL DE ENTRADA (documento clasificado) ============ -->
    <div
      v-if="seleccion"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-lg"
      @click.self="seleccion = null"
    >
      <div
        class="dossier-card w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-lg anim-modal"
      >
        <!-- Header del modal -->
        <div class="flex justify-between items-center p-5 border-b border-[#d8b15a]/15">
          <div class="flex items-center gap-3 min-w-0">
            <div
              class="mono bg-[#c03131]/15 text-[#e07a7a] px-3 py-1 rounded text-[10px] font-bold border border-[#c03131]/40 shrink-0 uppercase tracking-[0.2em]"
            >
              Nivel {{ seleccion.nivel.numero }}
            </div>
            <h2 class="mono text-lg font-bold text-white truncate uppercase">
              {{ seleccion.entry.titulo }}
            </h2>
          </div>
          <button
            class="text-slate-400 hover:text-white bg-white/5 hover:bg-white/15 p-2 rounded transition-colors shrink-0"
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
                class="h-48 rounded border border-[#d8b15a]/20 bg-black"
              />
              <img
                v-else
                :src="m.url"
                alt=""
                class="h-48 rounded border border-[#d8b15a]/20 object-cover"
                style="filter: saturate(0.85);"
              />
            </template>
          </div>

          <!-- Descripción / edición -->
          <template v-if="editandoEntrada">
            <input
              v-model="entradaDraft.titulo"
              maxlength="160"
              class="mono w-full bg-black/70 border border-[#d8b15a]/25 rounded px-4 py-3 text-white mb-3 focus:outline-none focus:border-[#56d68a]/70"
            />
            <textarea
              v-model="entradaDraft.descripcion"
              :maxlength="MAX_DESC"
              class="mono w-full bg-black/70 border border-[#d8b15a]/25 rounded px-4 py-3 text-white h-32 resize-none focus:outline-none focus:border-[#56d68a]/70"
            />
            <p class="mono text-right text-xs text-slate-500 mt-1">
              {{ entradaDraft.descripcion.length }}/{{ MAX_DESC }}
            </p>
            <div class="flex gap-3 mt-2">
              <button
                class="mono flex-1 bg-[#56d68a]/20 hover:bg-[#56d68a]/30 border border-[#56d68a]/40 text-[#56d68a] font-bold py-2.5 rounded uppercase tracking-wider text-sm transition-all"
                @click="guardarEntrada"
              >
                Guardar
              </button>
              <button
                class="px-4 bg-white/5 hover:bg-white/15 border border-[#d8b15a]/20 rounded transition-all"
                @click="editandoEntrada = false"
              >
                Cancelar
              </button>
            </div>
          </template>
          <p v-else class="mono text-slate-300 leading-relaxed mb-6 whitespace-pre-wrap text-[15px]">
            {{ seleccion.entry.descripcion || "[ Descripción redactada por la agencia. ]" }}
          </p>

          <!-- Banda sonora del nivel -->
          <div
            v-if="!editandoEntrada"
            class="mb-6 p-4 rounded border border-[#d8b15a]/20 bg-black/30"
          >
            <p class="dossier-label mb-2 flex items-center gap-2">
              <Music :size="12" /> Banda sonora del nivel {{ seleccion.nivel.numero }}
            </p>
            <div class="flex flex-col sm:flex-row sm:items-center gap-3">
              <p class="mono text-xs flex-1 truncate" :class="seleccion.nivel.music_url ? 'text-[#56d68a]' : 'text-slate-500 italic'">
                {{
                  seleccion.nivel.music_url
                    ? `♪ ${nombreMusica(seleccion.nivel.music_url)}`
                    : "Sin música — el video usará solo la narración"
                }}
              </p>
              <div class="flex gap-2 shrink-0">
                <label
                  class="mono flex items-center gap-2 px-3 py-2 bg-white/5 hover:bg-white/15 border border-[#d8b15a]/25 rounded cursor-pointer transition-all text-xs uppercase tracking-wider"
                >
                  <UploadCloud :size="14" />
                  {{ subiendoMusica ? "Subiendo…" : "Subir audio" }}
                  <input
                    type="file"
                    accept="audio/*"
                    class="hidden"
                    @change="subirMusicaNivel($event, seleccion.nivel)"
                  />
                </label>
                <button
                  v-if="seleccion.nivel.music_url"
                  class="px-3 py-2 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 rounded transition-all"
                  title="Quitar música"
                  @click="quitarMusicaNivel(seleccion.nivel)"
                >
                  <Trash2 :size="14" />
                </button>
              </div>
            </div>
          </div>

          <!-- Acciones -->
          <div
            v-if="!editandoEntrada"
            class="flex flex-col sm:flex-row gap-3 pt-4 border-t border-[#d8b15a]/15"
          >
            <button
              :disabled="generando"
              :class="[
                'mono flex-1 flex items-center justify-center gap-2 py-3 rounded font-bold uppercase tracking-wider text-sm transition-all',
                generando
                  ? 'bg-white/5 text-slate-500 cursor-not-allowed border border-white/10'
                  : 'bg-[#56d68a]/20 hover:bg-[#56d68a]/30 border border-[#56d68a]/50 text-[#56d68a] shadow-lg shadow-[#56d68a]/10',
              ]"
              @click="generarVideoNarrado"
            >
              <template v-if="generando">
                <span
                  class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"
                />
                Filtrando el informe…
              </template>
              <template v-else>
                <Play :size="16" />
                Generar video narrado
              </template>
            </button>

            <label
              class="mono flex items-center justify-center gap-2 px-4 py-3 bg-white/5 hover:bg-white/15 border border-[#d8b15a]/20 rounded cursor-pointer transition-all text-xs uppercase tracking-wider"
            >
              <UploadCloud :size="16" />
              {{ subiendo ? "Subiendo…" : "Adjuntar evidencia" }}
              <input
                type="file"
                accept="image/*,video/*"
                class="hidden"
                @change="subirArchivoModal"
              />
            </label>
            <button
              class="px-4 py-3 bg-white/5 hover:bg-white/15 border border-[#d8b15a]/20 rounded transition-all"
              title="Editar"
              @click="empezarEdicionEntrada"
            >
              <Pencil :size="16" />
            </button>
            <button
              class="px-4 py-3 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 rounded transition-all"
              title="Eliminar"
              @click="borrarEntrada"
            >
              <Trash2 :size="16" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ============ PANEL DE EDICIÓN ============ -->
    <div
      v-if="panelAbierto"
      class="fixed top-0 right-0 h-full w-full md:w-96 bg-[#070b10]/97 backdrop-blur-2xl border-l border-[#d8b15a]/20 z-40 p-6 shadow-2xl flex flex-col gap-8 overflow-y-auto anim-panel"
    >
      <div class="flex justify-between items-center mt-16 md:mt-20">
        <h3 class="mono text-lg font-bold flex items-center gap-2 uppercase tracking-wider">
          <Plus :size="18" class="text-[#56d68a]" />
          Nueva evidencia
        </h3>
        <button class="md:hidden" @click="panelAbierto = false">
          <X :size="24" class="text-slate-400" />
        </button>
      </div>

      <form class="flex flex-col gap-5" @submit.prevent="crearEntrada">
        <div>
          <label class="dossier-label block mb-1.5">Título</label>
          <input
            v-model="nueva.titulo"
            required
            maxlength="160"
            placeholder="Ej. El incidente Max Headroom"
            class="mono w-full bg-black/70 border border-[#d8b15a]/25 rounded px-4 py-3 text-white placeholder-slate-600 focus:outline-none focus:border-[#56d68a]/70 focus:ring-1 focus:ring-[#56d68a]/30 transition-all"
          />
        </div>

        <div>
          <label class="dossier-label block mb-1.5">Profundidad (nivel)</label>
          <select
            v-model="nueva.level_id"
            class="mono w-full bg-black/70 border border-[#d8b15a]/25 rounded px-4 py-3 text-white focus:outline-none focus:border-[#56d68a]/70 transition-all appearance-none"
          >
            <option v-for="l in niveles" :key="l.id" :value="l.id">
              Nivel {{ l.numero }}{{ l.nombre ? `: ${l.nombre}` : "" }}
            </option>
          </select>
        </div>

        <div>
          <label class="dossier-label block mb-1.5">
            Descripción
            <span class="text-slate-500 normal-case tracking-normal">(la voz narra este texto)</span>
          </label>
          <textarea
            v-model="nueva.descripcion"
            :maxlength="MAX_DESC"
            placeholder="Lo que el público no debería saber…"
            class="mono w-full bg-black/70 border border-[#d8b15a]/25 rounded px-4 py-3 text-white placeholder-slate-600 focus:outline-none focus:border-[#56d68a]/70 focus:ring-1 focus:ring-[#56d68a]/30 transition-all resize-none h-32"
          />
          <p
            class="mono text-right text-xs mt-1"
            :class="nueva.descripcion.length >= MAX_DESC ? 'text-amber-400' : 'text-slate-600'"
          >
            {{ nueva.descripcion.length }}/{{ MAX_DESC }}
          </p>
        </div>

        <label
          class="p-4 bg-black/40 border border-[#d8b15a]/25 border-dashed rounded text-center cursor-pointer hover:bg-black/60 transition-colors block"
        >
          <UploadCloud :size="24" class="mx-auto text-slate-400 mb-2" />
          <span class="mono text-xs text-slate-400 block">
            {{ nueva.file ? nueva.file.name : "Adjuntar imagen/video como evidencia" }}
          </span>
          <span class="mono text-[10px] text-slate-600">Se comprime a WebP / máx. 25 MB video</span>
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
          class="mono w-full bg-[#56d68a]/20 hover:bg-[#56d68a]/30 disabled:opacity-40 disabled:cursor-not-allowed border border-[#56d68a]/50 text-[#56d68a] font-bold py-3 px-4 rounded uppercase tracking-wider text-sm transition-all"
        >
          {{ creandoEntrada ? "Archivando…" : "Archivar en el expediente" }}
        </button>
        <p v-if="!niveles.length" class="mono text-xs text-amber-400 -mt-3">
          Primero crea un nivel abajo. ↓
        </p>
      </form>

      <!-- Gestión de niveles -->
      <div class="border-t border-[#d8b15a]/15 pt-6">
        <h4 class="dossier-label mb-3 flex items-center gap-2">
          <Layers :size="14" /> Niveles de profundidad
        </h4>
        <div
          v-for="(nivel, i) in niveles"
          :key="nivel.id"
          class="flex items-center gap-2 py-2 border-b border-white/5 text-sm"
        >
          <span class="mono text-[#56d68a] font-bold shrink-0 text-xs">N{{ nivel.numero }}</span>
          <span class="mono flex-1 truncate text-slate-300 text-xs">{{ nivel.nombre || "(sin nombre)" }}</span>
          <Music
            v-if="nivel.music_url"
            :size="12"
            class="text-[#d8b15a]/70 shrink-0"
            title="Tiene música"
          />
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
            class="mono flex-1 bg-black/70 border border-[#d8b15a]/25 rounded px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-[#56d68a]/70"
          />
          <button
            class="px-3 bg-white/5 hover:bg-white/15 border border-[#d8b15a]/20 rounded transition-all"
          >
            <Plus :size="16" />
          </button>
        </form>
      </div>

      <!-- Zona de peligro -->
      <div class="border-t border-[#c03131]/30 pt-6 mt-auto">
        <button
          class="mono w-full flex items-center justify-center gap-2 py-2.5 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 rounded text-xs font-semibold uppercase tracking-wider transition-all"
          @click="borrarIceberg"
        >
          <Trash2 :size="14" /> Destruir expediente completo
        </button>
      </div>
    </div>

    <!-- Toast -->
    <div
      v-if="toast"
      class="mono fixed bottom-6 left-1/2 -translate-x-1/2 bg-black/90 border border-[#56d68a]/40 rounded px-5 py-3 text-sm shadow-2xl z-[60] text-[#cdeedd]"
    >
      {{ toast }}
    </div>
  </div>
</template>
