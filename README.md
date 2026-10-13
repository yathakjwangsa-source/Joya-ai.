# Joya.ai

Joya is a learning assistant for Physics, Chemistry, Mathematics, JEE practice,
Universe topics, and study notes. The website includes private accounts,
per-user storage, a hosted AI chat, and interactive practice tests.

## Run locally

1. Install Python 3.11 or newer.
2. Install dependencies: `pip install -r requirements.txt`
3. Set `OPENAI_API_KEY` in your terminal environment to enable AI chat.
4. Run `python web_app.py` and open `http://127.0.0.1:8000`.

## Deploy

The Render Blueprint creates the web service and PostgreSQL database. Follow
[DEPLOYING_JOYA.md](./DEPLOYING_JOYA.md) for setup, secrets, and cost details.
Do not commit API keys, `.env` files, local databases, or personal data.

Joya uses AI-generated content that can be incorrect; verify important answers
with trusted learning resources.
