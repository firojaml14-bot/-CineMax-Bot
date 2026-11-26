
import os
import logging
import requests
from io import BytesIO
from urllib.parse import quote_plus

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

logging.basicConfig(level=logging.INFO)

PLATFORMS = [
    ("Netflix", "https://www.netflix.com/search?q="),
    ("Prime Video", "https://www.primevideo.com/search?phrase="),
    ("JioHotstar", "https://www.hotstar.com/in/search?q="),
    ("ZEE5", "https://www.zee5.com/search?q="),
    ("YouTube Movies", "https://www.youtube.com/results?search_query="),
    ("SonyLIV", "https://www.sonyliv.com/"),
    ("Amazon MX Player", "https://www.mxplayer.in/"),
    ("Apple TV", "https://tv.apple.com/in/search?term="),
    ("Lionsgate Play", "https://lionsgateplay.com/"),
    ("MUBI", "https://mubi.com/"),
    ("Sun NXT", "https://www.sunnxt.com/"),
    ("aha", "https://www.aha.video/"),
    ("Hoichoi", "https://www.hoichoi.tv/"),
    ("ManoramaMAX", "https://www.manoramamax.com/"),
    ("ShemarooMe", "https://www.shemaroome.com/"),
    ("Eros Now", "https://erosnow.com/"),
    ("Airtel Xstream", "https://www.airtelxstream.in/"),
    ("Chaupal", "https://www.chaupal.tv/"),
    ("Discovery+", "https://www.discoveryplus.com/"),
    ("JustWatch", "https://www.justwatch.com/in/search?q="),
    ("hdhub4u","https://new17.hdhub4u.cl/search.html?q=+"),
   ]

def get_movie(name):
    r = requests.get(
        "https://api.themoviedb.org/3/search/movie",
        params={"api_key": TMDB_API_KEY, "query": name},
        timeout=20
    )
    r.raise_for_status()
    results = r.json().get("results", [])
    return results[0] if results else None

def get_keyboard(title, imdb_id=None):
    q = quote_plus(title)
    buttons = [
        [
            InlineKeyboardButton("🎬 Trailer", url=f"https://www.youtube.com/results?search_query={q}+official+trailer"),
            InlineKeyboardButton("⭐ IMDb", url=f"https://www.imdb.com/title/{imdb_id}/" if imdb_id else f"https://www.imdb.com/find/?q={q}")
        ]
    ]

    for i in range(0, len(PLATFORMS), 2):
        row = []
        for name, base in PLATFORMS[i:i+2]:
            url = base + q if "search" in base or "q=" in base or "phrase=" in base or "term=" in base else base
            row.append(InlineKeyboardButton("▶️ " + name, url=url))
        buttons.append(row)

    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Welcome to CineMax!\n\nMovie ka naam bhejo aur details pao."
    )

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    wait = await update.message.reply_text("🔍 Movie search ho rahi hai...")

    try:
        movie = get_movie(name)
        if not movie:
            await wait.edit_text("❌ Movie nahi mili. Dusra naam try karo.")
            return

        title = movie.get("title", name)
        year = (movie.get("release_date") or "Unknown")[:4]
        rating = movie.get("vote_average", 0)
        overview = movie.get("overview") or "Details available nahi hain."

        imdb_id = None
        detail = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie['id']}",
            params={"api_key": TMDB_API_KEY, "append_to_response": "external_ids"},
            timeout=20
        )
        detail.raise_for_status()
        imdb_id = detail.json().get("external_ids", {}).get("imdb_id")

        caption = (
            f"🎬 {title}\n\n"
            f"📅 Release: {year}\n"
            f"⭐ TMDB Rating: {rating}/10\n\n"
            f"📝 {overview[:700]}"
        )
        keyboard = get_keyboard(title, imdb_id)

        poster = movie.get("poster_path")
        if poster:
            image = requests.get(
                "https://image.tmdb.org/t/p/w500" + poster,
                timeout=20
            )
            image.raise_for_status()
            await update.message.reply_photo(
                photo=BytesIO(image.content),
                caption=caption,
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(caption, reply_markup=keyboard)

        await wait.delete()

    except Exception:
        logging.exception("Search error")
        await wait.edit_text("⚠️ Server error. Dobara try karo.")

def main():
    if not BOT_TOKEN or not TMDB_API_KEY:
        print("BOT_TOKEN present:", bool(BOT_TOKEN))
        print("TMDB_API_KEY present:", bool(TMDB_API_KEY))
        raise ValueError("BOT_TOKEN ya TMDB_API_KEY missing hai.")
    

    

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    print("CineMax started")
    app.run_polling()

if __name__ == "__main__":
    main()
