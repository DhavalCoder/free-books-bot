# 📚 Free Programming Books Telegram Bot

A Telegram bot that finds **free and legal** programming books from:
- [EbookFoundation/free-programming-books](https://github.com/EbookFoundation/free-programming-books) (GitHub)
- [Open Library / Internet Archive](https://openlibrary.org)

## Setup

### 1. Get a Telegram Bot Token
1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the token you receive

### 2. Install dependencies
```bash
cd free-books-bot
pip install -r requirements.txt
```

### 3. Configure environment
```bash
copy .env.example .env
```
Edit `.env` and replace `your_telegram_bot_token_here` with your actual token.

### 4. Run the bot
```bash
python bot.py
```

## Usage
- Send any topic: `Python`, `Machine Learning`, `Algorithms`
- Send a book title: `Clean Code`, `The Pragmatic Programmer`
- `/start` — Welcome message
- `/help` — Usage instructions

## Sources
All results are 100% free and legal to read/download.
