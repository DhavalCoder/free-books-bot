import os
import google.generativeai as genai
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=(
        "You are an expert AI assistant specialized exclusively in Artificial Intelligence, "
        "Machine Learning, Deep Learning, LLMs, Agents, RAG, MCP, Vector Databases, Prompt Engineering, "
        "MLOps, and all related AI/ML topics.\n\n"
        "Rules:\n"
        "- Only answer AI-related questions. For anything else, say: "
        "'⚠ This terminal only handles AI queries. Ask me about AI, LLMs, agents, RAG, MCP, etc.'\n"
        "- Always structure responses clearly with sections, bullet points, and code examples where relevant.\n"
        "- Be concise but thorough. Think like a senior AI engineer explaining to a fellow developer."
    )
)

# Store chat sessions per user
sessions: dict[int, genai.ChatSession] = {}

BANNER = """```
╔══════════════════════════════════════╗
║         AI TERMINAL v1.0             ║
║   Powered by Gemini • by DhavalCoder ║
╚══════════════════════════════════════╝
Type any AI question to get started.
Commands: /start /clear /help
```"""

HELP_TEXT = """```
┌─────────────────────────────────────┐
│           AVAILABLE COMMANDS        │
├─────────────────────────────────────┤
│ /start  → Boot terminal             │
│ /clear  → Clear conversation memory │
│ /help   → Show this help            │
├─────────────────────────────────────┤
│ TOPICS YOU CAN ASK ABOUT:           │
│  • LLMs, GPT, Claude, Gemini        │
│  • RAG, Vector DBs, Embeddings      │
│  • AI Agents, MCP, LangChain        │
│  • Prompt Engineering               │
│  • Fine-tuning, LoRA, PEFT          │
│  • MLOps, Deployment, Inference     │
│  • Computer Vision, NLP             │
│  • Reinforcement Learning           │
└─────────────────────────────────────┘
```"""


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    sessions[user_id] = model.start_chat(history=[])
    await update.message.reply_text(BANNER, parse_mode="Markdown")


async def clear(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    sessions[user_id] = model.start_chat(history=[])
    await update.message.reply_text(
        "```\n> Memory cleared. New session started.\n```",
        parse_mode="Markdown"
    )


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def chat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text.strip()

    if user_id not in sessions:
        sessions[user_id] = model.start_chat(history=[])

    # Show typing indicator
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = sessions[user_id].send_message(user_input)
        reply = response.text

        # Terminal-style header
        header = f"`> {user_input[:50]}{'...' if len(user_input) > 50 else ''}`\n\n"
        await update.message.reply_text(
            header + reply,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    except Exception as e:
        await update.message.reply_text(
            f"```\n[ERROR] {str(e)}\nTry /clear to reset session.\n```",
            parse_mode="Markdown"
        )


if __name__ == "__main__":
    if not BOT_TOKEN or not GEMINI_KEY:
        raise ValueError("BOT_TOKEN or GEMINI_API_KEY not set in .env")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("AI Terminal Bot running...")
    app.run_polling()
