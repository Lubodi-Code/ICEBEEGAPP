<script setup>
import { ref, computed } from "vue";
import { api, generarVideo } from "../api.js";

const props = defineProps({
  nivel: { type: Object, required: true },
  icebergTitulo: { type: String, required: true },
  primero: Boolean,
  ultimo: Boolean,
});
const emit = defineEmits(["refrescar", "avisar", "mover"]);

const abierto = ref(true);
const nuevaEntrada = ref({ titulo: "", descripcion: "" });
const generando = ref(null); // id de la entrada cuyo video se está generando
const subiendo = ref(null); // id de la entrada cuya media se está subiendo

const entradas = computed(() => [...props.nivel.entries].sort((a, b) => a.orden - b.orden));

async function renombrarNivel() {
  const nombre = prompt("Nombre del nivel:", props.nivel.nombre || "");
  if (nombre === null) return;
  await api.editarNivel(props.nivel.id, { nombre: nombre.trim() || null });
  emit("refrescar");
}

async function borrarNivel() {
  if (!confirm(`¿Eliminar el nivel ${props.nivel.numero} y sus entradas?`)) return;
  await api.borrarNivel(props.nivel.id);
  emit("refrescar");
}

async function agregarEntrada() {
  if (!nuevaEntrada.value.titulo.trim()) return;
  await api.crearEntrada(props.nivel.id, {
    titulo: nuevaEntrada.value.titulo.trim(),
    descripcion: nuevaEntrada.value.descripcion.trim(),
    orden: entradas.value.length,
  });
  nuevaEntrada.value = { titulo: "", descripcion: "" };
  emit("refrescar");
}

async function editarEntrada(entrada) {
  const titulo = prompt("Título:", entrada.titulo);
  if (titulo === null) return;
  const descripcion = prompt("Descripción:", entrada.descripcion);
  if (descripcion === null) return;
  await api.editarEntrada(entrada.id, {
    titulo: titulo.trim() || entrada.titulo,
    descripcion: descripcion.trim(),
  });
  emit("refrescar");
}

async function borrarEntrada(entrada) {
  if (!confirm(`¿Eliminar "${entrada.titulo}"?`)) return;
  await api.borrarEntrada(entrada.id);
  emit("refrescar");
}

async function subirArchivo(entrada, event) {
  const file = event.target.files?.[0];
  if (!file) return;
  subiendo.value = entrada.id;
  try {
    await api.subirMedia(entrada.id, file);
    emit("refrescar");
  } catch (e) {
    emit("avisar", `Error al subir: ${e.message}`);
  } finally {
    subiendo.value = null;
    event.target.value = "";
  }
}

async function video(entrada) {
  generando.value = entrada.id;
  try {
    const blob = await generarVideo({
      iceberg_title: props.icebergTitulo,
      level_number: props.nivel.numero,
      level_name: props.nivel.nombre,
      entry_title: entrada.titulo,
      description: entrada.descripcion,
      media: entrada.media.map((m) => ({ url: m.url, tipo: m.tipo })),
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `iceberg-${entrada.titulo.toLowerCase().replace(/\s+/g, "-")}.mp4`;
    a.click();
    URL.revokeObjectURL(url);
    emit("avisar", "🎬 Video descargado");
  } catch (e) {
    emit("avisar", `Error al generar video: ${e.message}`);
  } finally {
    generando.value = null;
  }
}
</script>

<template>
  <section class="panel">
    <div class="nivel-header" @click="abierto = !abierto">
      <span>{{ abierto ? "▾" : "▸" }}</span>
      <span class="badge">Nivel {{ nivel.numero }}</span>
      <strong class="crece">{{ nivel.nombre || "(sin nombre)" }}</strong>
      <span class="dim">{{ entradas.length }} entrada(s)</span>
      <button class="fantasma" :disabled="primero" @click.stop="emit('mover', -1)">↑</button>
      <button class="fantasma" :disabled="ultimo" @click.stop="emit('mover', 1)">↓</button>
      <button class="fantasma" @click.stop="renombrarNivel">✏️</button>
      <button class="fantasma" @click.stop="borrarNivel">🗑</button>
    </div>

    <div v-if="abierto">
      <div v-for="entrada in entradas" :key="entrada.id" class="entrada">
        <div class="fila">
          <strong class="crece">{{ entrada.titulo }}</strong>
          <button class="fantasma" @click="editarEntrada(entrada)">✏️</button>
          <button class="fantasma" @click="borrarEntrada(entrada)">🗑</button>
        </div>
        <p v-if="entrada.descripcion" class="dim" style="margin: 4px 0">
          {{ entrada.descripcion }}
        </p>

        <div v-if="entrada.media.length" class="media-grid">
          <template v-for="m in entrada.media" :key="m.id">
            <video v-if="m.tipo === 'video'" :src="m.url" controls muted />
            <img v-else :src="m.url" alt="" />
          </template>
        </div>

        <div class="fila" style="margin-top: 8px">
          <label>
            <input
              type="file"
              accept="image/*,video/*"
              style="display: none"
              @change="subirArchivo(entrada, $event)"
            />
            <span
              class="badge"
              style="cursor: pointer"
              role="button"
              tabindex="0"
            >
              {{ subiendo === entrada.id ? "Subiendo…" : "📷 Subir foto/video" }}
            </span>
          </label>
          <button :disabled="generando === entrada.id" @click="video(entrada)">
            {{ generando === entrada.id ? "Generando…" : "🎬 Generar video" }}
          </button>
        </div>
      </div>

      <form class="fila" style="margin-top: 12px" @submit.prevent="agregarEntrada">
        <input
          v-model="nuevaEntrada.titulo"
          class="crece"
          placeholder="Título de la entrada"
          maxlength="160"
        />
        <input
          v-model="nuevaEntrada.descripcion"
          class="crece"
          placeholder="Descripción (opcional)"
        />
        <button :disabled="!nuevaEntrada.titulo.trim()">＋ Entrada</button>
      </form>
    </div>
  </section>
</template>
