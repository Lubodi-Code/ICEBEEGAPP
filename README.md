# Iceberg Web — Backend

Plataforma social para crear, compartir y narrar *icebergs* de curiosidades entre amigos.
Backend en **Python / FastAPI** con **arquitectura por capas**, donde **cada capa es su propio
paquete instalable** (estilo solución multi-proyecto de .NET), gestionado como un **uv workspace**.

La regla de dependencias entre capas no es solo una convención: queda **enforced** por
`import-linter` y se valida en CI.

---

## Arquitectura por capas

Cada capa vive en `packages/<capa>/` como un paquete Python independiente con su propio
`pyproject.toml` y su propio nombre de import:

| Paquete (carpeta) | Import | Rol |
|---|---|---|
| `packages/entities`    | `iceberg_entities`    | Modelos SQLModel (tablas). Acceso a datos. |
| `packages/accesodatos` | `iceberg_accesodatos` | Settings, engine y sesión. Acceso a datos. |
| `packages/repositorio` | `iceberg_repositorio` | Repositorios por entidad. **Única** capa que toca la DB. |
| `packages/dto`         | `iceberg_dto`         | Schemas Pydantic (request/response). **Transversal.** |
| `packages/negocio`     | `iceberg_negocio`     | Servicios, mapeo entity↔dto, factory DI, storage R2, pipeline de video. |
| `packages/api`         | `iceberg_api`         | FastAPI: routers, dependencias, páginas públicas. |
| `cliente/`             | —                     | Frontend (Vue, aparte). Habla a `api` por HTTP. |

### Regla de dependencias (la parte más importante)

```
api  ->  negocio  ->  repositorio  ->  accesodatos  ->  entities
                 \
                  └─>  dto   (transversal: lo importan negocio y api; dto no importa ninguna capa)
```

- **`api`** importa **solo** `negocio` y `dto` (más `accesodatos.get_session` para abrir la sesión).
- **`api` NUNCA** importa `iceberg_repositorio` ni `iceberg_entities`.
- **`negocio`** importa `repositorio`, `dto`, `entities` y `accesodatos` (tipos de sesión).
- **`dto`** no importa ninguna otra capa.
- **`cliente`** no comparte código; se comunica por HTTP.

Esto se enforce en [`.importlinter`](.importlinter) con dos contratos:

1. **Capas** (`type = layers`): un nivel inferior no puede importar uno superior.
2. **API no toca datos** (`type = forbidden`): `iceberg_api` no puede importar
   `iceberg_repositorio` ni `iceberg_entities`.

```bash
uv run lint-imports   # debe PASAR; falla si la API toca la capa de datos
```

### ¿Por qué funciona el aislamiento?

Cada `pyproject.toml` declara **solo** sus dependencias internas permitidas. Por ejemplo,
`api` depende de `iceberg-negocio`, `iceberg-dto` e `iceberg-accesodatos`, pero **no** de
`iceberg-repositorio` ni `iceberg-entities`. Si alguien intentara importarlos, fallaría tanto
la resolución de dependencias como `lint-imports`.

---

## Modelo de datos

Cadena 1-a-N con borrado en cascada: `Iceberg → Level → Entry → Media` (más `User` como dueño).
PK UUID (str), timestamps en UTC. Definidos en `packages/entities/`.

