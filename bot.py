import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

GITHUB_SEARCH_URL = "https://api.github.com/search/code"
OPEN_LIBRARY_URL = "https://openlibrary.org/search.json"


def search_github_books(query: str) -> list:
    params = {"q": f"{query} repo:EbookFoundation/free-programming-books", "per_page": 5}
    headers = {"Accept": "application/vnd.github+json"}
    try:
        r = requests.get(GITHUB_SEARCH_URL, params=params, headers=headers, timeout=8)
        return [{"title": i["name"].replace(".md", ""), "url": i["html_url"]}
                for i in r.json().get("items", [])[:5]]
    except Exception:
        return []


def search_open_library(query: str) -> list:
    params = {"q": query, "fields": "title,author_name,ia,has_fulltext", "limit": 5}
    try:
        r = requests.get(OPEN_LIBRARY_URL, params=params, timeout=8)
        results = []
        for doc in r.json().get("docs", []):
            if doc.get("has_fulltext") and doc.get("ia"):
                ia_id = doc["ia"][0] if isinstance(doc["ia"], list) else doc["ia"]
                results.append({
                    "title": doc.get("title", "Unknown"),
                    "author": ", ".join(doc.get("author_name", ["Unknown"])),
                    "url": f"https://archive.org/details/{ia_id}",
                })
        return results
    except Exception:
        return []


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *Free Programming Books Bot*\n\n"
        "Send me any topic or book title and I'll find *free & legal* resources.\n\n"
        "Examples: `Python`, `Algorithms`, `Linux`, `Clean Code`",
        parse_mode="Markdown",
    )


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Just type a topic and I'll search:\n"
        "• *EbookFoundation/free-programming-books* (GitHub)\n"
        "• *Open Library / Internet Archive*\n\nAll results are free and legal ✅",
        parse_mode="Markdown",
    )


async def search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    if not query:
        return
    await update.message.reply_text(f"🔍 Searching for *{query}*...", parse_mode="Markdown")

    gh = search_github_books(query)
    ol = search_open_library(query)

    if not gh and not ol:
        await update.message.reply_text(
            "😕 No results found. Try: `Python`, `Linux`, `Algorithms`",
            parse_mode="Markdown",
        )
        return

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

    await update.message.reply_text(
        "\n".join(lines), parse_mode="Markdown", disable_web_page_preview=True
    )


if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("BOT_TOKEN not set")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    print("Bot is running...")
    app.run_polling()
