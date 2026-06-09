# cliente/ — Frontend (placeholder)

Esta carpeta es un **placeholder**. El frontend (Vue 3 + Vite, o Alpine.js) se desarrolla
aparte y **no comparte código** con el backend: se comunica con la API exclusivamente por
HTTP (JSON) y consume las páginas públicas (`GET /i/{slug}`) que el backend renderiza con
Jinja2 + OG tags.

Capa **cliente** dentro de la arquitectura por capas:

```
cliente  ──HTTP──>  api  ->  negocio  ->  repositorio  ->  accesodatos  ->  entities
                                    \
                                     └─ dto (contratos transversales)
```

## Cuando se implemente

- `npm create vite@latest` (plantilla Vue) dentro de esta carpeta.
- Apuntar las llamadas a `http://localhost:8000` (o `PUBLIC_BASE_URL`).
- Deploy sugerido: Cloudflare Pages (gratis).
