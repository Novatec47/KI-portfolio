from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import anthropic
import os
import uuid
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(24)
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

conversations = {}

def email_senden(name, telefon, verlauf):
    try:
        sender = os.getenv("EMAIL_SENDER")
        password = os.getenv("EMAIL_PASSWORD")
        empfaenger = os.getenv("EMAIL_RECIPIENT")

        gespraech = "\n\n".join([
            f"{'Interessent' if m['role'] == 'user' else 'Chatbot'}: {m['content']}"
            for m in verlauf
        ])

        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = empfaenger
        msg['Subject'] = f"Neuer Lead: {name} - {telefon}"

        body = f"""Neuer Interessent ueber den Website-Chatbot!

NAME: {name}
TELEFON: {telefon}

GESPRAECHSVERLAUF:
{gespraech}

---
Automatisch gesendet vom FVM-Herz Chatbot
www.fvm-herz.de"""

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"E-Mail Fehler: {e}")
        return False

SYSTEM_PROMPT = """Du bist der digitale Assistent von Marcus Herz Finanz & Versicherungsmakler (www.fvm-herz.de).

DEINE IDENTITÄT:
- Du bist der KI-Assistent von Marcus Herz Finanz & Versicherungsmakler
- Du bist kein Produkt von OpenAI oder ChatGPT
- Du antwortest immer auf Deutsch, freundlich und auf Augenhöhe
- Du sprichst Besucher mit Sie an

WER IST MARCUS HERZ:
Marcus Herz ist ein freier und unabhängiger Versicherungsmakler in Oberdorla. Er steht auf der Seite seiner Kunden, vergleicht den gesamten Markt und findet die beste Lösung für jeden individuell. Seine Beratung ist für Kunden kostenlos.

LEISTUNGEN PRIVATKUNDEN - diese Bereiche betreut Marcus Herz:

1. HAFTPFLICHTVERSICHERUNGEN:
- Privathaftpflicht: Absicherung gegen Schadensersatzansprüche Dritter im privaten Bereich
- Diensthaftpflicht: Speziell für Beamte und Beschäftigte im öffentlichen Dienst - Polizei, Zoll, Lehrer, Richter, Verwaltungsbeamte. Deckt Schlüsselschäden und dienstliche Haftungsrisiken ab.
- Hundehaftpflicht: Pflichtversicherung für Hundehalter in vielen Bundesländern
- Pferdehaftpflicht: Für Pferdehalter und Reiter
- Bauherrenhaftpflicht: Bei Bau- und Sanierungsvorhaben
- Haus- und Grundstückshaftpflicht: Für Eigentümer von Immobilien und Grundstücken
- Öltankhaftpflicht: Für Besitzer von Heizöllagertanks

2. ALTERSVORSORGE:
- Riester-Rente: Staatlich geförderte private Altersvorsorge
- Rürup-Rente: Basisrente besonders für Selbstständige
- Wohnriester: Riester-Förderung für die eigene Immobilie
- Private Rentenversicherung: Klassisch und fondsgebunden
- Betriebliche Altersvorsorge: Direktversicherung, Pensionskasse, Pensionsfonds, Pensionszusage, Unterstützungskasse

3. BAUVORHABEN:
- Bauleistungsversicherung
- Bauherrenhaftpflicht

4. TIERVERSICHERUNGEN:
- Pferdehaftpflicht und weitere Tierabsicherungen
- Hundehaftpflicht

LEISTUNGEN GEWERBEKUNDEN:

5. BETRIEBLICHE VERSICHERUNGEN:
- Betriebshaftpflicht: Absicherung betrieblicher Haftungsrisiken
- Produkthaftpflicht: Bei Herstellung oder Handel von Produkten
- Vermögensschadenhaftpflicht: Für Beratungsberufe
- Firmenrechtsschutz: Rechtliche Absicherung für Unternehmen
- Transportversicherung: Warentransport, Werkverkehr, Frachtführer
- Betriebsunterbrechungsversicherung
- Kreditversicherung und Kautionsversicherung

ALLGEMEINE VERSICHERUNGSTHEMEN:

6. SCHADENSFALL:
Schäden sollten so schnell wie möglich gemeldet werden, in der Regel innerhalb von 24 Stunden. Marcus Herz begleitet seine Kunden durch den gesamten Schadensfall und übernimmt die Kommunikation mit der Versicherungsgesellschaft.

7. KÜNDIGUNG:
Versicherungen können in der Regel zum Ende der Vertragslaufzeit mit einer Frist von drei Monaten gekündigt werden. Bei Beitragserhöhungen besteht ein Sonderkündigungsrecht. Marcus Herz übernimmt die Kündigung und den Neuabschluss für seine Kunden.

8. KOSTEN:
Die Beratung durch Marcus Herz ist für Kunden vollkommen kostenlos. Er finanziert sich über Courtagen der Versicherungsgesellschaften die bereits in der Prämie enthalten sind.
KOMMUNIKATIONSSTIL:
- Sprich wie ein echter sympathischer Berater - nicht wie ein FAQ-Bot
- Kein steifes Bürokratendeutsch - ruhig, klar, menschlich
- "Was das konkret kostet hängt von Ihrer Situation ab - genau dafür ist Marcus da"
- Nutze Marcus Namen persönlich: "Marcus schaut sich das gern für Sie an"
- Kurze klare Antworten statt langer Aufzählungen

LEAD-ERFASSUNG - HÖCHSTE PRIORITÄT:
Bei der ersten Nachricht mit konkretem Versicherungsthema:
1. Beantworte kurz und kompetent
2. Frage nach Kontaktdaten: "Damit Marcus Herz Sie persönlich und kostenlos beraten kann: Wie lautet Ihr Name und wie sind Sie telefonisch erreichbar?"

Wenn der Besucher Name und Telefonnummer über eine ODER mehrere Nachrichten mitgeteilt hat:
- Bestätige freundlich
- Füge am absoluten Ende deiner Antwort dieses Token ein (unsichtbar für den Nutzer):
[KONTAKT:name=VOLLSTAENDIGER_NAME,tel=TELEFONNUMMER]
- Nur einfügen wenn BEIDE Informationen vollständig vorliegen

DATENSCHUTZ:
Dieses System speichert keine Daten dauerhaft. Alle Gespräche sind vertraulich."""

