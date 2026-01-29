import os
import json
import asyncio
import streamlit as st

def get_or_create_eventloop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

def load_db():
    # Ermittle den Pfad dieses Skripts (client/utils.py)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Wir suchen die db.json relativ zu diesem Skript
    # Struktur: 
    #   /root
    #     /src/db.json
    #     /client/utils.py
    
    paths_to_try = [
        # 1. Standard: Ein Ordner hoch (zu root), dann in src/
        os.path.join(script_dir, "..", "src", "db.json"),
        
        # 2. Fallback: Falls wir im root sind und src/ direkt sehen
        os.path.join(os.getcwd(), "src", "db.json"),
        
        # 3. Fallback: Falls die db.json direkt im client ordner liegt
        os.path.join(script_dir, "db.json")
    ]
    
    for p in paths_to_try:
        # Pfad normalisieren (entfernt ../ usw.)
        full_path = os.path.abspath(p)
        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                return {"error": f"Fehler beim Lesen der DB: {str(e)}"}

    # Wenn nichts gefunden wurde, zeigen wir an, wo wir gesucht haben
    return {"error": f"Database file not found. Searched in: {[os.path.abspath(p) for p in paths_to_try]}"}

@st.cache_data
def load_translations(language):
    try:
        lang_code = "de" if language == "German" else "en"
        filename = f"{lang_code}.json"
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Pfade für Übersetzungen
        paths = [
             os.path.join(script_dir, "..", "translations", filename),
             os.path.join(script_dir, "translations", filename)
        ]
        
        for p in paths:
            if os.path.exists(p):
                 with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
        return {}
    except Exception:
        return {}

def get_text(key):
    # Relies on st.session_state being initialized
    lang = st.session_state.get("language", "German")
    current_translations = load_translations(lang)
    return current_translations.get(key, f"[{key}]")