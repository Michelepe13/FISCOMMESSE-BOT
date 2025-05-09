import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === CARICAMENTO DELLE CHIAVI DAL .env ===
load_dotenv()

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TSD_APIKEY       = os.getenv("TSD_APIKEY")           # TheSportsDB
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")     # API-Football su RapidAPI
# Se vorrai un'altra API key, aggiungi altre variabili qui

# === FUNZIONI DI CHIAMATA ALLE API ===

def get_prossime_partite_thesportsdb(count=5, league_id="4332"):
    """Ritorna le prossime partite Serie A da TheSportsDB"""
    url = f"https://www.thesportsdb.com/api/v1/json/{TSD_APIKEY}/eventsnextleague.php?id={league_id}"
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return [f"Errore API TheSportsDB: {r.status_code}"]
        data = r.json().get("events", [])[:count]
        risultato = []
        for m in data:
            casa = m['strHomeTeam']
            trasferta = m['strAwayTeam']
            data_ora = f"{m['dateEvent']} {m['strTime']}"
            risultato.append(f"[TheSportsDB]\n{casa} vs {trasferta}\n{data_ora}")
        return risultato if risultato else ["Nessuna partita trovata su TheSportsDB."]
    except Exception as e:
        return [f"Errore (TheSportsDB): {str(e)}"]

def get_prossime_partite_apifootball(count=5):
    """Ritorna le prossime partite Serie A da API-Football"""
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    headers = {
        "X-RapidAPI-Key": API_FOOTBALL_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    params = {
        "league": "135",   # Serie A
        "season": "2023",  # Anno in corso o aggiorna se necessario
        "next": count
    }
    try:
        r = requests.get(url, headers=headers, params=params)
        if r.status_code != 200:
            return [f"Errore API API-Football: {r.status_code}"]
        fixtures = r.json().get("response", [])
        output = []
        for m in fixtures:
            casa = m['teams']['home']['name']
            trasferta = m['teams']['away']['name']
            data = m['fixture']['date'][:10]
            ora = m['fixture']['date'][11:16]
            output.append(f"[API-Football]\n{casa} vs {trasferta}\n{data} {ora}")
        return output if output else ["Nessuna partita trovata su API-Football."]
    except Exception as e:
        return [f"Errore (API-Football): {str(e)}"]

# # ESEMPIO: QUI ALTRE FUNZIONI PER ALTRE API PUOI AGGIUNGERE
# def get_altro_da_altraapi():
#     api_key = os.getenv("MIA_ALTRA_API_KEY")
#     # ... qui codice ...
#     return ["Risposta dall'altra API"]

# === HANDLER DEI COMANDI TELEGRAM ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao! Bot pronostici multi-API.\n"
        "Comandi disponibili:\n"
        "• /pronostici_thesportsdb – Dati da TheSportsDB\n"
        "• /pronostici_apifootball – Dati da API-Football\n"
        # "• /mioaltrocomando – Dati da altra API\n"
        "Aggiungerò altri comandi su richiesta!"
    )

async def pronostici_thesportsdb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = get_prossime_partite_thesportsdb()
    await update.message.reply_text('\n\n'.join(res))

async def pronostici_apifootball(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = get_prossime_partite_apifootball()
    await update.message.reply_text('\n\n'.join(res))

# # Handler esempio per un'altra API
# async def mioaltrocomando(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     res = get_altro_da_altraapi()
#     await update.message.reply_text('\n'.join(res))

# === AVVIO DEL BOT ===

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pronostici_thesportsdb", pronostici_thesportsdb))
    app.add_handler(CommandHandler("pronostici_apifootball", pronostici_apifootball))
    # app.add_handler(CommandHandler("mioaltrocomando", mioaltrocomando))
    print("Bot Telegram multi-API in esecuzione. Premi CTRL+C per fermare.")
    app.run_polling()

if __name__ == "__main__":
    main()