# InsurCalim AI — Investigator Dashboard (React)

A professional React + Tailwind dashboard for the flagship claim flow:
**submit → live investigation → explainable report**. It talks to the Starlette
API (`api/main.py`), which reuses the existing Python pipeline unchanged.

## Design

Dark, premium "operations dashboard" style (glassmorphism, cyan/indigo glow),
sharing the landing page's brand tokens. Icons are SVG (lucide-react); numbers
use tabular mono figures. Built following the `ui-ux-pro-max` design system.

## Run (development)

Prerequisites: the API and database must be running.

```bash
# 1) Database + API (from the repo root)
docker compose -f infra/docker-compose.yml up -d db
.venv/Scripts/python.exe -m uvicorn api.main:app --port 8000

# 2) This app
cd dashboard
npm install
npm run dev            # http://localhost:5174
```

Open it via the sign-in page (http://localhost:5173) so it receives a session
token, or append `?token=insurclaim-demo-2026` for a direct dev login.

`/api` is proxied to `http://localhost:8000` in dev (see `vite.config.js`), so
the browser talks same-origin and there is no CORS setup to worry about.

## Build

```bash
npm run build         # -> dist/
npm run preview
```

## Environment

See `.env.example`. `VITE_API_URL` (default `/api`) and `VITE_LANDING_URL`.
