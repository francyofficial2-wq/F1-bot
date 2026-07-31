import urllib.request
import json
import datetime
import os
import sys
import time

# Webhook Discord configurato
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1532537113785139200/TaM7NFE7zNGCTk_a7I0cEG9IZlKchv_xLSwYsFOrbTKzGdwzA58aeb3S8pwgEJH3ADrR")

MONTHS_IT = {
    1: 'Gennaio', 2: 'Febbraio', 3: 'Marzo', 4: 'Aprile',
    5: 'Maggio', 6: 'Giugno', 7: 'Luglio', 8: 'Agosto',
    9: 'Settembre', 10: 'Ottobre', 11: 'Novembre', 12: 'Dicembre'
}

def get_json(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    req = urllib.request.Request(url, headers=headers)
    
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"Tentativo {attempt}/3 fallito per {url}: {e}")
            if attempt < 3:
                time.sleep(2)
    return None

def send_discord_embed(payload):
    if not WEBHOOK_URL.startswith("https://discord"):
        print("ERRORE CRITICO: URL Webhook Discord non valido!")
        sys.exit(1)
        
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print("Messaggio inviato con successo a Discord!")
    except Exception as e:
        print(f"Errore nell'invio a Discord: {e}")
        sys.exit(1)

def format_date_range(start_date, end_date):
    if start_date.month == end_date.month:
        return f"dal {start_date.day} al {end_date.day} {MONTHS_IT[end_date.month]} {end_date.year}"
    else:
        return f"dal {start_date.day} {MONTHS_IT[start_date.month]} al {end_date.day} {MONTHS_IT[end_date.month]} {end_date.year}"

