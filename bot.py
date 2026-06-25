import os
import time
from collections import defaultdict, deque
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ── Rate limiter: max 10 messages per 60 seconds per user ──────────────────
RATE_LIMIT = 10
RATE_WINDOW = 60
user_timestamps: dict[int, deque] = defaultdict(deque)

def is_rate_limited(user_id: int) -> tuple[bool, int]:
    now = time.time()
    timestamps = user_timestamps[user_id]
    while timestamps and now - timestamps[0] > RATE_WINDOW:
        timestamps.popleft()
    if len(timestamps) >= RATE_LIMIT:
        wait = int(RATE_WINDOW - (now - timestamps[0])) + 1
        return True, wait
    timestamps.append(now)
    return False, 0

# ── System prompt ───────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert AI/ML engineer and system design architect.
You specialize in: LLMs, RAG, AI Agents, MCP, Vector DBs, Prompt Engineering,
MLOps, System Design, Backend Architecture, API Design, Distributed Systems,
Database Design, Microservices, Cloud Architecture, and all AI/ML topics.

Rules:
- Only answer AI, ML, system design, and backend engineering topics.
- For anything else say: '⚠️ Out of scope. Ask me about AI, system design, or backend engineering.'
- Always include working code examples when relevant.
- Format code in proper markdown code blocks with language specified.
- Be precise and production-focused."""

sessions: dict[int, list] = {}

# ── VS Code style UI strings ────────────────────────────────────────────────
BANNER = """```
╔═══════════════════════════════════════════╗
║  ▸ AI TERMINAL  v2.0                      ║
║  ▸ Model  : Llama 3.3 70B via Groq        ║
║  ▸ Topics : AI · ML · System Design       ║
╠═══════════════════════════════════════════╣
║  Type /commands to see all commands       ║
║  Type any question to start chatting      ║
╚═══════════════════════════════════════════╝
```"""

COMMANDS_TEXT = """```
 AI TERMINAL — COMMAND PALETTE
 ───────────────────────────────────────────
  /start              Boot terminal
  /clear              Clear memory
  /help               Show topics
  /commands           This menu

 ── LEARNING ──────────────────────────────
  /roadmap  <topic>   Step-by-step roadmap
  /notes    <topic>   Structured study notes
  /explain  <term>    Simple explanation
  /quiz     <topic>   MCQ quiz question
  /cheatsheet <topic> Quick reference card

 ── BUILDING ──────────────────────────────
  /stack    <usecase> Recommended tech stack
  /architecture <sys> System design blueprint
  /integrate <tool>   Integration guide
  /deploy   <model>   Deployment guide

 ── RESOURCES ─────────────────────────────
  /resources <topic>  Free links & papers
  /compare  <A vs B>  Side-by-side comparison
  /interview <topic>  Interview Q&A

 ───────────────────────────────────────────
  Examples:
    /stack    rag chatbot
    /notes    transformer architecture
    /compare  RAG vs fine-tuning
    /architecture ai agent system
```"""

HELP_TEXT = """```
 SUPPORTED TOPICS
 ───────────────────────────────────────────
  AI / ML
    LLMs · GPT · Claude · Gemini · Llama
    RAG · Vector DBs · Embeddings
    AI Agents · MCP · LangChain · LlamaIndex
    Prompt Engineering · Fine-tuning
    LoRA · PEFT · MLOps · Inference

  SYSTEM DESIGN
    Distributed Systems · Microservices
    API Design · Database Design
    Caching · Message Queues · Load Balancing
    Cloud Architecture · Scalability

  BACKEND ENGINEERING
    FastAPI · Node.js · Databases
    Authentication · Rate Limiting
    Deployment · Docker · Kubernetes
 ───────────────────────────────────────────
```"""


# ── Groq API call ────────────────────────────────────────────────────────────
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
    return groq_call([{"role": "system", "content": SYSTEM_PROMPT},
                      {"role": "user", "content": prompt}], max_tokens)


async def send(update: Update, text: str):
    try:
        await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception:
        await update.message.reply_text(text, disable_web_page_preview=True)


async def check_limit(update: Update) -> bool:
    limited, wait = is_rate_limited(update.effective_user.id)
    if limited:
        await update.message.reply_text(
            f"```\n⏳ Rate limit reached.\n   Try again in {wait}s (max {RATE_LIMIT} msgs/min)\n```",
            parse_mode="Markdown"
        )
    return limited


# ── Command handlers ─────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    sessions[update.effective_user.id] = []
    await update.message.reply_text(BANNER, parse_mode="Markdown")


async def clear(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    sessions[update.effective_user.id] = []
    await update.message.reply_text("```\n✓ Memory cleared — new session started\n```", parse_mode="Markdown")


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def commands_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(COMMANDS_TEXT, parse_mode="Markdown")


async def roadmap(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if await check_limit(update): return
    topic = " ".join(ctx.args)
    if not topic:
        await send(update, "Usage: `/roadmap <topic>`  →  e.g. `/roadmap LLMs`")
        return
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await send(update, f"```\n▸ Generating roadmap: {topic}\n```")
    reply = ai(
        f"Create a detailed 5-phase learning roadmap for: {topic}.\n"
        f"Separate each phase with exactly '---PHASE---'.\n"
        f"Each phase: title, duration, topics, resources, milestone.",
        max_tokens=3000
    )
    phases = [p.strip() for p in reply.split("---PHASE---") if p.strip()]
    if len(phases) <= 1:
        await send(update, f"🗺 *Roadmap: {topic}*\n\n{reply}")
        return
    for i, phase in enumerate(phases, 1):
        await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await send(update, f"🗺 *Phase {i}/{len(phases)} — {topic}*\n\n{phase}")
    await send(update, f"```\n✓ Roadmap complete for: {topic}\n  Next: /notes {topic}\n```")


async def notes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if await check_limit(update): return
    topic = " ".join(ctx.args)
    if not topic:
        await send(update, "Usage: `/notes <topic>`  →  e.g. `/notes RAG`")
        return
    await send(update, f"```\n▸ Generating notes: {topic}\n```")
    sections = [
        ("📖 1/6 — Definition",   f"Define '{topic}' clearly in 4-5 sentences."),
        ("⚙️ 2/6 — How It Works", f"Explain step-by-step how '{topic}' works technically."),
        ("💡 3/6 — Key Concepts", f"List 5-7 key concepts of '{topic}' with one-line explanations."),
        ("🛠 4/6 — Use Cases",    f"List 5 real-world use cases of '{topic}' with examples."),
        ("💻 5/6 — Code Example", f"Write one practical Python code example for '{topic}' with inline comments."),
        ("✅ 6/6 — Summary",      f"Summarize '{topic}' in exactly 3 bullet points: what, why, when."),
    ]
    for title, prompt in sections:
        await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        reply = ai(prompt)
        await send(update, f"*{title}*\n\n{reply}")
    await send(update, f"```\n✓ Notes complete: {topic}\n```")


async def stack(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if await check_limit(update): return
    usecase = " ".join(ctx.args)
    if not usecase:
        await send(update, "Usage: `/stack <use case>`  →  e.g. `/stack rag chatbot`")
        return
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ai(
        f"Recommend the best production tech stack for: {usecase}.\n"
        f"Include: LLM/model choice, vector DB, backend framework, frontend, deployment, monitoring.\n"
        f"For each component explain WHY it's chosen over alternatives.\n"
        f"End with a simple architecture diagram using ASCII art."
    )
    await send(update, f"🛠 *Stack: {usecase}*\n\n{reply}")


async def architecture(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if await check_limit(update): return
    system = " ".join(ctx.args)
    if not system:
        await send(update, "Usage: `/architecture <system>`  →  e.g. `/architecture ai agent`")
        return
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ai(
        f"Design a production-grade system architecture for: {system}.\n"
        f"Include: components, data flow, scalability considerations, failure points, and an ASCII diagram."
    )
    await send(update, f"🏗 *Architecture: {system}*\n\n{reply}")


async def compare(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if await check_limit(update): return
    topic = " ".join(ctx.args)
    if not topic:
        await send(update, "Usage: `/compare <A vs B>`  →  e.g. `/compare RAG vs fine-tuning`")
        return
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ai(f"Compare {topic}. Use a structured table + pros/cons + when to use each.")
    await send(update, f"⚖️ *Compare: {topic}*\n\n{reply}")


async def integrate(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if await check_limit(update): return
    tool = " ".join(ctx.args)
    if not tool:
        await send(update, "Usage: `/integrate <tool>`  →  e.g. `/integrate openai fastapi`")
        return
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ai(f"Show a complete step-by-step guide with working code to integrate: {tool}.")
    await send(update, f"🔌 *Integrate: {tool}*\n\n{reply}")


async def deploy(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if await check_limit(update): return
    model = " ".join(ctx.args)
    if not model:
        await send(update, "Usage: `/deploy <model>`  →  e.g. `/deploy llama`")
        return
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ai(f"Step-by-step production deployment guide for: {model}. Include code, configs, and cost estimate.")
    await send(update, f"🚀 *Deploy: {model}*\n\n{reply}")


async def interview(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if await check_limit(update): return
    topic = " ".join(ctx.args) or "AI/ML"
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ai(f"Generate 10 real interview questions about {topic} with detailed answers. Mix conceptual and coding.")
    await send(update, f"🎯 *Interview: {topic}*\n\n{reply}")


async def resources(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if await check_limit(update): return
    topic = " ".join(ctx.args)
    if not topic:
        await send(update, "Usage: `/resources <topic>`")
        return
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ai(f"List the best free resources for: {topic}. Include papers, GitHub repos, courses, YouTube, docs.")
    await send(update, f"🔗 *Resources: {topic}*\n\n{reply}")


async def quiz(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if await check_limit(update): return
    topic = " ".join(ctx.args) or "AI/ML"
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ai(f"One challenging MCQ about {topic}. Format: question, A/B/C/D options, answer + explanation.")
    await send(update, f"🧠 *Quiz: {topic}*\n\n{reply}")


async def explain(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if await check_limit(update): return
    term = " ".join(ctx.args)
    if not term:
        await send(update, "Usage: `/explain <term>`  →  e.g. `/explain attention mechanism`")
        return
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ai(f"Explain '{term}': 1) ELI5, 2) technical explanation, 3) analogy, 4) code example.")
    await send(update, f"💡 *Explain: {term}*\n\n{reply}")


async def cheatsheet(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if await check_limit(update): return
    topic = " ".join(ctx.args)
    if not topic:
        await send(update, "Usage: `/cheatsheet <topic>`  →  e.g. `/cheatsheet transformers`")
        return
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ai(f"Create a concise cheat sheet for {topic}. Key formulas, commands, patterns, and gotchas.")
    await send(update, f"📋 *Cheatsheet: {topic}*\n\n{reply}")


async def chat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if await check_limit(update): return
    user_id = update.effective_user.id
    user_input = update.message.text.strip()
    if user_id not in sessions:
        sessions[user_id] = []
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    sessions[user_id].append({"role": "user", "content": user_input})
    try:
        reply = groq_call([{"role": "system", "content": SYSTEM_PROMPT}] + sessions[user_id])
        sessions[user_id].append({"role": "assistant", "content": reply})
        preview = user_input[:45] + ("..." if len(user_input) > 45 else "")
        await send(update, f"```\n▸ {preview}\n```\n\n{reply}")
    except Exception as e:
        sessions[user_id].pop()
        await update.message.reply_text(f"```\n✗ ERROR: {str(e)}\n  Try /clear to reset.\n```", parse_mode="Markdown")


if __name__ == "__main__":
    if not BOT_TOKEN or not GROQ_API_KEY:
        raise ValueError("BOT_TOKEN or GROQ_API_KEY not set")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    for cmd, handler in [
        ("start", start), ("clear", clear), ("help", help_cmd),
        ("commands", commands_cmd), ("roadmap", roadmap), ("notes", notes),
        ("stack", stack), ("architecture", architecture), ("compare", compare),
        ("integrate", integrate), ("deploy", deploy), ("interview", interview),
        ("resources", resources), ("quiz", quiz), ("explain", explain),
        ("cheatsheet", cheatsheet),
    ]:
        app.add_handler(CommandHandler(cmd, handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("AI Terminal Bot v2.0 running...")
    app.run_polling()
