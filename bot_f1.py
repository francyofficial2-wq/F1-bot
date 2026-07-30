import urllib.request
import json
import datetime
import os
import sys

# Inserto qui il tuo Webhook URL di Discord (oppure impostalo tra le Secret di GitHub)
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1532537113785139200/TaM7NFE7zNGCTk_a7I0cEG9IZlKchv_xLSwYsFOrbTKzGdwzA58aeb3S8pwgEJH3ADrR")
def get_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def send_discord_embed(payload):
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print("Messaggio inviato con successo a Discord!")
    except Exception as e:
        print(f"Errore nell'invio a Discord: {e}")

def main():
    today = datetime.date.today()
    # Calcola il lunedì e la domenica della settimana corrente
    monday = today - datetime.timedelta(days=today.weekday())
    sunday = monday + datetime.timedelta(days=6)

    print(f"Verifica calendario F1 per la settimana: {monday} -> {sunday}")

    # 1. Recupera il calendario F1 della stagione corrente
    schedule_data = get_json("https://api.jolpica.net/ergast/f1/current.json")
    races = schedule_data['MRData']['RaceTable']['Races']

    current_race = None
    for race in races:
        race_date = datetime.datetime.strptime(race['date'], "%Y-%m-%d").date()
        if monday <= race_date <= sunday:
            current_race = race
            break

    # FILTRO FONDAMENTALE: Se non c'è una gara questa settimana, lo script si ferma.
    if not current_race:
        print("Nessun Gran Premio previsto per questa settimana. Nessun messaggio inviato.")
        sys.exit(0)

    race_name = current_race['raceName']
    circuit = current_race['Circuit']['circuitName']
    country = current_race['Circuit']['Location']['country']
    day_of_week = today.weekday() # 0 = Lunedì, 4 = Venerdì, 5 = Sabato, 6 = Domenica

    # 2. LUNEDÌ: Message "RACE WEEK" + Orari
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

        # Aggiungi orario della Gara
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

    # 3. VENERDÌ / SABATO / DOMENICA: Risultati sessioni
    elif day_of_week in [4, 5, 6]:
        # Recupera l'ultimo risultato disponibile
        results_data = get_json("https://api.jolpica.net/ergast/f1/current/last/results.json")
        race_res = results_data['MRData']['RaceTable']['Races'][0]
        
        results_list = race_res['Results'][:5] # Top 5
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
      
