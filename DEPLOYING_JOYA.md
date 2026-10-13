# Deploying Joya publicly

Joya's public version uses individual accounts, a PostgreSQL database, and
OpenAI through a server-side API key. It does not publish the local Ollama
service or the notes and chat history from the desktop app.

## Run it locally

1. Install Python 3.11 or newer.
2. In the project folder, run `pip install -r requirements.txt`.
3. Double-click `RUN_JOYA_WEBSITE.bat` (or run `python web_app.py`).
4. Open `http://127.0.0.1:8000` if the browser does not open automatically.
5. For AI chat locally, set `OPENAI_API_KEY` in your environment first.

## Publish on Render

1. Put the project in a **private GitHub repository**. Do not upload `.venv`,
   `.env`, API keys, local databases, or personal chat/notes files.
2. In the OpenAI dashboard, create an API key and set an appropriate usage
   budget. Do not paste that key into source files, browser JavaScript, or chat.
3. In Render, choose **New → Blueprint** and connect the private repository.
   Render reads `render.yaml` to create the Python web service and PostgreSQL
   database.
4. When prompted, enter the OpenAI API key for `OPENAI_API_KEY` as a secret
   environment variable. Render generates the session secret automatically.
5. Wait for the service health check to pass, then use the `onrender.com`
   URL shown on the Render dashboard.
6. Register an account on the deployed site and verify that chat, saved notes,
   and JEE practice work before sharing the URL.

The Blueprint uses a paid Render web service and database plan. Check Render
and OpenAI pricing before deployment. AI use is limited to 30 questions per
account per day; the provider account should also have a spending limit.

Accounts use hashed passwords, HTTP-only session cookies, CSRF checks, and
user-scoped notes/history/progress. HTTPS secure cookies are enabled by the
Render configuration. The local development server is bound only to
`127.0.0.1`; it is not itself a public deployment.
