import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === Carica variabili ambiente ===
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TSD_APIKEY = os.getenv("TSD_APIKEY")

# Utility per trovare l'ID di Serie A
SERIE_A_LEAGUE_ID = "4332"
SEASON = "2023-2024"  # aggiorna per la stagione attuale

def get_event_id_by_teams(home, away):
    """
    Cerca l'ID evento della partita (home vs away) prossima in Serie A
    """
    url = f"https://www.thesportsdb.com/api/v1/json/{TSD_APIKEY}/eventsnextleague.php?id={SERIE_A_LEAGUE_ID}"
    res = requests.get(url)
    if res.status_code != 200:
        return None
    events = res.json().get("events", [])
    home, away = home.lower(), away.lower()
    for event in events:
        if home in event['strHomeTeam'].lower() and away in event['strAwayTeam'].lower():
            return event['idEvent']
    return None

def get_past_event_stats(team, limit=5):
    """
    Restituisce statistiche sulle ultime partite della squadra.
    """
    url = f"https://www.thesportsdb.com/api/v1/json/{TSD_APIKEY}/eventslast.php?id={get_team_id_by_name(team)}"
    res = requests.get(url)
    if res.status_code != 200:
        return []
    events = res.json().get("results", [])[:limit]
    stats = {"gol_fatti": 0, "gol_subiti": 0, "goal": 0, "nover": 0, "nmatch": 0}
    for e in events:
        if not e["intHomeScore"] or not e["intAwayScore"]:
            continue
        if e["strHomeTeam"].lower() == team.lower():
            fatti = int(e["intHomeScore"])
            subiti = int(e["intAwayScore"])
        else:
            fatti = int(e["intAwayScore"])
            subiti = int(e["intHomeScore"])
        stats["gol_fatti"] += fatti
        stats["gol_subiti"] += subiti
        if fatti > 0 and subiti > 0:
            stats["goal"] += 1
        if fatti + subiti > 2.5:
            stats["nover"] += 1
        stats["nmatch"] += 1
    return stats

def get_team_id_by_name(team_name):
    # Ottieni l'id squadra (funziona anche se il nome non è preciso)
    url = f"https://www.thesportsdb.com/api/v1/json/{TSD_APIKEY}/searchteams.php?t={team_name}"
    res = requests.get(url)
    if res.status_code != 200:
        return None
    teams = res.json().get("teams", [])
    if teams:
        return teams[0]["idTeam"]
    return None

def analyze_match(home, away):
    """
    Analizza la partita e produce pronostici in base alle statistiche delle ultime 5 partite di entrambe.
    """
    stats_home = get_past_event_stats(home)
    stats_away = get_past_event_stats(away)

    suggerimenti = []
    # Pronostico 1X2 semplice: squadra con miglior rapporto gol fatti/gol subiti
    home_rate = stats_home["gol_fatti"] / stats_home["nmatch"] if stats_home["nmatch"] > 0 else 0
    away_rate = stats_away["gol_fatti"] / stats_away["nmatch"] if stats_away["nmatch"] > 0 else 0

    if home_rate > away_rate + 0.5:
        suggerimenti.append("1 (Vittoria casa consigliata)")
    elif away_rate > home_rate + 0.5:
        suggerimenti.append("2 (Vittoria trasferta consigliata)")
    else:
        suggerimenti.append("X (Pareggio probabile)")

    tot_avg = ((stats_home["gol_fatti"]+stats_away["gol_fatti"])+(stats_home["gol_subiti"]+stats_away["gol_subiti"])) / (stats_home["nmatch"]+stats_away["nmatch"] or 1)
    if tot_avg > 2.8:
        suggerimenti.append("Over 2.5 (tanti gol previsti)")
    elif tot_avg < 2.0:
        suggerimenti.append("Under 2.5 (pochi gol previsti)")

    goal_prob = (stats_home["goal"] + stats_away["goal"]) / ((stats_home["nmatch"]+stats_away["nmatch"]) or 1)
    if goal_prob > 0.7:
        suggerimenti.append("Goal (entrambe segnano)")
    elif goal_prob < 0.4:
        suggerimenti.append("No Goal (almeno una squadra non segna)")

    return suggerimenti[:3]

async def pronostico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /pronostico Napoli-Genoa
    """
    try:
        if not context.args or len(context.args) < 1:
            await update.message.reply_text("Usa: /pronostico SquadraCasa-SquadraTrasferta\nEsempio: /pronostico Napoli-Genoa")
            return
        arg = ' '.join(context.args)
        if "-" not in arg:
            await update.message.reply_text("Scrivi il match con il trattino: Es. Napoli-Genoa")
            return
        home, away = [x.strip() for x in arg.split("-", 1)]
        event_id = get_event_id_by_teams(home, away)
        if not event_id:
            await update.message.reply_text("Partita non trovata tra i prossimi match di Serie A!")
            return
        suggerimenti = analyze_match(home, away)
        await update.message.reply_text(f"Pronostici per {home}-{away}:\n" + "\n".join(f"- {s}" for s in suggerimenti))
    except Exception as ex:
        await update.message.reply_text(f"Errore: {str(ex)}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Usa /pronostico Napoli-Genoa per ricevere i consigli automatici.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pronostico", pronostico))
    print("Bot Telegram pronostici pronto!")
    app.run_polling()

if __name__ == "__main__":
    main()