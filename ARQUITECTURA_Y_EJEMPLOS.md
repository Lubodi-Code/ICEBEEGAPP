# 📐 Arquitectura y Ejemplos de Código

## 1. Flujo de Generación de Video - Versión Mejorada

```
┌─────────────────────────────────────────────────────────────────┐
│ Frontend (Vue)                                                  │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ IcebergEditor.vue                                          │ │
│ │ - Mostrar entrada con música configurada                  │ │
│ │ - Botón: "Generar video con música"                       │ │
│ │ - Botón: "Compartir enlace de editor"                     │ │
│ └────────────────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────────────┘
                     │ POST /video
                     │ {
                     │   iceberg_title,
                     │   level_number,
                     │   level_name,
                     │   entry_title,        ← NUEVO: para zoom
                     │   description,
                     │   music_url,          ← NUEVO
                     │   media,
                     │   show_url: false     ← NUEVO
                     │ }
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Backend (FastAPI)                                               │
│                                                                 │
│  VideoRouter.py                                                 │
│  ├─> VideoService.generate(req)                                │
│      ├─> NarrationBuilder.build(req)  ──► Narración de texto   │
│      │                                                          │
│      ├─> TTSEngine.synth(text)        ──► Audio narración      │
│      │                                      (si no hay música)  │
│      │                                                          │
│      ├─> MediaFetcher.fetch(req.media)──► Descargar media      │
│      │                                                          │
│      ├─> SceneBuilder.build_scenes()  ──► Escenas con texto    │
│      │                                                          │
│      └─> VideoRenderer.render(                                 │
│          scenes,                                               │
│          audio,                                                │
│          title,              ← entry_title para zoom intro    │
│          music_url,          ← música para outro/background   │
│          show_url            ← mostrar URL o no                │
│      ) ──► MP4 final                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                     │ FileResponse(mp4)
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Cliente                                                         │
│ ├─ Descarga MP4                                                │
│ └─ Reproduce:                                                  │
│    INTRO (2.2s): Zoom a "incidente del 8080"                   │
│    BODY (N s):   Escenas con narración + música                │
│    OUTRO (2.0s): "Crea el tuyo" + URL (o vacío)                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Cambios en Entidades

### Antes
```python
# level.py
class Level(SQLModel, table=True):
    id: str
    iceberg_id: str
    numero: int
    nombre: str | None
    orden: int
```

### Después
```python
# level.py
class Level(SQLModel, table=True):
    __tablename__ = "levels"
    
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    iceberg_id: str = Field(foreign_key="icebergs.id", ondelete="CASCADE", index=True)
    numero: int
    nombre: str | None = Field(default=None)
    orden: int = Field(default=0)
    music_url: str | None = Field(default=None)  # ← NUEVO: URL de música
    
    iceberg: "Iceberg" = Relationship(back_populates="levels")
    entries: list["Entry"] = Relationship(back_populates="level", cascade_delete=True)
```

---

## 3. Cambios en DTOs

### VideoRequest
```python
# video_dto.py
class VideoRequest(BaseModel):
    iceberg_title: str = Field(max_length=120)
    entry_title: str = Field(max_length=160)  # ← NUEVO: para zoom intro
    level_number: int
    level_name: str | None = None
    description: str = Field(max_length=DESCRIPCION_MAX)
    media: list[MediaRef] = []
    music_url: str | None = None              # ← NUEVO: URL de música
    show_url: bool = Field(default=False)    # ← NUEVO: mostrar URL en outro
```

### LevelRead (para retornar en GET)
```python
# level_dto.py
class LevelRead(BaseModel):
    id: str
    numero: int
    nombre: str | None
    orden: int
    music_url: str | None                    # ← NUEVO
    entries: list[EntryRead] = []
```

---

## 4. Ejemplo: VideoRenderer.render() Mejorado

```python
# video_renderer.py

