# 📊 Resumen Ejecutivo - Nuevas Features

## 🎯 Objetivos Principales

| Feature | Impacto | Complejidad | Prioridad |
|---------|--------|------------|-----------|
| 🔍 Zoom en Intro | Alto (UX) | Media | 🔴 Alta |
| 🎵 Música por Nivel | Alto (Content) | Media | 🔴 Alta |
| 🔗 Compartir Editor | Medio (Collab) | Alta | 🟡 Media |
| 🌐 Remover localhost | Bajo (Polish) | Baja | 🟢 Baja |

---

## 📈 Impacto en Arquitectura

### Cambios Mínimos (0-2 horas)
```
✓ Remover localhost del outro
✓ Pasar entry_title a video
→ Cambios en VideoRenderer.render()
```

### Cambios Moderados (2-4 horas)
```
✓ Agregar music_url a Level entity
✓ Actualizar DTOs
✓ Lógica de música en VideoService
→ Cambios en video_service.py, video_dto.py, level_router.py
```

### Cambios Complejos (4-8 horas)
```
✓ Zoom animation en intro
✓ Editor token system
✓ Middleware de validación
→ Cambios en video_renderer.py, nuevos servicios/routers
```

---

## 🔧 Orden de Implementación Recomendado

### Paso 1️⃣ (1-2 horas): Remover localhost
```python
# VideoRenderer.render()
if not url.startswith("localhost"):
    outro_text = url
else:
    outro_text = ""
```
**Beneficio**: Validación rápida del cambio en arquitectura
**Prueba**: Generar video en localhost, verificar que outro está vacío

### Paso 2️⃣ (2-3 horas): Agregar Zoom a Intro
```python
# VideoRenderer._card_with_zoom()
# Usar moviepy.vfx para resize progresivo
```
**Beneficio**: Mejora visual inmediata
**Prueba**: Video inicia con zoom al nombre de entrada

### Paso 3️⃣ (3-4 horas): Música por Nivel
```python
# 1. Migración: ALTER TABLE levels ADD COLUMN music_url
# 2. Entity Level + DTOs
# 3. VideoService + VideoRenderer
# 4. UI en IcebergEditor
```
**Beneficio**: Más control sobre contenido del video
**Prueba**: Generar video con música UNDERTALE

### Paso 4️⃣ (4-6 horas): Editor Compartido
```python
# 1. EditorTokenService
# 2. EditorRouter + middleware
# 3. EditorView.vue
# 4. Auth validation
```
**Beneficio**: Colaboración sin login
**Prueba**: Compartir token, editar sin ownership

---

## 📦 Dependencias Externas

### Bibliotecas Necesarias (ya presentes)
- ✅ `moviepy` - Video rendering
- ✅ `pydantic` - DTOs
- ✅ `sqlmodel` - ORM

### Archivo de Música
- 📁 Adjuntado: `005. Ruins (UNDERTALE Soundtrack) - Toby Fox.mp3`
- 📍 Ubicación recomendada: `media_local/default_music/undertale_ruins.mp3`
- 🔗 Alternativa: Subir a S3/CDN y usar URL

---

## 🗂️ Estructura de Carpetas (Cambios)

```
icebergapp/
├── PROMPT_NUEVAS_FEATURES.md         ← Tú estás aquí
├── ARQUITECTURA_Y_EJEMPLOS.md        ← Guía técnica
├── media_local/
│   └── default_music/
│       └── undertale_ruins.mp3       ← NUEVO
├── packages/
│   ├── entities/
│   │   └── src/iceberg_entities/
│   │       └── level.py              ✏️ Agregar music_url
│   ├── dto/
│   │   └── src/iceberg_dto/
│   │       ├── video_dto.py          ✏️ Agregar music_url, entry_title
│   │       └── level_dto.py          ✏️ Agregar music_url
│   ├── negocio/
│   │   └── src/iceberg_negocio/
│   │       ├── editor_token_service.py  ← NUEVO
│   │       ├── share_service.py      ✏️ Método build_editor_url()
│   │       └── video/
│   │           ├── video_service.py  ✏️ Pasar music_url
│   │           └── video_renderer.py ✏️ Zoom + música + no localhost
│   ├── repositorio/
│   │   └── ...
│   └── accesodatos/
│       └── ...
├── packages/api/
│   └── src/iceberg_api/
│       ├── main.py                   ✏️ Agregar middleware
│       └── routers/
│           ├── level_router.py       ✏️ PATCH con music_url
│           ├── editor_router.py      ← NUEVO
│           └── ...
└── cliente/
    └── src/
        ├── api.js                    ✏️ Nuevos endpoints
        └── components/
            ├── IcebergEditor.vue     ✏️ Música + compartir editor
            └── EditorView.vue        ← NUEVO
```

---

## 🚀 Checklist Pre-Implementación

### ✅ Validar Ambiente
```bash
# Backend
cd packages/api
pip install -e ".[dev]"
pytest  # Verificar tests pasan

# Frontend
cd cliente
npm install
npm run dev  # Verificar que corre sin errores
```

### ✅ Crear Rama de Feature
```bash
git checkout -b features/video-enhancements
```

