<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { api, enlacePublico } from "../api.js";
import { recordarReciente, olvidarReciente } from "../recientes.js";
import LevelCard from "./LevelCard.vue";

const props = defineProps({ slug: { type: String, required: true } });
const emit = defineEmits(["volver"]);

const iceberg = ref(null);
const error = ref("");
const toast = ref("");
const editandoTitulo = ref(false);
const tituloDraft = ref("");
const nuevoNivelNombre = ref("");

const niveles = computed(() =>
  iceberg.value ? [...iceberg.value.levels].sort((a, b) => a.orden - b.orden || a.numero - b.numero) : []
);

async function cargar() {
  error.value = "";
  try {
    iceberg.value = await api.obtenerIceberg(props.slug);
    recordarReciente(iceberg.value.slug, iceberg.value.titulo);
  } catch (e) {
    error.value = e.message;
  }
}

function avisar(msg) {
  toast.value = msg;
  setTimeout(() => (toast.value = ""), 2500);
}

async function guardarTitulo() {
  const t = tituloDraft.value.trim();
  if (t && t !== iceberg.value.titulo) {
    await api.editarIceberg(iceberg.value.id, { titulo: t });
    await cargar();
  }
  editandoTitulo.value = false;
}

async function copiarEnlace() {
  await navigator.clipboard.writeText(enlacePublico(iceberg.value.slug));
  avisar("Enlace copiado 📋");
}

async function borrarIceberg() {
  if (!confirm(`¿Eliminar "${iceberg.value.titulo}" y todo su contenido?`)) return;
  await api.borrarIceberg(iceberg.value.id);
  olvidarReciente(iceberg.value.slug);
  emit("volver");
}

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

async function moverNivel(levelId, delta) {
  const ids = niveles.value.map((l) => l.id);
  const i = ids.indexOf(levelId);
  const j = i + delta;
  if (j < 0 || j >= ids.length) return;
  [ids[i], ids[j]] = [ids[j], ids[i]];
  await api.reordenarNiveles(ids);
  await cargar();
}

onMounted(cargar);
watch(() => props.slug, cargar);
</script>

<template>
  <p v-if="error" class="error">
    {{ error }} — <a href="#" @click.prevent="emit('volver')">volver</a>
  </p>

  <template v-if="iceberg">
    <section class="panel">
      <div class="fila">
        <template v-if="editandoTitulo">
          <input
            v-model="tituloDraft"
            class="crece"
            maxlength="120"
            @keyup.enter="guardarTitulo"
            @keyup.esc="editandoTitulo = false"
          />
          <button @click="guardarTitulo">Guardar</button>
        </template>
        <template v-else>
          <h2 class="crece" style="margin: 0">{{ iceberg.titulo }}</h2>
          <button
            class="fantasma"
            @click="
              tituloDraft = iceberg.titulo;
              editandoTitulo = true;
            "
          >
            ✏️ Editar
          </button>
        </template>
      </div>
      <div class="fila" style="margin-top: 12px">
        <button @click="copiarEnlace">🔗 Copiar enlace</button>
        <a :href="enlacePublico(iceberg.slug)" target="_blank" rel="noopener">
          <button type="button">👁 Ver página pública</button>
        </a>
        <span class="crece"></span>
        <button class="peligro" @click="borrarIceberg">🗑 Eliminar iceberg</button>
      </div>
    </section>

    <LevelCard
      v-for="(nivel, i) in niveles"
      :key="nivel.id"
      :nivel="nivel"
      :iceberg-titulo="iceberg.titulo"
      :primero="i === 0"
      :ultimo="i === niveles.length - 1"
      @refrescar="cargar"
      @avisar="avisar"
      @mover="(delta) => moverNivel(nivel.id, delta)"
    />

    <section class="panel">
      <h3 style="margin-top: 0">Agregar nivel</h3>
      <form class="fila" @submit.prevent="agregarNivel">
        <input
          v-model="nuevoNivelNombre"
          class="crece"
          placeholder="Nombre del nivel (opcional), ej: La superficie"
        />
        <button>＋ Nivel {{ niveles.length ? Math.max(...niveles.map((l) => l.numero)) + 1 : 1 }}</button>
      </form>
    </section>
  </template>

  <div v-if="toast" class="toast">{{ toast }}</div>
</template>
