# 🚀 QuickStart - Comenzar Implementación

## 📋 Paso 0: Lee Primero Esto

> **Si solo tienes 5 minutos**: Lee este archivo y `RESUMEN_EJECUTIVO.md`  
> **Si tienes 15 minutos**: Lee todos los archivos en orden  
> **Si vas a programar**: Usa `ARQUITECTURA_Y_EJEMPLOS.md` como referencia

---

## 📂 Documentos Disponibles

| Documento | Tiempo | Contenido |
|-----------|--------|----------|
| `PROMPT_NUEVAS_FEATURES.md` | 10 min | Especificación completa de cada feature |
| `ARQUITECTURA_Y_EJEMPLOS.md` | 15 min | Diagramas y código de ejemplo |
| `RESUMEN_EJECUTIVO.md` | 5 min | Plan y checklist de implementación |
| **ESTE ARCHIVO** | 5 min | Guía rápida de inicio |

---

## 🎯 Las 4 Features en 30 Segundos

### 1. 🔍 Zoom en Intro (Fácil)
```
Video comienza con zoom al nombre de entrada
"incidente del 8080" crece desde pequeño a grande
→ Cambio en VideoRenderer._card_with_zoom()
```

### 2. 🎵 Música por Nivel (Medio)
```
Cada nivel tiene música asociada
Default: UNDERTALE Ruins
→ Nuevo campo music_url en Level
→ Usar música en lugar de TTS
```

### 3. 🔗 Compartir Editor (Complejo)
```
Generar token que permite editar sin login
https://app.com/i/{slug}/edit?token=xyz
→ EditorTokenService + EditorRouter
```

### 4. 🌐 Sin Localhost (Trivial)
```
Outro no muestra "localhost:8000"
→ if not url.startswith("localhost"): ...
```

---

## 🔧 Setup Rápido

### 1. Instalar Dependencias
```bash
# Backend
cd packages/api
pip install -e ".[dev]"

# Frontend
cd ../../cliente
npm install
```

### 2. Copiar Música Default
```bash
mkdir -p media_local/default_music
cp "005. Ruins (UNDERTALE Soundtrack) - Toby Fox.mp3" \
   media_local/default_music/undertale_ruins.mp3
```

### 3. Variables de Entorno
```bash
# .env
EDIT_TOKEN_EXPIRY_DAYS=30
EDIT_TOKEN_LENGTH=32
```

### 4. Iniciar Desarrollo
```bash
# Terminal 1: Backend
cd packages/api
uvicorn iceberg_api.main:app --reload --port 8000

# Terminal 2: Frontend
cd cliente
npm run dev
```

---

## 📊 Roadmap Visual

```
Semana 1                Semana 2              Semana 3
├─ Remover localhost   ├─ Zoom animation     ├─ Editor tokens
├─ ✅ 1 hora           ├─ ✅ 2 horas        ├─ ✅ 4 horas
│                      │                    │
├─ Música por nivel    ├─ Testing           ├─ Pulir
├─ ✅ 3 horas          ├─ ✅ 2 horas        ├─ ✅ 2 horas
│                      │                    │
└─ Preparar BD         └─ Deployment        └─ Release
  ✅ 1 hora              ✅ 1 hora            ✅ 0.5 horas
```

---

## 🎬 Feature por Feature - Paso a Paso

### Feature 1️⃣: Remover Localhost (1 hora)

#### Cambio
Archivo: `packages/negocio/src/iceberg_negocio/video/video_renderer.py`
```python
# Línea ~75, en render()
- outro_text = self._settings.public_base_url.removeprefix("https://").removeprefix("http://")
+ url = self._settings.public_base_url.removeprefix("https://").removeprefix("http://")
+ outro_text = url if not url.startswith("localhost") else ""
```

#### Prueba
```bash
# Generar video en dev (localhost:8000)
# Verificar que outro esté vacío
```

---

### Feature 2️⃣: Zoom en Intro (2 horas)

#### Cambios
1. **VideoRequest DTO**: Agregar `entry_title`
```python
# packages/dto/src/iceberg_dto/video_dto.py
class VideoRequest(BaseModel):
    # ... campos existentes ...
    entry_title: str = Field(max_length=160)  # ← NUEVO
```