class VideoRenderer:
    def render(
        self,
        scenes: list[Any],
        *,
        audio: str | None = None,
        title: str = "",
        entry_title: str = "",        # ← NUEVO
        music_url: str | None = None, # ← NUEVO
        show_url: bool = True,        # ← NUEVO
        workdir: str | None = None,
    ) -> str:
        """Renderiza video con intro zoomeable y outro sin localhost."""
        import numpy as np
        from moviepy import AudioFileClip, ImageClip, concatenate_videoclips, vfx

        size = frame_size(self._settings)
        out_dir = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="iceberg_video_"))
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "iceberg.mp4"

        # ✨ INTRO con zoom al entry_title
        intro = self._card_with_zoom(
            size,
            headline="ICEBERG",
            subtitle=entry_title,  # ← Hace zoom a esto
            duration=INTRO_SECONDS,
            image_clip=ImageClip,
            np=np
        ).with_effects([vfx.FadeIn(0.5), vfx.FadeOut(0.4)])

        # ✨ OUTRO sin localhost
        outro_text = ""
        if show_url and self._settings.public_base_url:
            url = self._settings.public_base_url.removeprefix("https://").removeprefix("http://")
            # No mostrar localhost
            if not url.startswith("localhost"):
                outro_text = url
            else:
                outro_text = ""  # Vacío si es localhost

        outro = self._card(
            size, "Crea el tuyo", outro_text, OUTRO_SECONDS, ImageClip, np
        ).with_effects([vfx.FadeIn(0.4), vfx.FadeOut(0.5)])

        body = concatenate_videoclips(scenes) if scenes else None
        parts = [intro] + ([body] if body is not None else []) + [outro]
        final = concatenate_videoclips(parts)

        # ✨ Usar música si está disponible
        if music_url:
            try:
                full_audio_path = self._prepare_music_audio(
                    music_url,
                    final.duration,
                    out_dir
                )
                final = final.with_audio(AudioFileClip(full_audio_path))
            except Exception as e:
                # Fallback a TTS si música falla
                if audio:
                    full_audio = out_dir / "full_audio.wav"
                    full_audio_path = self._build_full_audio(audio, full_audio)
                    final = final.with_audio(AudioFileClip(full_audio_path))
        elif audio:
            # Usar TTS si no hay música
            full_audio = out_dir / "full_audio.wav"
            full_audio_path = self._build_full_audio(audio, full_audio)
            final = final.with_audio(AudioFileClip(full_audio_path))

        final.write_videofile(
            str(out_path),
            fps=self._settings.video_fps,
            codec="libx264",
            audio_codec="aac",
            preset="veryfast",
            logger=None,
        )
        final.close()
        return str(out_path)

    def _card_with_zoom(self, size, headline: str, subtitle: str, duration: float, image_clip, np):
        """Intro con zoom hacia el subtitle."""
        from moviepy import vfx
        
        w, h = size
        bg = make_background(size)
        card = ImageClip(bg).set_duration(duration)
        
        # ✨ Agregar texto con zoom
        # Idea: usar moviepy's resizing/position changes
        # O: renderizar múltiples frames con moviepy compositor
        
        # Aproximación: hacer composición frame-a-frame
        # (Esto es complejo, mejor usar bibliotecas de composición)
        
        # TODO: Implementar con moviepy's `fx_resize` o similar
        # Por ahora, retornar card estándar
        return card

    def _prepare_music_audio(self, music_url: str, target_duration: float, work_dir: Path) -> str:
        """Prepara audio de música (descarga si es URL, ajusta duración)."""
        from moviepy import AudioFileClip
        import requests
        
        # Si es URL, descargar
        if music_url.startswith("http"):
            music_path = work_dir / "music.mp3"
            response = requests.get(music_url)
            music_path.write_bytes(response.content)
        else:
            music_path = Path(music_url)
        
        # Cargar y ajustar duración
        with AudioFileClip(str(music_path)) as aud:
            # Si es más larga que el video, cortar
            if aud.duration > target_duration:
                aud = aud.subclipped(0, target_duration)
            # Si es más corta, repetir (loop)
            elif aud.duration < target_duration:
                # Loop: repetir la música
                from moviepy import concatenate_audioclips
                num_loops = int(target_duration / aud.duration) + 1
                looped = concatenate_audioclips([aud] * num_loops)
                looped = looped.subclipped(0, target_duration)
                final_path = work_dir / "music_looped.wav"
                looped.write_audiofile(str(final_path), logger=None)
                return str(final_path)
        
        return str(music_path)