## API REST (resumen)

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/icebergs` | Crear un iceberg |
| GET | `/icebergs/{slug}` | Obtener el iceberg con su grafo (levels→entries→media) |
| PATCH | `/icebergs/{id}` | Editar un iceberg |
| DELETE | `/icebergs/{id}` | Eliminar un iceberg (cascada) |
| POST | `/icebergs/{iceberg_id}/levels` | Crear un nivel |
| PATCH / DELETE | `/levels/{id}` | Editar / eliminar nivel |
| POST | `/levels/reorder` | Reordenar niveles |
| POST | `/levels/{level_id}/entries` | Crear una entrada |
| PATCH / DELETE | `/entries/{id}` | Editar / eliminar entrada |
| POST | `/entries/{entry_id}/media` | Subir foto/video (multipart; imágenes → WebP) |
| POST | `/video` | Genera y descarga el video narrado (.mp4 efímero) |
| GET | `/i/{slug}` | Página pública con OG tags (Jinja2) |
| GET | `/health` | Healthcheck |

---

## Requisitos

- [uv](https://docs.astral.sh/uv/) (gestiona Python 3.12 automáticamente).
- No necesitas Postgres ni credenciales R2 para dev: por defecto usa **SQLite** y un
  **fallback de storage local** (`./media_local/`), de modo que corre **100% offline**.

## Configuración (`.env`)

Copia `.env.example` a `.env` y ajusta lo que necesites:

| Variable | Default | Para qué |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./dev.db` | DB. En prod: `postgresql://...` (Neon); se normaliza a `postgresql+psycopg://`. |
| `PUBLIC_BASE_URL` | `http://localhost:8000` | Base de slugs compartibles, OG tags y media local. |
| `R2_ACCOUNT_ID` / `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` / `R2_BUCKET` / `R2_PUBLIC_URL` | vacío | Cloudflare R2. Si están vacías, usa el fallback local. |
| `MAX_VIDEO_MB` | `25` | Tamaño máximo para videos subidos. |
| `TTS_ENGINE` | `espeak` | Motor de voz: `espeak` (robótico clásico), `piper` (neuronal, requiere `PIPER_VOICE`) o `silent` (sin TTS instalado; dev/tests). |
| `ESPEAK_VOICE` / `ESPEAK_SPEED` | `es` / `165` | Voz y velocidad de eSpeak-NG. |
| `PIPER_VOICE` | vacío | Ruta al modelo `.onnx` de Piper (solo con `TTS_ENGINE=piper`). |
| `VIDEO_ASPECT` / `VIDEO_FPS` | `9:16` / `24` | Aspecto (vertical u horizontal `16:9`) y fps del video exportado. |

---

## Cómo correr todo

```bash
# 1) Instalar el workspace completo (todas las capas en editable)
uv sync

# 2) Arrancar el servidor de desarrollo
uv run uvicorn iceberg_api.main:app --reload --port 8000
#   -> http://localhost:8000/health   (healthcheck)
#   -> http://localhost:8000/docs     (OpenAPI / Swagger)
```

### Flujo de ejemplo

```bash
# Crear iceberg
curl -X POST localhost:8000/icebergs -H "Content-Type: application/json" \
  -d '{"titulo":"Curiosidades del oceano"}'
# -> { "id": "...", "slug": "curiosidades-del-oceano", ... }

# Crear nivel y entrada (usa los ids/slug devueltos)
curl -X POST localhost:8000/icebergs/<ICEBERG_ID>/levels -H "Content-Type: application/json" \
  -d '{"numero":1,"nombre":"La superficie"}'
curl -X POST localhost:8000/levels/<LEVEL_ID>/entries -H "Content-Type: application/json" \
  -d '{"titulo":"El mar tiene rios"}'

# Subir una imagen (se comprime a WebP)
curl -X POST localhost:8000/entries/<ENTRY_ID>/media -F "file=@foto.png"

# Leer el grafo completo y la página pública
curl localhost:8000/icebergs/<SLUG>
curl localhost:8000/i/<SLUG>
```

## Calidad y tests

```bash
uv run ruff check          # lint
uv run ruff format         # formato
uv run lint-imports        # contratos de capas (import-linter)
uv run pytest              # smoke tests (health + flujo CRUD + público + video 501)
```

## Docker (backend, compatible HF Spaces)

```bash
docker build -t iceberg-api .
docker run -p 7860:7860 --env-file .env iceberg-api
# -> http://localhost:7860/health
```

---

## Estado / Roadmap

- [x] **Fase 1 — MVP:** CRUD de iceberg/level/entry + vista pública.
- [x] **Fase 2 — Compartir:** enlace público con OG tags (el gancho).
- [x] **Fase 3 — Multimedia:** subida con compresión WebP (Pillow) → R2 / fallback local.
- [x] **Fase 4 — Video:** pipeline TTS (eSpeak-NG / Piper / silent) + moviepy/FFmpeg en
      `packages/negocio/src/iceberg_negocio/video/`; `POST /video` devuelve el `.mp4`
      (escenas Ken Burns, overlays de título/nivel/subtítulos, intro/outro, 9:16 o 16:9).
- [x] **Fase 5 — Frontend:** SPA Vue 3 + Vite en `cliente/` (crear/editar iceberg, niveles
      colapsables, subir media, copiar enlace y generar video).
- [ ] **Pulido futuro:** cuentas, plantillas, música de fondo, etiquetas por nivel.

> Restricción de diseño: **costo de operación cero** (todo dentro de planes gratuitos:
> Cloudflare Pages/R2, Hugging Face Spaces, Neon, GitHub Actions).
