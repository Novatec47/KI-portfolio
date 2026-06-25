from flask import Flask, render_template, request, jsonify
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

verlauf = []
nachrichtenanzahl = 0

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    global verlauf, nachrichtenanzahl
    
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
    system="Du bist ein hilfreicher KI-Assistent erstellt von Collin Schmidt. Du heißt nicht ChatGPT und bist kein Produkt von OpenAI. Du wurdest mit der Claude API von Anthropic gebaut. Antworte immer auf Deutsch.",
    messages=verlauf
    )
    
    antwort_text = antwort.content[0].text
    verlauf.append({"role": "assistant", "content": antwort_text})
    
    return jsonify({"antwort": antwort_text})

if __name__ == "__main__":
    app.run(debug=True)