import urllib.request
import json
import datetime
import os
import sys
import time

# Webhook Discord configurato
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1532537113785139200/TaM7NFE7zNGCTk_a7I0cEG9IZlKchv_xLSwYsFOrbTKzGdwzA58aeb3S8pwgEJH3ADrR")

def get_json(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    req = urllib.request.Request(url, headers=headers)
    
    # Riprova fino a 3 volte in caso di micro-interruzione DNS/rete
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"Tentativo {attempt}/3 fallito per {url}: {e}")
            if attempt < 3:
                time.sleep(3)
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

def main():
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    sunday = monday + datetime.timedelta(days=6)

    print(f"Verifica calendario F1 per la settimana: {monday} -> {sunday}")

    urls_to_try = [
        "https://api.jolpica.net/ergast/f1/current.json",
        f"https://api.jolpica.net/ergast/f1/{today.year}.json"
    ]
    
    schedule_data = None
    for url in urls_to_try:
        print(f"Connessione a: {url}")
        schedule_data = get_json(url)
        if schedule_data:
            break

    if not schedule_data:
        print("ERRORE: Impossibile recuperare i dati del calendario F1 dopo tutti i tentativi.")
        sys.exit(1)

    races = schedule_data['MRData']['RaceTable']['Races']

    current_race = None
    for race in races:
        race_date = datetime.datetime.strptime(race['date'], "%Y-%m-%d").date()
        if monday <= race_date <= sunday:
            current_race = race
            break

    if not current_race:
        print("Nessun Gran Premio previsto per questa settimana. Nessun messaggio inviato.")
        sys.exit(0)

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
            "https://api.jolpica.net/ergast/f1/current/last/results.json",
            f"https://api.jolpica.net/ergast/f1/{today.year}/last/results.json"
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
    
