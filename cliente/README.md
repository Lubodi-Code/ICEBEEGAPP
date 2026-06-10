# cliente/ — Frontend (Vue 3 + Vite)

SPA para crear y editar icebergs. **No comparte código** con el backend: se comunica con
la API exclusivamente por HTTP (JSON) y delega la vista pública en `GET /i/{slug}`
(renderizada por el backend con Jinja2 + OG tags).

Capa **cliente** dentro de la arquitectura por capas:

```
cliente  ──HTTP──>  api  ->  negocio  ->  repositorio  ->  accesodatos  ->  entities
                                    \
                                     └─ dto (contratos transversales)
```

## Funcionalidad

- Crear icebergs y abrir existentes por slug/enlace (recientes en `localStorage`).
- Editar título; agregar/renombrar/reordenar/eliminar niveles (colapsables).
- Agregar/editar/eliminar entradas; subir fotos (→ WebP) y videos.
- **Copiar enlace** público y abrir la página con OG tags.
- **Generar video**: llama `POST /video` y descarga el `.mp4` narrado.

## Cómo correr

```bash
cd cliente
npm install
cp .env.example .env   # ajusta VITE_API_URL si hace falta
npm run dev            # http://localhost:5173 (la API debe estar en VITE_API_URL)
```

## Build / deploy

```bash
npm run build          # genera dist/
```

Deploy sugerido: **Cloudflare Pages** (gratis) con `VITE_API_URL` apuntando al
Hugging Face Space del backend.
