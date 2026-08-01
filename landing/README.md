# InsurClaim AI Landing page

A cinematic React (Vite) landing page and sign-in gate for the InsurClaim AI dashboard.
On a successful sign-in it hands off to the Streamlit dashboard (port 8501) using a shared
token, so the user is not asked to sign in a second time.

## Run

The Streamlit dashboard must be running first (from the repo root):

```bash
python -m streamlit run frontend/app.py --server.port 8501
```

Then start the landing page:

```bash
cd landing
npm install
npm run dev
```

Open **http://localhost:5173**, sign in with the demo credentials, and the dashboard opens.

- Demo credentials: `admin` / `insurclaim2026`
- To override any config, copy `.env.example` to `.env.local` and edit the `VITE_*` values.

## How the sign-in hand-off works

1. `LoginCard.jsx` checks the entered username/password against the Vite env values.
2. On success it redirects to `${VITE_STREAMLIT_URL}/?token=${VITE_APP_LOGIN_TOKEN}`.
3. The Streamlit app (`frontend/app.py`, `_check_auth`) reads that `token` query param; if it
   matches `APP_LOGIN_TOKEN` it authenticates the session and clears the token from the URL.

`VITE_APP_LOGIN_TOKEN` here and `APP_LOGIN_TOKEN` in the repo-root `.env` must match.

## Security note (demo only)

This is a **demo gate, not real authentication**. Vite inlines the `VITE_*` values into the
client bundle, and the Streamlit dashboard on 8501 is directly reachable, so anyone who can
reach the ports can reach the app. Do not put real secrets in `.env.example`; use synthetic
demo credentials only. Real secrets live in the git-ignored root `.env`.

## Assets

The hero uses a looping car video at `public/assets/hero-cars.mp4` with a poster image at
`public/assets/hero-poster.jpg`. If those files are absent the hero falls back to a cinematic
CSS gradient, so the page still looks good offline. Replace them with your own free-license
clips/images (e.g. from Coverr, Pexels or Pixabay) if you like.
