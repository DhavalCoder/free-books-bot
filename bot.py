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
    "- Only answer AI-related questions. For anything else say: "
    "'⚠ This terminal only handles AI queries.'\n"
    "- Structure responses clearly with sections and bullet points.\n"
    "- Include code examples where relevant."
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
│ /start            → Boot terminal   │
│ /clear            → Clear memory    │
│ /help             → Topics list     │
│ /commands         → This menu       │
│ /roadmap <topic>  → Detailed roadmap│
│ /notes <topic>    → Study notes     │
│ /resources <topic>→ Free links      │
│ /quiz <topic>     → Quiz question   │
│ /explain <term>   → Explanation     │
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


def groq_call(messages: list, max_tokens: int = 2048) -> str:
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile", "messages": messages, "max_tokens": max_tokens},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def ai(prompt: str, max_tokens: int = 2048) -> str:
    return groq_call([{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}], max_tokens)


async def send_chunks(update: Update, chunks: list[str]):
    """Send a list of strings as separate messages."""
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            await update.message.reply_text(chunk, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception:
            await update.message.reply_text(chunk, disable_web_page_preview=True)


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
    await update.message.reply_text("```\n> Memory cleared.\n```", parse_mode="Markdown")


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def commands_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(COMMANDS_TEXT, parse_mode="Markdown")


async def roadmap(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(ctx.args)
    if not topic:
        await update.message.reply_text("Usage: `/roadmap <topic>`\nExample: `/roadmap LLMs`", parse_mode="Markdown")
        return
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await send(update, f"🗺 *Roadmap: {topic}* — generating...")

    reply = ai(
        f"Create a detailed learning roadmap for: {topic}.\n"
        f"Format it as exactly 5 phases. Each phase must be separated by '---SPLIT---'.\n"
        f"Each phase: Phase number, title, duration, topics to learn, and resources.",
        max_tokens=3000
    )

    chunks = reply.split("---SPLIT---")
    if len(chunks) <= 1:
        # fallback: split by double newline sections
        chunks = [c for c in reply.split("\n\n") if c.strip()]
        # group into ~5 messages
        grouped, current = [], ""
        for c in chunks:
            current += c + "\n\n"
            if len(current) > 600:
                grouped.append(current)
                current = ""
        if current:
            grouped.append(current)
        chunks = grouped

    await send_chunks(update, [f"🗺 *Roadmap: {topic}*\n\n*Phase {i+1}:*\n{c}" for i, c in enumerate(chunks)])
    await send(update, "✅ *Roadmap complete!* Use `/notes " + topic + "` for detailed study notes.")


async def notes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(ctx.args)
    if not topic:
        await update.message.reply_text("Usage: `/notes <topic>`\nExample: `/notes RAG`", parse_mode="Markdown")
        return
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await send(update, f"📝 *Notes: {topic}* — generating...")

    sections = [
        ("📖 1/6 — Definition", f"Define '{topic}' in 3-5 sentences only."),
        ("⚙️ 2/6 — How It Works", f"Explain step by step how '{topic}' works technically. Be concise."),
        ("💡 3/6 — Key Concepts", f"List 5-7 key concepts of '{topic}' with one-line explanations each."),
        ("🛠 4/6 — Use Cases", f"List 5 real-world use cases of '{topic}' with brief examples."),
        ("💻 5/6 — Code Example", f"Show one practical Python code example for '{topic}' with short comments."),
        ("✅ 6/6 — Summary", f"3 bullet points only: what '{topic}' is, why it matters, when to use it."),
    ]

    for title, prompt in sections:
        await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        reply = ai(prompt)
        await send(update, f"*{title}*\n\n{reply}")

    await send(update, f"✅ *Notes complete for {topic}!*")


async def resources(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(ctx.args)
    if not topic:
        await update.message.reply_text("Usage: `/resources <topic>`", parse_mode="Markdown")
        return
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ai(f"List the best free learning resources for: {topic}. "
               f"Include papers, YouTube channels, GitHub repos, courses, and websites with URLs.")
    await send(update, f"🔗 *Resources: {topic}*\n\n{reply}")


async def quiz(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(ctx.args) or "AI/ML"
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ai(f"Give one challenging multiple choice quiz question about: {topic}. "
               f"Format: Question, 4 options (A/B/C/D), correct answer with explanation.")
    await send(update, f"🧠 *Quiz: {topic}*\n\n{reply}")


async def explain(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    term = " ".join(ctx.args)
    if not term:
        await update.message.reply_text("Usage: `/explain <term>`", parse_mode="Markdown")
        return
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ai(f"Explain '{term}': first in simple ELI5 terms, then technically with an analogy and code example.")
    await send(update, f"💡 *Explain: {term}*\n\n{reply}")


async def chat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text.strip()
    if user_id not in sessions:
        sessions[user_id] = []
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    sessions[user_id].append({"role": "user", "content": user_input})
    try:
        reply = groq_call([{"role": "system", "content": SYSTEM_PROMPT}] + sessions[user_id])
        sessions[user_id].append({"role": "assistant", "content": reply})
        await send(update, f"> {user_input[:50]}{'...' if len(user_input) > 50 else ''}\n\n{reply}")
    except Exception as e:
        sessions[user_id].pop()
        await update.message.reply_text(f"```\n[ERROR] {str(e)}\n```", parse_mode="Markdown")


if __name__ == "__main__":
    if not BOT_TOKEN or not GROQ_API_KEY:
        raise ValueError("BOT_TOKEN or GROQ_API_KEY not set")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("commands", commands_cmd))
    app.add_handler(CommandHandler("roadmap", roadmap))
    app.add_handler(CommandHandler("notes", notes))
    app.add_handler(CommandHandler("resources", resources))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("explain", explain))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("AI Terminal Bot running...")
    app.run_polling()
