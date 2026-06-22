import os
import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

GITHUB_SEARCH_URL = "https://api.github.com/search/code"
OPEN_LIBRARY_URL = "https://openlibrary.org/search.json"

TOPICS = [
    ["🐍 Python", "☕ Java", "🌐 JavaScript"],
    ["🤖 AI / Machine Learning", "📊 Data Science", "🧠 Deep Learning"],
    ["☁️ Cloud / AWS", "🐳 Docker / DevOps", "🔐 Cybersecurity"],
    ["⚛️ React", "🖥️ Linux", "🗄️ Databases"],
    ["📱 Flutter / Mobile", "🦀 Rust", "🐹 Go"],
    ["🧮 Algorithms", "🏗️ System Design", "🔧 C / C++"],
]


def topic_keyboard():
    keyboard = []
    for row in TOPICS:
        keyboard.append([
            InlineKeyboardButton(t, callback_data=t.split(" ", 1)[1])
            for t in row
        ])
    keyboard.append([InlineKeyboardButton("🔍 Search Custom Topic", callback_data="__custom__")])
    return InlineKeyboardMarkup(keyboard)


def search_books(query: str) -> str:
    gh, ol = [], []

    try:
        r = requests.get(GITHUB_SEARCH_URL,
                         params={"q": f"{query} repo:EbookFoundation/free-programming-books", "per_page": 5},
                         headers={"Accept": "application/vnd.github+json"}, timeout=8)
        gh = [{"title": i["name"].replace(".md", ""), "url": i["html_url"]}
              for i in r.json().get("items", [])[:5]]
    except Exception:
        pass

    try:
        r = requests.get(OPEN_LIBRARY_URL,
                         params={"q": query, "fields": "title,author_name,ia,has_fulltext", "limit": 5},
                         timeout=8)
        for doc in r.json().get("docs", []):
            if doc.get("has_fulltext") and doc.get("ia"):
                ia_id = doc["ia"][0] if isinstance(doc["ia"], list) else doc["ia"]
                ol.append({
                    "title": doc.get("title", "Unknown"),
                    "author": ", ".join(doc.get("author_name", ["Unknown"])),
                    "url": f"https://archive.org/details/{ia_id}",
                })
    except Exception:
        pass

    if not gh and not ol:
        return "😕 No results found. Try a different topic."

    lines = [f"📖 *Free books for: {query}*\n"]
    if gh:
        lines.append("*From Free Programming Books (GitHub):*")
        for b in gh:
            lines.append(f"• [{b['title']}]({b['url']})")
    if ol:
        lines.append("\n*From Open Library / Internet Archive:*")
        for b in ol:
            lines.append(f"• [{b['title']}]({b['url']}) — _{b['author']}_")
    lines.append("\n_All books are free and legal_ ✅")
    return "\n".join(lines)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *Free Programming Books Bot*\n\nChoose a topic or search for anything:",
        parse_mode="Markdown",
        reply_markup=topic_keyboard(),
    )


async def menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Choose a topic:",
        reply_markup=topic_keyboard(),
    )


async def button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "__custom__":
        await query.message.reply_text("✏️ Type any topic or book name to search:")
        return

    await query.message.reply_text(f"🔍 Searching *{query.data}*...", parse_mode="Markdown")
    result = search_books(query.data)
    await query.message.reply_text(result, parse_mode="Markdown", disable_web_page_preview=True)
    await query.message.reply_text("Choose another topic:", reply_markup=topic_keyboard())


async def search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    if not query:
        return
    await update.message.reply_text(f"🔍 Searching *{query}*...", parse_mode="Markdown")
    result = search_books(query)
    await update.message.reply_text(result, parse_mode="Markdown", disable_web_page_preview=True)
    await update.message.reply_text("Search another topic:", reply_markup=topic_keyboard())


if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("BOT_TOKEN not set")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    print("Bot is running...")
    app.run_polling()
