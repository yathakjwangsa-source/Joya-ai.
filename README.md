# Joya.ai

Joya is a learning assistant for Physics, Chemistry, Mathematics, JEE practice,
Universe topics, and study notes. The website includes private accounts,
per-user storage, optional Ollama-powered AI chat, and interactive practice tests.

You can use lessons, notes, and JEE practice as a guest without creating an
account. Guest learning data is saved to that browser's guest profile. Sign in
or create an account to keep it across devices. AI chat runs through Ollama on
the same computer as the website; no OpenAI key or paid AI API is used.

## Run locally

1. Install Python 3.11 or newer and [Ollama](https://ollama.com/download).
2. In a terminal, download Joya's default model: `ollama pull qwen3.5:4b`.
3. Install dependencies: `pip install -r requirements.txt`
4. Run `python web_app.py` and open `http://127.0.0.1:8000`.
   Keep Ollama running locally for AI chat. Set `OLLAMA_MODEL` to use a
   different model already downloaded in Ollama.

## Deploy

The Render Blueprint creates a free web service. Follow
[DEPLOYING_JOYA.md](./DEPLOYING_JOYA.md) to connect a free Supabase database,
configure secrets, and understand hosting limitations. Do not commit database
secrets, `.env` files, local databases, or personal data.

Joya uses AI-generated content that can be incorrect; verify important answers
with trusted learning resources.