```

---

## 5. Editor Compartido - Flujo de Tokens

```
┌──────────────────────────────┐
│ IcebergEditor.vue            │
│ Botón: Compartir             │
└────────────┬─────────────────┘
             │ POST /icebergs/{id}/get-edit-token
             ▼
┌────────────────────────────────────────┐
│ EditorRouter                           │
│ @router.post("/icebergs/{id}/get-edit-token") │
│ → EditorTokenService.create_token()  │
│ → Devuelve { token, expires_at }    │
└────────────┬─────────────────────────┘
             │ Frontend copia URL:
             │ https://app.com/i/{slug}/edit?token=xyz123
             ▼
        Usuario envía enlace
             │
             ▼
┌────────────────────────────────────────┐
│ EditorView.vue (nueva ruta)            │
│ - Valida token en backend              │
│ - Carga IcebergEditor.vue              │
│ - Usa token en headers para auth       │
└────────────┬─────────────────────────┘
             │ GET /icebergs/{slug}?token={token}
             │ PATCH /icebergs/{id} (con header token)
             ▼
┌────────────────────────────────────────┐
│ IcebergRouter (middleware)             │
│ - Valida token OR ownership            │
│ - Devuelve 403 si inválido             │
└────────────────────────────────────────┘
```

---

## 6. EditorTokenService

```python
# editor_token_service.py
from datetime import datetime, timedelta, UTC
import secrets
import hashlib
from sqlmodel import Session, select

from iceberg_entities import Iceberg
from iceberg_accesodatos.config import Settings

class EditorToken:
    """Representa un token de edición."""
    iceberg_id: str
    token_hash: str  # Hash del token (no almacenar plain)
    expires_at: datetime
    created_at: datetime