### ✅ Configurar Música Default
```bash
# Copiar archivo de música a media_local/
cp "005. Ruins (UNDERTALE Soundtrack) - Toby Fox.mp3" \
   media_local/default_music/undertale_ruins.mp3
```

### ✅ Configurar Variables de Entorno
```env
# .env
EDIT_TOKEN_EXPIRY_DAYS=30
EDIT_TOKEN_LENGTH=32
UNDERTALE_RUINS_URL=file://media_local/default_music/undertale_ruins.mp3
```

---

## 🧪 Plan de Pruebas

### Unit Tests (Backend)
```python
# test_video_renderer.py
def test_render_without_localhost_outro():
    # Verificar que outro no muestra localhost
    
def test_render_with_music_url():
    # Verificar que música se carga
    
def test_editor_token_validation():
    # Verificar tokens expiran correctamente
```

### Integration Tests (End-to-End)
```bash
# 1. Crear iceberg
# 2. Asignar música a nivel
# 3. Generar video
# 4. Verificar video contiene música
# 5. Compartir editor
# 6. Editar con token
# 7. Generar nuevo video
```

### Manual Testing Checklist
- [ ] Video inicia con zoom al título
- [ ] Audio de UNDERTALE Ruins se escucha
- [ ] Outro está vacío cuando es localhost
- [ ] Outro muestra URL cuando es public
- [ ] Token válido permite editar
- [ ] Token inválido devuelve 403
- [ ] Música se descarga correctamente si es URL
- [ ] Música se repite si es más corta que el video

---

## 📝 Notas de Desarrollo

### Zoom Animation - Consideraciones
```python
# Option 1: Usar moviepy.vfx (simple pero limitado)
from moviepy import vfx
intro = intro.with_effects([vfx.Resize(scale_factor=1.5)])

# Option 2: Renderizar frames progresivamente (más control)
# - Generar N frames con PIL/matplotlib
# - Aumentar tamaño del text de frame en frame
# - Compilar en video

# Option 3: Usar manim o similar (overkill para esto)
```

### Música y Audio - Consideraciones
```python
# Problema: ¿Música reemplaza narración o coexisten?
# Solución recomendada: Musik REEMPLAZA, TTS solo si no hay música

# Si queremos ambas (música + TTS), necesitamos:
# - Bajar volumen de TTS
# - O usar música solo en fondo (background)
# - Mezclador de audio

# Por ahora: Música XOR TTS (uno u otro)
```

### Tokens - Seguridad
```python
# ✅ DO: Guardar hash del token, no el plain
# ✅ DO: Expiration date
# ✅ DO: Rate limiting en validación
# ❌ DON'T: Guardar token en plain text
# ❌ DON'T: Tokens sin expiración
# ❌ DON'T: Sin rate limiting
```

---

## 📞 Soporte - Preguntas Frecuentes

### P: ¿Dónde descargo UNDERTALE Ruins?
**R**: Está adjunto en la conversación. Copialo a `media_local/default_music/`.

### P: ¿Puedo usar otra música?
**R**: Sí, cualquier formato que moviepy soporte (MP3, WAV, OGG, etc.).

### P: ¿Qué pasa si la música es muy corta?
**R**: `_prepare_music_audio()` la repite automáticamente (loop).

### P: ¿Cómo expiro un token?
**R**: Automáticamente después de `EDIT_TOKEN_EXPIRY_DAYS` (30 días default).

### P: ¿Puedo revocar un token manualmente?
**R**: Sí, agregar método `revoke_token()` en EditorTokenService.

### P: ¿Otro_text debe estar siempre en el outro?
**R**: Recomendación: mostrar solo si no es localhost, y solo si user lo desea.

---

## 🎬 Próximos Pasos

### Inmediatos (Esta semana)
1. ✅ Revisar este documento
2. ✅ Validar ambiente (pytest, npm run dev)
3. 🔜 Implementar Paso 1 (remover localhost)
4. 🔜 Pruebas de Paso 1

### Corto Plazo (Próxima semana)
5. Implementar Paso 2 (zoom)
6. Implementar Paso 3 (música)
7. Pruebas E2E

### Mediano Plazo (2-3 semanas)
8. Implementar Paso 4 (editor compartido)
9. Pruebas de seguridad
10. Deployment a producción

---

## 📚 Referencias

- **VideoRenderer**: `packages/negocio/src/iceberg_negocio/video/video_renderer.py`
- **VideoService**: `packages/negocio/src/iceberg_negocio/video/video_service.py`
- **MoviePy Docs**: https://zulko.github.io/moviepy/
- **SQLModel**: https://sqlmodel.tiangolo.com/
- **FastAPI**: https://fastapi.tiangolo.com/

---

## 💬 Conclusión

Este documento proporciona:
1. ✅ Análisis completo de cambios necesarios
2. ✅ Código de ejemplo para cada componente
3. ✅ Plan de implementación paso-a-paso
4. ✅ Checklist de testing
5. ✅ Guía de resolución de problemas

**Tiempo estimado total**: 10-14 horas
**Complejidad**: Media-Alta
**Riesgo de breaking changes**: Bajo (arquitectura bien separada)

¿Listo para empezar? 🚀