def main():
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    sunday = monday + datetime.timedelta(days=6)

    print(f"Verifica calendario F1 per la settimana: {monday} -> {sunday}")

    urls_to_try = [
        "https://api.jolpi.ca/ergast/f1/current.json",
        f"https://api.jolpi.ca/ergast/f1/{today.year}.json"
    ]
    
    schedule_data = None
    for url in urls_to_try:
        print(f"Connessione a: {url}")
        schedule_data = get_json(url)
        if schedule_data:
            break

    if not schedule_data:
        print("ERRORE: Impossibile recuperare i dati del calendario F1.")
        sys.exit(1)

    races = schedule_data['MRData']['RaceTable']['Races']

    current_race = None
    next_race = None

    for race in races:
        race_date = datetime.datetime.strptime(race['date'], "%Y-%m-%d").date()
        if monday <= race_date <= sunday:
            current_race = race
            break
        elif race_date > today and next_race is None:
            next_race = race

    # CASE 1: NESSUN GRAN PREMIO QUESTA SETTIMANA -> COUNTDOWN PROSSIMA GARA
    if not current_race:
        print("Nessun Gran Premio questa settimana. Ricerca prossimo Gran Premio...")
        
        if not next_race:
            for race in races:
                race_date = datetime.datetime.strptime(race['date'], "%Y-%m-%d").date()
                if race_date > today:
                    next_race = race
                    break

        if next_race:
            race_name = next_race['raceName']
            circuit = next_race['Circuit']['circuitName']
            country = next_race['Circuit']['Location']['country']
            sunday_date = datetime.datetime.strptime(next_race['date'], "%Y-%m-%d").date()
            
            # Determinazione data di inizio (FP1 se presente, altrimenti venerdì)
            if 'FirstPractice' in next_race and 'date' in next_race['FirstPractice']:
                start_date = datetime.datetime.strptime(next_race['FirstPractice']['date'], "%Y-%m-%d").date()
            else:
                start_date = sunday_date - datetime.timedelta(days=2)
            
            days_left = (start_date - today).days
            date_range_str = format_date_range(start_date, sunday_date)

            payload = {
                "username": "F1 Race Control",
                "avatar_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/F1.svg/512px-F1.svg.png",
                "embeds": [{
                    "title": "💤 Nessuna gara questa settimana",
                    "description": (
                        f"Questa settimana la Formula 1 è in pausa.\n\n"
                        f"🏁 **Prossimo Gran Premio:** {race_name}\n"
                        f"📍 **Circuito:** {circuit} ({country})\n"
                        f"📅 **Date:** {date_range_str}\n"
                        f"⏳ **Countdown:** Mancano **{days_left} giorni** all'inizio del weekend di gara!"
                    ),
                    "color": 3447003, # Azzurro
                    "footer": {"text": "F1 Live Automation System"}
                }]
            }
            send_discord_embed(payload)
            sys.exit(0)
        else:
            print("Nessuna ulteriore gara trovata in calendario per questa stagione.")
            sys.exit(0)

    # CASE 2: C'È UNA GARA QUESTA SETTIMANA
    race_name = current_race['raceName']
    circuit = current_race['Circuit']['circuitName']
    country = current_race['Circuit']['Location']['country']
    day_of_week = today.weekday()

    print(f"Trovata gara questa settimana: {race_name} in {country}")

    # LUNEDÌ: Race Week + Orari
    if day_of_week == 0:
        fields = []
        sessions = [
            ('FirstPractice', '🏎️ Prove Libere 1'),
            ('SecondPractice', '🏎️ Prove Libere 2'),
            ('ThirdPractice', '🏎️ Prove Libere 3'),
            ('SprintQualifying', '⏱️ Qualifiche Sprint'),
            ('Sprint', '⚡ Gara Sprint'),
            ('Qualifying', '⏱️ Qualifiche'),
        ]
        
        for key, label in sessions:
            if key in current_race:
                s_date = current_race[key].get('date', '')
                s_time = current_race[key].get('time', '').replace('Z', ' UTC')
                fields.append({"name": label, "value": f"📅 {s_date} — ⏰ {s_time}", "inline": True})

        race_time = current_race.get('time', '').replace('Z', ' UTC')
        fields.append({"name": "🏁 GARA", "value": f"📅 {current_race['date']} — ⏰ {race_time}", "inline": False})

        payload = {
            "username": "F1 Race Control",
            "avatar_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/F1.svg/512px-F1.svg.png",
            "embeds": [{
                "title": f"🚨 IT'S RACE WEEK! — {race_name}",
                "description": f"Questa settimana la Formula 1 corre in **{country}** sul circuito di **{circuit}**!\nEcco il programma completo del weekend:",
                "color": 14747136,
                "fields": fields,
                "footer": {"text": "F1 Live Automation System"}
            }]
        }
        send_discord_embed(payload)

    # VENERDÌ, SABATO, DOMENICA: Risultati
    elif day_of_week in [4, 5, 6]:
        results_urls = [
            "https://api.jolpi.ca/ergast/f1/current/last/results.json",
            f"https://api.jolpi.ca/ergast/f1/{today.year}/last/results.json"
        ]
        results_data = None
        for r_url in results_urls:
            results_data = get_json(r_url)
            if results_data:
                break
        
        if not results_data or not results_data['MRData']['RaceTable']['Races']:
            print("Nessun risultato ancora disponibile per la sessione.")
            sys.exit(0)

        race_res = results_data['MRData']['RaceTable']['Races'][0]
        results_list = race_res['Results'][:5]
        lines = []
        pos_emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        
        for idx, res in enumerate(results_list):
            driver = f"{res['Driver']['givenName']} {res['Driver']['familyName']}"
            team = res['Constructor']['name']
            lines.append(f"{pos_emojis[idx]} **{driver}** ({team})")

        payload = {
            "username": "F1 Race Control",
            "avatar_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/F1.svg/512px-F1.svg.png",
            "embeds": [{
                "title": f"📊 Risultati Sessione — {race_res['raceName']}",
                "description": "\n".join(lines),
                "color": 14747136,
                "footer": {"text": "Aggiornamento automatico F1"}
            }]
        }
        send_discord_embed(payload)

if __name__ == "__main__":
    main()
    
