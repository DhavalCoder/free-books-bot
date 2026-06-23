import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

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

sessions: dict[int, list] = {}

BANNER = """```
╔══════════════════════════════════════╗
║         AI TERMINAL v1.0             ║
║   Powered by Groq • DhavalCoder      ║
╚══════════════════════════════════════╝
> Ready. Ask me anything about AI.
> Type /commands to see all commands.
```"""

COMMANDS_TEXT = """```
┌─────────────────────────────────────┐
│           ALL COMMANDS              │
├─────────────────────────────────────┤
│ /start          → Boot terminal     │
│ /clear          → Clear memory      │
│ /help           → Topics list       │
│ /commands       → Show this menu    │
│ /roadmap <topic>→ Detailed roadmap  │
│ /notes <topic>  → Study notes       │
│ /resources <topic>→ Free links      │
│ /quiz <topic>   → Quiz question     │
│ /explain <term> → Simple explanation│
└─────────────────────────────────────┘
Examples:
  /roadmap LLMs
  /notes RAG
  /resources Prompt Engineering
  /quiz Transformers
  /explain attention mechanism
```"""

HELP_TEXT = """```
┌─────────────────────────────────────┐
│           AI TOPICS                 │
├─────────────────────────────────────┤
│  LLMs · GPT · Claude · Gemini       │
│  RAG · Vector DBs · Embeddings      │
│  AI Agents · MCP · LangChain        │
│  Prompt Engineering · Fine-tuning   │
│  LoRA · PEFT · MLOps · Inference    │
│  Computer Vision · NLP · RL         │
└─────────────────────────────────────┘
```"""


def groq(messages: list) -> str:
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile", "messages": messages, "max_tokens": 2048},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def ai(prompt: str) -> str:
    return groq([{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}])


async def send(update: Update, text: str):
    try:
        await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception:
        await update.message.reply_text(text, disable_web_page_preview=True)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    sessions[update.effective_user.id] = []
    await update.message.reply_text(BANNER, parse_mode="Markdown")


async def clear(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    sessions[update.effective_user.id] = []
    await update.message.reply_text("```\n> Memory cleared. New session started.\n```", parse_mode="Markdown")


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def commands(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(COMMANDS_TEXT, parse_mode="Markdown")


async def roadmap(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(ctx.args)
    if not topic:
        await update.message.reply_text("Usage: `/roadmap <topic>`\nExample: `/roadmap LLMs`", parse_mode="Markdown")
        return
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ai(f"Create a very detailed step-by-step learning roadmap for: {topic}. "
               f"Include phases, subtopics, estimated time, and resources for each phase.")
    await send(update, f"🗺 *Roadmap: {topic}*\n\n{reply}")


async def notes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(ctx.args)
    if not topic:
        await update.message.reply_text("Usage: `/notes <topic>`\nExample: `/notes RAG`", parse_mode="Markdown")
        return
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ai(f"Create comprehensive study notes for: {topic}. "
               f"Include: definition, key concepts, how it works, use cases, pros/cons, and code example if applicable.")
    await send(update, f"📝 *Notes: {topic}*\n\n{reply}")


async def resources(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(ctx.args)
    if not topic:
        await update.message.reply_text("Usage: `/resources <topic>`\nExample: `/resources Transformers`", parse_mode="Markdown")
        return
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ai(f"List the best free learning resources for: {topic}. "
               f"Include papers, YouTube channels, GitHub repos, courses, and websites with URLs.")
    await send(update, f"🔗 *Resources: {topic}*\n\n{reply}")


async def quiz(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(ctx.args) or "AI/ML"
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ai(f"Give me one challenging multiple choice quiz question about: {topic}. "
               f"Format: Question, 4 options (A/B/C/D), then the correct answer with explanation.")
    await send(update, f"🧠 *Quiz: {topic}*\n\n{reply}")


async def explain(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    term = " ".join(ctx.args)
    if not term:
        await update.message.reply_text("Usage: `/explain <term>`\nExample: `/explain attention mechanism`", parse_mode="Markdown")
        return
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ai(f"Explain '{term}' in simple terms (ELI5 style), then give a more technical explanation with an analogy and example.")
    await send(update, f"💡 *Explain: {term}*\n\n{reply}")


async def chat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text.strip()
    if user_id not in sessions:
        sessions[user_id] = []
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    sessions[user_id].append({"role": "user", "content": user_input})
    try:
        reply = groq([{"role": "system", "content": SYSTEM_PROMPT}] + sessions[user_id])
        sessions[user_id].append({"role": "assistant", "content": reply})
        await send(update, f"> {user_input[:50]}{'...' if len(user_input) > 50 else ''}\n\n{reply}")
    except Exception as e:
        sessions[user_id].pop()
        await update.message.reply_text(f"```\n[ERROR] {str(e)}\nTry /clear to reset.\n```", parse_mode="Markdown")


if __name__ == "__main__":
    if not BOT_TOKEN or not GROQ_API_KEY:
        raise ValueError("BOT_TOKEN or GROQ_API_KEY not set")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("commands", commands))
    app.add_handler(CommandHandler("roadmap", roadmap))
    app.add_handler(CommandHandler("notes", notes))
    app.add_handler(CommandHandler("resources", resources))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("explain", explain))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("AI Terminal Bot running...")
    app.run_polling()
