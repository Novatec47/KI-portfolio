import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

print("Chatbot gestartet. Tippe 'beenden' um zu stoppen.\n")

verlauf = []
zusammenfassung = ""
nachrichtenanzahl = 0

while True:
    eingabe = input("Du: ")
    
    if eingabe.lower() == "beenden":
        print("Tschüss!")
        break
    
    nachrichtenanzahl += 1
    verlauf.append({"role": "user", "content": eingabe})
    
    if nachrichtenanzahl % 6 == 0:
        zusammenfassung_antwort = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=verlauf + [{"role": "user", "content": "Fasse unser bisheriges Gespräch in 3 prägnanten Sätzen zusammen."}]
        )
        zusammenfassung = zusammenfassung_antwort.content[0].text
        verlauf = [{"role": "user", "content": f"Zusammenfassung unseres bisherigen Gesprächs: {zusammenfassung}"},
                   {"role": "assistant", "content": "Verstanden, ich habe den bisherigen Kontext."}]
        print("\n[Gesprächsverlauf automatisch zusammengefasst]\n")
    
    antwort = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=verlauf
    )
    
    antwort_text = antwort.content[0].text
    verlauf.append({"role": "assistant", "content": antwort_text})
    
    print(f"\nClaude: {antwort_text}\n")