class EditorTokenService:
    def __init__(self, settings: Settings, session: Session):
        self._settings = settings
        self._session = session
    
    def create_token(self, iceberg_id: str) -> dict:
        """Crea un nuevo token de edición."""
        # Generar token seguro
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        expires_at = datetime.now(UTC) + timedelta(
            days=self._settings.edit_token_expiry_days or 30
        )
        
        # Guardar en BD (o Redis para efímeros)
        et = EditorToken(
            iceberg_id=iceberg_id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=datetime.now(UTC)
        )
        # self._session.add(et)
        # self._session.commit()
        
        return {
            "token": token,  # ← Devolver plain al usuario UNA VEZ
            "expires_at": expires_at.isoformat(),
            "url": f"{self._settings.public_base_url}/i/{iceberg_id}/edit?token={token}"
        }
    
    def validate_token(self, iceberg_id: str, token: str) -> bool:
        """Valida si el token es válido para este iceberg."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Buscar en BD
        # stmt = select(EditorToken).where(
        #     EditorToken.iceberg_id == iceberg_id,
        #     EditorToken.token_hash == token_hash,
        #     EditorToken.expires_at > datetime.now(UTC)
        # )
        # result = self._session.exec(stmt).first()
        # return result is not None
        
        return True  # Placeholder
```

---

## 7. Middleware de Validación

```python
# main.py
from fastapi import Request, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware

class EditTokenMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Si es ruta de edición, validar token
        if request.url.path.startswith("/icebergs/") and request.method in ["PATCH", "POST", "DELETE"]:
            token = request.query_params.get("token")
            if not token:
                # Comprobar si está logueado (por ahora, ignorar)
                pass
            else:
                # Validar token
                iceberg_id = request.url.path.split("/")[2]
                if not validate_token(iceberg_id, token):
                    raise HTTPException(status_code=403, detail="Invalid edit token")
        
        return await call_next(request)

app.add_middleware(EditTokenMiddleware)
```

---

## 8. Frontend: IcebergEditor mejorado

```vue
<!-- IcebergEditor.vue - Fragment -->

<script setup>
// ... imports ...

const musicaDefault = "https://cdn.ejemplo.com/undertale_ruins.mp3";

async function compartirEnlaceEditor() {
  try {
    const resp = await api.generarTokenEdicion(iceberg.value.id);
    await navigator.clipboard.writeText(resp.url);
    avisar("🔗 Enlace de editor copiado");
  } catch (e) {
    avisar(`Error: ${e.message}`);
  }
}

async function cargarMusica(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  
  // Subir música a nivel actual
  try {
    const formData = new FormData();
    formData.append("file", file);
    const resp = await api.subirMusica(seleccion.value.nivel.id, formData);
    await cargar();
    avisar("🎵 Música subida");
  } catch (e) {
    avisar(`Error: ${e.message}`);
  }
}

async function usarMusicaDefault() {
  await api.editarNivel(seleccion.value.nivel.id, {
    music_url: musicaDefault
  });
  await cargar();
  avisar("🎵 Usando UNDERTALE Ruins");
}

async function generarVideoNarrado() {
  const { entry, nivel } = seleccion.value;
  generando.value = true;
  try {
    const blob = await generarVideo({
      iceberg_title: iceberg.value.titulo,
      entry_title: entry.titulo,           // ← NUEVO
      level_number: nivel.numero,
      level_name: nivel.nombre,
      description: entry.descripcion,
      media: entry.media.map((m) => ({ url: m.url, tipo: m.tipo })),
      music_url: nivel.music_url,          // ← NUEVO
      show_url: false                      // ← NUEVO
    });
    // Descargar...
  } finally {
    generando.value = false;
  }
}
</script>

<template>
  <!-- ... template existente ... -->
  
  <!-- Sección Música (en panel de nivel) -->
  <section v-if="seleccion" class="p-4 bg-slate-900/50 rounded">
    <h3 class="text-lg mb-2">🎵 Música del Nivel</h3>
    
    <div class="flex gap-2">
      <button
        @click="$refs.musicInput.click()"
        class="px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded flex items-center gap-2"
      >
        <UploadCloud size="16" /> Subir Música
      </button>
      <input
        ref="musicInput"
        type="file"
        accept="audio/*"
        @change="cargarMusica"
        hidden
      />
      
      <button
        @click="usarMusicaDefault"
        class="px-3 py-2 bg-purple-600 hover:bg-purple-700 rounded"
      >
        Usar UNDERTALE Ruins
      </button>
    </div>
    
    <p v-if="seleccion.nivel.music_url" class="mt-2 text-sm text-slate-300">
      Música configurada: {{ seleccion.nivel.music_url }}
    </p>
  </section>
  
  <!-- Botón Compartir Editor -->
  <button
    @click="compartirEnlaceEditor"
    class="mt-4 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 rounded flex items-center gap-2"
  >
    <Share2 size="16" /> Compartir Enlace de Editor
  </button>
</template>
```

---

## 9. Checklist de Implementación

### BD & Migrations
- [ ] Agregar columna `music_url` a tabla `levels`
- [ ] Agregar tabla `edit_tokens` (o usar Redis)
- [ ] Ejecutar migraciones

### Backend DTOs
- [ ] Actualizar `VideoRequest`
- [ ] Actualizar `LevelRead`
- [ ] Agregar `VideoResponse` con `show_url`

### Backend Services
- [ ] `EditorTokenService` completo
- [ ] `VideoService.generate()` mejorado para pasar `music_url`
- [ ] `VideoRenderer` con métodos de zoom y música

### Backend Routers
- [ ] `level_router.py`: PATCH con `music_url`
- [ ] `editor_router.py`: POST get-token, GET validate
- [ ] Middleware de validación de tokens

### Frontend
- [ ] `EditorView.vue` (nueva ruta)
- [ ] Botones en `IcebergEditor.vue` para música
- [ ] Botón "Compartir enlace de editor"
- [ ] Actualizar `api.js` con nuevos endpoints

### Testing
- [ ] Video con zoom funciona
- [ ] Música se reproduce
- [ ] Token de editor válido durante 30 días
- [ ] URL sin localhost en outro
- [ ] Compatibilidad con navegadores
