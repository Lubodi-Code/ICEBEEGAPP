# 🎬 Prompt: Nuevas Características para Iceberg Video Generator

## Resumen de Cambios Solicitados

### 1. 🔍 Animación de Zoom Inicial
**Objetivo**: Hacer zoom dramático al título de la entrada al iniciar el video.

**Comportamiento**:
- La intro debe mostrar el título de entrada (ej: "incidente del 8080") con efecto zoom-in
- Inicia pequeño/lejano y crece hasta llenar pantalla
- Luego continúa como está actualmente
- Duración: 2.2 segundos (INTRO_SECONDS)

**Cambios técnicos**:
- `VideoRenderer._card()`: Añadir animación de zoom con moviepy
- `SceneBuilder`: Crear intro scene con el entry_title como protagonista

---

### 2. 🎵 Música Configurable por Nivel
**Objetivo**: Permitir añadir música personalizada a cada nivel (default: UNDERTALE Ruins).

**Comportamiento**:
- Cada nivel puede tener una URL de música asociada
- Si no hay música configurada, usa default: UNDERTALE Ruins
- La música se toca durante todo el video (en lugar de narración TTS o junto a ella)
- Opción en editor: cargar archivo de música o usar default

**Cambios técnicos**:

#### Backend (Python)
1. **Entity Level** (`packages/entities/src/iceberg_entities/level.py`):
   ```python
   class Level(SQLModel, table=True):
       # ... campos existentes ...
       music_url: str | None = Field(default=None)  # Nueva columna
   ```

2. **DTO VideoRequest** (`packages/dto/src/iceberg_dto/video_dto.py`):
   ```python
   class VideoRequest(BaseModel):
       # ... campos existentes ...
       music_url: str | None = None  # URL de música para este video
   ```

3. **DTO LevelRead** (`packages/dto/src/iceberg_dto/level_dto.py`):
   - Agregar campo `music_url` para retornar en GET /icebergs/{id}

4. **Level Router** (`packages/api/src/iceberg_api/routers/level_router.py`):
   - Permitir PATCH `/levels/{id}` con `music_url`

5. **VideoService** (`packages/negocio/src/iceberg_negocio/video/video_service.py`):
   - Si `req.music_url` existe, usar esa música
   - Si no existe, usar música default (descargar de S3 o ruta local)
   - Pasar `music_url` a `renderer.render()`

6. **VideoRenderer** (`packages/negocio/src/iceberg_negocio/video/video_renderer.py`):
   - Si `music_url` está disponible, usarla en lugar de generar silencio + narración
   - Mantener TTS como respaldo

#### Frontend (Vue)
- En `IcebergEditor.vue`: 
  - Botón "Subir música" en la sección de nivel
  - Selector para usar "Música default (UNDERTALE Ruins)"
  - Preview de audio
  - Pasar `music_url` al generar video

---

### 3. 🔗 Enlace Compartido para Editar
**Objetivo**: Generar un enlace que permite a otros editar el iceberg sin tener cuenta.

**Comportamiento**:
- Botón "Compartir enlace de editor" en IcebergEditor
- Genera token temporal (o permanente, según necesidad)
- Enlace: `https://miapp.com/i/{slug}/edit?token=abc123`
- Acceso de lectura/escritura completo con solo el token

**Cambios técnicos**:

#### Backend
1. **Entity Iceberg** (opcional):
   - Agregar campo `edit_token: str | None` para tokens persistentes
   - O usar tokens efímeros en Redis (más seguro)

2. **ShareService** (`packages/negocio/src/iceberg_negocio/share_service.py`):
   ```python
   def build_editor_url(self, slug: str, token: str) -> str:
       return f"{self._base}/i/{slug}/edit?token={token}"
   ```

3. **Nuevo Router: `editor_router.py`**:
   - `GET /i/{slug}/edit?token={token}` → valida y retorna el editor
   - `POST /icebergs/{slug}/get-edit-token` → genera nuevo token
   - Endpoints existentes responden con `403` si token inválido

#### Frontend
- Nueva vista: `EditorView.vue` (renderiza IcebergEditor con token)
- En IcebergEditor: botón "Copiar enlace de editor" que copia el URL con token
- Validar token al cargar (o hacerlo en backend)

---

### 4. 🌐 Remover "localhost" del Outro
**Objetivo**: El outro no debe mostrar "localhost:8000" cuando se comparte.

**Comportamiento actual**:
```python
# En VideoRenderer.render()
outro_text = self._settings.public_base_url.removeprefix("https://").removeprefix("http://")
# Resultado: "localhost:8000" o "app.example.com"
```

**Cambios**:
```python
def render(self, scenes, audio=None, title="", workdir=None, show_url=True):
    # ...
    outro_text = ""
    if show_url and self._settings.public_base_url:
        url = self._settings.public_base_url.removeprefix("https://").removeprefix("http://")
        # ✅ Remover localhost y puerto
        if not url.startswith("localhost"):
            outro_text = url
        else:
            outro_text = "iceberg.app"  # Fallback
    # ...
```