2. **VideoRenderer**: Pasar entry_title y crear método zoom
```python
# packages/negocio/src/iceberg_negocio/video/video_renderer.py
def render(self, scenes, *, ..., entry_title="", ...):
    intro = self._card_with_zoom(entry_title, ...)
```

3. **Frontend**: Pasar entry_title al generar
```js
// cliente/src/components/IcebergEditor.vue
const blob = await generarVideo({
    // ... campos existentes ...
    entry_title: entry.titulo,  // ← NUEVO
});
```

#### Prueba
```bash
# Generar video y verificar que comience con zoom al título
```

---

### Feature 3️⃣: Música por Nivel (3 horas)

#### Cambios (Orden importante)
1. **BD**: Migración
```sql
ALTER TABLE levels ADD COLUMN music_url VARCHAR NULL;
```

2. **Level Entity**
```python
# packages/entities/src/iceberg_entities/level.py
class Level(SQLModel, table=True):
    # ... campos existentes ...
    music_url: str | None = Field(default=None)  # ← NUEVO
```

3. **DTOs**
```python
# packages/dto/src/iceberg_dto/video_dto.py
class VideoRequest(BaseModel):
    # ... campos existentes ...
    music_url: str | None = None  # ← NUEVO

# packages/dto/src/iceberg_dto/level_dto.py
class LevelRead(BaseModel):
    # ... campos existentes ...
    music_url: str | None = None  # ← NUEVO
```

4. **Level Router** - Permitir actualizar música
```python
# packages/api/src/iceberg_api/routers/level_router.py
# El PATCH existente ya funciona si Level tiene music_url
```

5. **VideoService** - Pasar música
```python
# packages/negocio/src/iceberg_negocio/video/video_service.py
mp4 = self.renderer.render(
    scenes,
    audio=audio,
    title=req.iceberg_title,
    entry_title=req.entry_title,
    music_url=req.music_url,  # ← NUEVO
    workdir=str(workdir),
)
```

6. **VideoRenderer** - Usar música
```python
# packages/negocio/src/iceberg_negocio/video/video_renderer.py
def render(self, ..., music_url=None, ...):
    if music_url:
        full_audio_path = self._prepare_music_audio(music_url, ...)
        final = final.with_audio(AudioFileClip(full_audio_path))
    elif audio:
        # TTS fallback
        ...

def _prepare_music_audio(self, music_url, target_duration, work_dir):
    # Descargar si es URL, ajustar duración, repetir si es necesario
    ...
```

7. **Frontend**: UI para música
```vue
<!-- cliente/src/components/IcebergEditor.vue -->
<button @click="usarMusicaDefault">🎵 UNDERTALE Ruins</button>
<button @click="$refs.musicInput.click()">Subir Música</button>
```

#### Prueba
```bash
# 1. Crear nivel
# 2. Asignar música UNDERTALE
# 3. Generar video
# 4. Verificar que video tenga audio de música
```

---

### Feature 4️⃣: Compartir Editor (4 horas)

#### Cambios Complejos - Ver `ARQUITECTURA_Y_EJEMPLOS.md` para detalles

Resumen:
1. Crear `EditorTokenService` (generar + validar tokens)
2. Crear `EditorRouter` con endpoint `/icebergs/{id}/get-edit-token`
3. Crear `EditorView.vue` que acepta token
4. Agregar middleware de validación
5. Botón en IcebergEditor: "Compartir enlace de editor"

#### Prueba
```bash
# 1. Generar token desde UI
# 2. Copiar URL con token
# 3. Abrir incógnito y acceder a URL
# 4. Editar iceberg sin login
# 5. Verificar que token expira después de 30 días
```

---

## 🐛 Debugging Tips

### Backend no genera video
```bash
# Verificar que movie se instaló correctamente
python -c "import moviepy; print(moviepy.__version__)"

# Ver logs completos
# En VideoService, quitar logger=None para ver progreso
```

### Música no suena
```bash
# Verificar que el archivo existe
ls -la media_local/default_music/

# Probar que moviepy puede leer archivo
python -c "from moviepy import AudioFileClip; AudioFileClip('ruta/a/archivo.mp3')"
```