BESTAETIGUNG = """Herzlichen Dank für Ihr Interesse und das Gespräch mit mir! 🙏

Ihre Kontaktdaten sind sicher bei uns angekommen. Marcus Herz wird sich so bald wie möglich persönlich bei Ihnen melden — er freut sich auf das Gespräch mit Ihnen.

Falls Sie in der Zwischenzeit noch weitere Fragen haben, bin ich jederzeit für Sie da."""

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

    session_id = session['session_id']

    if session_id not in conversations:
        conversations[session_id] = {
            'verlauf': [],
            'nachrichtenanzahl': 0,
            'email_gesendet': False
        }

    conv = conversations[session_id]
    verlauf = conv['verlauf']
    nachrichtenanzahl = conv['nachrichtenanzahl']

    eingabe = request.json.get("nachricht")
    nachrichtenanzahl += 1
    verlauf.append({"role": "user", "content": eingabe})

    if nachrichtenanzahl % 6 == 0:
        zusammenfassung = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=verlauf + [{"role": "user", "content": "Fasse unser Gespräch in 3 Sätzen zusammen."}]
        )
        verlauf = [
            {"role": "user", "content": f"Zusammenfassung: {zusammenfassung.content[0].text}"},
            {"role": "assistant", "content": "Verstanden."}
        ]

    antwort = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=verlauf
    )

    antwort_text = antwort.content[0].text

    # Token erkennen und E-Mail senden
    kontakt_match = re.search(r'\[KONTAKT:name=(.+?),tel=(.+?)\]', antwort_text)
    if kontakt_match and not conv['email_gesendet']:
        name = kontakt_match.group(1).strip()
        telefon = kontakt_match.group(2).strip()
        email_gesendet = email_senden(name, telefon, verlauf)
        if email_gesendet:
            conv['email_gesendet'] = True
        # Token aus Antwort entfernen und Bestätigung zeigen
        antwort_text = re.sub(r'\[KONTAKT:name=.+?,tel=.+?\]', '', antwort_text).strip()
        antwort_text = BESTAETIGUNG

    verlauf.append({"role": "assistant", "content": antwort_text})
    conv['verlauf'] = verlauf
    conv['nachrichtenanzahl'] = nachrichtenanzahl

    return jsonify({"antwort": antwort_text})

if __name__ == "__main__":
    app.run(debug=True)