**Alternativa más segura**:
- Parámetro en VideoRequest: `show_url: bool = False`
- Dejar que el frontend decida si mostrar URL o no

---

## 📋 Plan de Implementación Paso a Paso

### Fase 1: Backend - Base de datos y DTOs
1. Ejecutar migración: añadir `music_url` a tabla `levels`
   ```bash
   # Si usas Alembic
   alembic revision --autogenerate -m "Add music_url to levels"
   alembic upgrade head
   ```
2. Actualizar `Level` entity
3. Actualizar DTOs: `VideoRequest`, `LevelRead`
4. Actualizar Level Router para aceptar `music_url`

### Fase 2: Backend - Lógica de Video
1. Modificar `VideoService.generate()` para pasar `music_url`
2. Modificar `VideoRenderer`:
   - `render()` para aceptar `music_url`
   - `_build_full_audio()` para usar música en lugar de generar silencio
3. Agregar soporte para descargar/usar música default (UNDERTALE Ruins)

### Fase 3: Backend - Editor Compartido
1. Crear tabla `edit_tokens` (o usar Redis)
2. Crear `EditorTokenService`
3. Crear `editor_router.py` con endpoints de validación
4. Middleware que valida tokens en endpoints de edición

### Fase 4: Frontend - UI para Música
1. Agregar campo música en `IcebergEditor.vue`
2. Botón "Subir música" y "Usar default"
3. Preview de audio

### Fase 5: Frontend - Editor Compartido
1. Crear `EditorView.vue`
2. Botón "Copiar enlace de editor" en IcebergEditor
3. Lógica de autenticación con token

### Fase 6: Frontend - Video con Zoom
1. Pasar `entry_title` a `generarVideo()`
2. Backend renderiza intro con zoom al título

### Fase 7: Testing y Ajustes
1. Probar cada feature
2. Ajustar timings de animaciones
3. Testing de compartir editor

---

## 🎯 Requisitos de Configuración

### Variables de Entorno Nuevas
```env
# .env (backend)
UNDERTALE_RUINS_URL=https://cdn.ejemplo.com/undertale-ruins.mp3
# O ruta local:
UNDERTALE_RUINS_PATH=/app/media_local/undertale_ruins.mp3

# Tokens
EDIT_TOKEN_EXPIRY_DAYS=30  # Duración de tokens de edición
EDIT_TOKEN_LENGTH=32  # Longitud del token
```

### Archivos a Crear/Modificar

**Crear**:
- `packages/negocio/src/iceberg_negocio/editor_token_service.py`
- `packages/api/src/iceberg_api/routers/editor_router.py`
- `cliente/src/components/EditorView.vue`

**Modificar**:
- `packages/entities/src/iceberg_entities/level.py` ✏️
- `packages/dto/src/iceberg_dto/video_dto.py` ✏️
- `packages/dto/src/iceberg_dto/level_dto.py` ✏️
- `packages/negocio/src/iceberg_negocio/video/video_service.py` ✏️
- `packages/negocio/src/iceberg_negocio/video/video_renderer.py` ✏️
- `packages/negocio/src/iceberg_negocio/share_service.py` ✏️
- `packages/api/src/iceberg_api/routers/level_router.py` ✏️
- `packages/api/src/iceberg_api/main.py` ✏️
- `cliente/src/components/IcebergEditor.vue` ✏️
- `cliente/src/api.js` ✏️

---

## 🔊 Archivo de Música Default

**UNDERTALE Ruins**:
- Ubicación sugerida: `media_local/undertale_ruins.mp3`
- Adjuntado en la conversación
- Cargar al inicio de la app o bajo demanda

---

## 💡 Notas Importantes

1. **Seguridad del Editor Compartido**: 
   - Usar tokens con hash seguro (no plain text)
   - Expiration date
   - Rate limiting para evitar brute force

2. **Música y TTS**:
   - ¿Música reemplaza narración o coexisten?
   - Sugerencia: música + TTS con volumen ajustado

3. **Zoom Animation**:
   - Biblioteca: moviepy tiene `vfx` module
   - O renderizar con matplotlib + pillow

4. **Migration de BD**:
   - Si no usas Alembic, ejecutar SQL manualmente:
     ```sql
     ALTER TABLE levels ADD COLUMN music_url VARCHAR NULL;
     ALTER TABLE icebergs ADD COLUMN edit_token VARCHAR NULL UNIQUE;
     ```

---

## ✅ Criterios de Aceptación

- [ ] Video inicia con zoom al título de entrada
- [ ] Cada nivel puede tener música configurada
- [ ] Default: UNDERTALE Ruins si no hay música
- [ ] Botón "Compartir enlace de editor" copia URL con token
- [ ] Token permite edición sin login
- [ ] Outro no muestra "localhost" en versión pública
- [ ] All features tested end-to-end
- [ ] No hay errores en consola frontend/backend

---

## 🚀 Próximos Pasos

1. Revisar y confirmar cambios propuestos
2. Decidir si música reemplaza o coexiste con TTS
3. Decidir si tokens son efímeros o persistentes
4. Comenzar con Fase 1 (BD + DTOs)