### Token no funciona
```bash
# Verificar que el hash es correcto
# Revisar que no ha expirado

# Debug: en EditorTokenService, agregar logs
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Token hash: {token_hash}")
```

### Frontend no ve cambios
```bash
# Limpiar caché de npm
npm cache clean --force

# Reiniciar servidor Vite
pkill node
npm run dev
```

---

## 📱 Testing Rápido

### 1. Crear Iceberg de Prueba
```bash
# API
curl -X POST http://localhost:8000/icebergs \
  -H "Content-Type: application/json" \
  -d '{"titulo": "Test Iceberg"}'

# Copiar el slug retornado
```

### 2. Crear Nivel con Música
```bash
curl -X POST http://localhost:8000/icebergs/{iceberg_id}/levels \
  -H "Content-Type: application/json" \
  -d '{
    "numero": 1,
    "nombre": "Nivel Test",
    "orden": 0,
    "music_url": "file://media_local/default_music/undertale_ruins.mp3"
  }'
```

### 3. Generar Video
```bash
curl -X POST http://localhost:8000/video \
  -H "Content-Type: application/json" \
  -d '{
    "iceberg_title": "Test",
    "entry_title": "incidente del 8080",
    "level_number": 1,
    "level_name": "Nivel Test",
    "description": "Descripción test",
    "media": [],
    "music_url": "file://media_local/default_music/undertale_ruins.mp3",
    "show_url": false
  }' > test.mp4
```

---

## 📚 Archivos que NO Modificaremos

```
✓ No tocar conftest.py
✓ No tocar test_smoke.py
✓ No tocar Dockerfile
✓ No tocar pyproject.toml (principales)
✓ No tocar package.json (npm scripts)
✓ No tocar ruff.toml
```

---

## ✅ Checklist Antes de Empezar

- [ ] He leído `RESUMEN_EJECUTIVO.md`
- [ ] He leído `PROMPT_NUEVAS_FEATURES.md`
- [ ] He copiado `undertale_ruins.mp3` a `media_local/default_music/`
- [ ] Backend corre: `pytest` ✅
- [ ] Frontend corre: `npm run dev` ✅
- [ ] Puedo generar un video básico
- [ ] Git branch está limpio: `git status`

---

## 🎯 Objetivo Final

**Video esperado después de implementar TODO**:

```
INTRO (2.2s):
  - Fondo iceberg degradado
  - Zoom de "incidente del 8080" que crece desde pequeño
  - UNDERTALE Ruins sonando de fondo
  - Fade in + fade out

BODY (10-30s):
  - Escenas con media (imágenes/videos)
  - Narración TTS (o solo música si es nivel con música)
  - Música de fondo

OUTRO (2s):
  - "Crea el tuyo"
  - URL vacía (si es localhost) o URL pública
  - Fade in + fade out
```

---

## 💬 Preguntas Frecuentes

**P: ¿Por dónde empiezo?**  
R: Por Feature 1 (remover localhost). Es la más fácil y valida el setup.

**P: ¿Necesito migración de BD?**  
R: Sí, para Feature 3 (música). SQLAlchemy la genera automáticamente si usas Alembic.

**P: ¿Puedo hacer features en paralelo?**  
R: Sí, pero recomiendo secuencial para evitar conflictos en IcebergEditor.vue.

**P: ¿Cuándo se puede mergear a main?**  
R: Cuando todas las features estén, testing completo y 0 breaking changes.

---

## 🚀 ¡Ahora Sí, a Programar!

```bash
# 1. Crear rama
git checkout -b features/video-enhancements

# 2. Empezar con Feature 1
# ... modificar video_renderer.py ...

# 3. Probar
pytest -v
npm run dev

# 4. Commit
git add .
git commit -m "feat: remove localhost from video outro"

# 5. Repetir con Features 2, 3, 4
```

**Tiempo estimado: 10-14 horas**  
**Complejidad: Media-Alta**  
**Valor agregado: Alto**

---

**¿Preguntas? Consulta `ARQUITECTURA_Y_EJEMPLOS.md` para detalles técnicos.**

¡A por ello! 🎬🎵🔗
