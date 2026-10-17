# Deploying Joya publicly

Joya's public version uses individual accounts and a PostgreSQL database.
AI chat connects to an Ollama server configured for the website process. A
Render service cannot access Ollama running on your personal computer; local
Ollama chat is intended for running Joya on that same computer.

## Run it locally

1. Install Python 3.11 or newer.
2. In the project folder, run `pip install -r requirements.txt`.
3. Double-click `RUN_JOYA_WEBSITE.bat` (or run `python web_app.py`).
4. Open `http://127.0.0.1:8000` if the browser does not open automatically.
5. Install Ollama and run `ollama pull qwen3.5:4b` before using AI chat.

## Publish for free with Render and Supabase

The Render Blueprint uses its Free web-service plan and an external Supabase
Postgres database. Supabase's free plan is limited and may pause projects after
one week of inactivity, but avoids Render's 30-day expiration for its own free
Postgres databases.

1. Push the project to GitHub without uploading `.venv`, `.env`, API keys,
   local databases, or personal chat/notes files.
2. Create a Supabase account at [supabase.com](https://supabase.com/) and make
   a project on its Free plan. In **Connect**, choose the Session pooler and
   copy its PostgreSQL connection string. This connection string is the
   database URL; keep its password private.
3. In Render, choose **New → Blueprint** and connect the GitHub repository.
   The Blueprint creates a Free Python web service and asks for `DATABASE_URL`.
   Paste the Supabase connection string there as a secret value. Render
   generates the session secret automatically.
4. For public AI chat, use an Ollama host with HTTPS and authentication; do
   not expose Ollama directly to the public internet. In the Render service's
   **Environment** settings, set `OLLAMA_URL` to the host's
   `https://your-host.example/api/chat`, `OLLAMA_MODEL` to a model installed on
   that host, and `OLLAMA_API_KEY` to its bearer token (without the `Bearer `
   prefix). These values are private; do not commit them to GitHub. Without a
   reachable secure Ollama host, keep public AI chat unavailable and use local
   Ollama only on your PC.
5. Wait for the service health check to pass, then use the `onrender.com` URL
   shown on the Render dashboard.
6. Register an account on the deployed site and verify that saved notes and
   JEE practice work before sharing the URL.
7. To install Joya on Windows, open the deployed HTTPS URL in Microsoft Edge
   or Chrome and choose **Install Joya** from the browser's menu or address
   bar. The installed app uses the same account and online service as the site.

Accounts use hashed passwords, HTTP-only session cookies, CSRF checks, and
user-scoped notes/history/progress. HTTPS secure cookies are enabled by the
Render configuration. Render's Free web service sleeps after 15 minutes
without traffic and can take about a minute to wake; its local filesystem is
temporary, so the external database is required for persistent user data.

AI chat is optional and requires a running Ollama server with the configured
model. Do not expose a local Ollama server publicly. Hosted Render instances
cannot reach Ollama on your personal computer without a separately secured,
network-accessible Ollama host. The app sends `OLLAMA_API_KEY` as a bearer
authorization header when one is configured.

The local development server is bound only to `127.0.0.1`; it is not itself a
public deployment.
