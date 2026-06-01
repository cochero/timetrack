# TimeTrack — Frontend (React + Vite)

The web UI for the TimeTrack operations console. Iteration 1 includes the
sign-in screen, the app shell (sidebar navigation), and a live dashboard.

## Run it
```bash
cd frontend
cp .env.example .env        # point VITE_API_BASE_URL at your backend
npm install
npm run dev                 # opens http://localhost:5173
```
The backend (see ../backend) must be running, and you must have signed up a
firm + owner (POST /api/auth/register-org/ or via the Django admin) to log in.

## Stack
- React 18 + Vite
- react-router-dom (routing), axios (API calls), recharts (charts)
- Plain CSS with design tokens — no build-time CSS framework to configure

## Structure
- `src/api/client.js` — axios instance that attaches your login token
- `src/auth/AuthContext.jsx` — login / logout / current-user state
- `src/components/Layout.jsx` — sidebar + content shell
- `src/pages/Login.jsx`, `src/pages/Dashboard.jsx` — the screens
