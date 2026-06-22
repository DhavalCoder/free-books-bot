import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

SYSTEM_PROMPT = (
    "You are an expert AI assistant specialized exclusively in Artificial Intelligence, "
    "Machine Learning, Deep Learning, LLMs, Agents, RAG, MCP, Vector Databases, Prompt Engineering, "
    "MLOps, and all related AI/ML topics.\n\n"
    "Rules:\n"
    "- Only answer AI-related questions. For anything else, reply: "
    "'⚠ This terminal only handles AI queries. Ask me about AI, LLMs, agents, RAG, MCP, etc.'\n"
    "- Structure responses clearly with sections and bullet points.\n"
    "- Include code examples where relevant.\n"
    "- Be concise but thorough."
)

# Store conversation history per user
sessions: dict[int, list] = {}

BANNER = """```
╔══════════════════════════════════════╗
║         AI TERMINAL v1.0             ║
║  Powered by DeepSeek • DhavalCoder   ║
╚══════════════════════════════════════╝
> Ready. Ask me anything about AI.
> Commands: /start  /clear  /help
```"""

HELP_TEXT = """```
┌─────────────────────────────────────┐
│           AVAILABLE COMMANDS        │
├─────────────────────────────────────┤
│ /start  → Boot terminal             │
│ /clear  → Clear conversation memory │
│ /help   → Show this help            │
├─────────────────────────────────────┤
│ TOPICS:                             │
│  LLMs · GPT · Claude · Gemini       │
│  RAG · Vector DBs · Embeddings      │
│  AI Agents · MCP · LangChain        │
│  Prompt Engineering · Fine-tuning   │
│  LoRA · PEFT · MLOps · Inference    │
│  Computer Vision · NLP · RL         │
└─────────────────────────────────────┘
```"""


def ask_openrouter(history: list) -> str:
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "deepseek/deepseek-r1-0528:free",
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + history,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    sessions[update.effective_user.id] = []
    await update.message.reply_text(BANNER, parse_mode="Markdown")


async def clear(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    sessions[update.effective_user.id] = []
    await update.message.reply_text("```\n> Memory cleared. New session started.\n```", parse_mode="Markdown")


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def chat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text.strip()

    if user_id not in sessions:
        sessions[user_id] = []

    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    sessions[user_id].append({"role": "user", "content": user_input})

    try:
        reply = ask_openrouter(sessions[user_id])
        sessions[user_id].append({"role": "assistant", "content": reply})
        header = f"`> {user_input[:50]}{'...' if len(user_input) > 50 else ''}`\n\n"
        await update.message.reply_text(header + reply, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        sessions[user_id].pop()  # remove failed message
        await update.message.reply_text(f"```\n[ERROR] {str(e)}\nTry /clear to reset.\n```", parse_mode="Markdown")


if __name__ == "__main__":
    if not BOT_TOKEN or not OPENROUTER_KEY:
        raise ValueError("BOT_TOKEN or OPENROUTER_API_KEY not set")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("AI Terminal Bot running...")
    app.run_polling()
