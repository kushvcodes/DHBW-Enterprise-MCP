import json
import asyncio
import httpx
import google.generativeai as genai
from mcp import ClientSession
from mcp.client.sse import sse_client

from config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, USE_DEEPSEEK, 
    GOOGLE_API_KEY, GEMINI_MODEL, MCP_URL, REAL_DB_NEWS, 
    DEEPSEEK_MODEL
)

if not USE_DEEPSEEK and GOOGLE_API_KEY: 
    genai.configure(api_key=GOOGLE_API_KEY)

async def call_deepseek_model(prompt_text: str, model_name: str, api_key: str):
    if not api_key: return "Error: DEEPSEEK_API_KEY not found."
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    messages = [{"role": "user", "content": prompt_text}]
    payload = {"model": model_name, "messages": messages}
    async with httpx.AsyncClient(base_url=DEEPSEEK_BASE_URL) as client:
        response = await client.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload, timeout=60.0)
        if response.status_code != 200: return f"Error {response.status_code}: {response.text}"
        return response.json()["choices"][0]["message"]["content"]

async def execute_mcp_pipeline(prompt_text, language="German"):
    trace_steps = []
    final_response = ""
    try:
        async with sse_client(MCP_URL) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                trace_steps.append({
                    "step": 1, "icon": "🔌", "title": "Verbindung & Handshake",
                    "simple_desc": "Der Client (Chatbot) verbindet sich via SSE-Protokoll mit dem DHBW-Enterprise Server.",
                    "visual_type": "status", "data": {"status": "Connected", "protocol": "JSON-RPC 2.0"}
                })
                
                tool_response = await session.list_tools()
                tools_list = [{"Tool Name": t.name, "Funktion": t.description[:60]+"..."} for t in tool_response.tools]
                
                trace_steps.append({
                    "step": 2, "icon": "🧰", "title": "Discovery (Werkzeug-Erkennung)",
                    "simple_desc": f"Der Server meldet {len(tool_response.tools)} verfügbare Fähigkeiten.",
                    "visual_type": "table", "data": tools_list, "raw_data": tool_response.tools
                })
                
                tools_for_prompt = [{"name": t.name, "description": t.description, "input_schema": t.inputSchema} for t in tool_response.tools]
                
                router_prompt = f"""
                You are the DHBW System Router. Language: {language}.
                Query: "{prompt_text}"
                TOOLS: {json.dumps(tools_for_prompt, indent=2)}
                RESOURCES: 
                - dhbw://syllabus/{{module_key}} (e.g. 'intsem', 'webeng', 'cloud', 'datasci' based on db.json)
                - dhbw://news/{{news_id}}
                
                OUTPUT JSON ONLY: {{ "action": "tool|resource|chat", "name|uri": "...", "reasoning": "...", "args": {{...}} }}
                """
                
                if USE_DEEPSEEK: raw_response = await call_deepseek_model(router_prompt, DEEPSEEK_MODEL, DEEPSEEK_API_KEY)
                else: 
                    model = genai.GenerativeModel(GEMINI_MODEL)
                    raw_response = (await model.generate_content_async(router_prompt)).text
                
                try: decision = json.loads(raw_response.replace("```json","").replace("```", "").strip())
                except: decision = {"action": "chat", "response": raw_response}
                
                trace_steps.append({
                    "step": 3, "icon": "🧠", "title": "Router (LLM Entscheidung)",
                    "simple_desc": f"Das KI-Modell analysiert Ihre Absicht. Es entscheidet sich für die Aktion **'{decision.get('action')}'**.",
                    "visual_type": "decision", "data": decision
                })
                
                execution_data = ""
                if decision.get("action") == "resource":
                    uri = decision.get("uri", decision.get("name", "N/A"))
                    try:
                        res = await session.read_resource(uri)
                        execution_data = res.contents[0].text if res.contents else "Resource Empty."
                        trace_steps.append({
                            "step": 4, "icon": "📄", "title": "Resource Fetch",
                            "simple_desc": f"Der Server lädt den Inhalt der Ressource '{uri}' aus der Datenbank.",
                            "visual_type": "code", "data": execution_data
                        })
                    except Exception as e:
                        execution_data = f"Error reading resource: {e}"
                        trace_steps.append({"step": 4, "icon": "❌", "title": "Resource Error", "simple_desc": "Fehler beim Laden", "visual_type": "error", "data": str(e)})

                elif decision.get("action") == "tool":
                    tool_name = decision.get("name", "N/A")
                    args = decision.get("args", {})
                    try:
                        res = await session.call_tool(tool_name, args)
                        execution_data = res.content[0].text if res.content else "No output."
                        trace_steps.append({
                            "step": 4, "icon": "⚡", "title": "Ausführung (Backend)",
                            "simple_desc": f"Der Server führt den Python-Code für '{tool_name}' aus.",
                            "visual_type": "code", "data": execution_data
                        })
                    except Exception as e: execution_data = f"Error: {e}"
                
                elif decision.get("action") == "chat":
                    execution_data = decision.get("response", "")
                    trace_steps.append({
                        "step": 4, "icon": "💬", "title": "Direkte Antwort",
                        "simple_desc": "Keine Datenbank-Abfrage notwendig.",
                        "visual_type": "text", "data": execution_data
                    })
                
                final_prompt = f"""Role: University Assistant. Lang: {language}. User: "{prompt_text}". Data: {execution_data}. Task: Answer nicely and professionally. Use Markdown."""
                if USE_DEEPSEEK: final_response = await call_deepseek_model(final_prompt, DEEPSEEK_MODEL, DEEPSEEK_API_KEY)
                else: 
                    model = genai.GenerativeModel(GEMINI_MODEL)
                    final_response = (await model.generate_content_async(final_prompt)).text
    except Exception as e:
        trace_steps.append({"step": 0, "title": "Fehler", "simple_desc": "Systemfehler", "visual_type": "error", "data": str(e)})
        final_response = "Es ist ein Fehler aufgetreten."
    return trace_steps, final_response

async def simulate_news_pipeline(query):
    await asyncio.sleep(1.5)
    trace_steps = []
    
    trace_steps.append({
        "step": 1, "icon": "🔌", "title": "Verbindung & Handshake",
        "simple_desc": "Verbindung via SSE. Protokoll-Version 2.0 etabliert.",
        "visual_type": "status", "data": {"status": "Connected", "protocol": "JSON-RPC 2.0"}
    })
    
    tools = [
        {"Tool Name": "get_university_news", "Funktion": "Get latest news filtered by category."},
        {"Tool Name": "get_student_grades", "Funktion": "Fetches grades..."}
    ]
    trace_steps.append({
        "step": 2, "icon": "🧰", "title": "Discovery (Simulation)",
        "simple_desc": "Der Server meldet (simuliert) das neue Tool 'get_university_news'.",
        "visual_type": "table", "data": tools, 
        "raw_data": [{"name": "get_university_news", "inputSchema": {"type": "object", "properties": {"category": {"type": "string"}}}}]
    })

    trace_steps.append({
        "step": 3, "icon": "🧠", "title": "Router (LLM Entscheidung)",
        "simple_desc": "Das KI-Modell wählt das neue Tool.",
        "visual_type": "decision", "data": {
            "action": "tool", "name": "get_university_news", "args": {"category": "Campus Life"}, 
            "reasoning": "User asks for campus news."
        }
    })

    filtered_news = [n for n in REAL_DB_NEWS if n['category'] == "Campus Life"]
    execution_data_json = json.dumps(filtered_news, indent=2)
    
    trace_steps.append({
        "step": 4, "icon": "⚡", "title": "Ausführung (Simuliert)",
        "simple_desc": "Das Tool gibt echte Daten aus der Datenbank zurück.",
        "visual_type": "code", "data": execution_data_json
    })

    final_res = f"**Aktuelle Campus-News:**\n\n"
    for news in filtered_news:
        final_res += f"- **{news['headline']}** ({news['date']}): {news['body']}\n"
    
    return trace_steps, final_res

async def verify_real_server_has_tool():
    try:
        async with sse_client(MCP_URL) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                response = await session.list_tools()
                tool_names = [t.name for t in response.tools]
                
                if "get_university_news" in tool_names:
                    return True, "Tool 'get_university_news' gefunden! Gute Arbeit."
                else:
                    return False, f"Tool nicht gefunden. Gefundene Tools: {', '.join(tool_names)}"
    except Exception as e:
        return False, f"Verbindung fehlgeschlagen: {str(e)}. Läuft der Server?"
    
# --- NEW: RESOURCE VERIFICATION (FIXED) ---
async def verify_real_server_has_resource(resource_pattern):
    try:
        async with sse_client(MCP_URL) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                response = await session.list_resources()
                
                # FIX: Explicitly convert AnyUrl to string to prevent TaskGroup errors
                found = False
                uris = []
                for res in response.resources:
                    # Convert AnyUrl object to string for comparison
                    uri_str = str(res.uri)
                    uris.append(uri_str)
                    if resource_pattern in uri_str:
                        found = True
                        break
                
                if found:
                    return True, f"Resource mit Pattern '{resource_pattern}' gefunden!"
                else:
                    short_uris = ", ".join(uris[:3]) + "..." if uris else "Keine"
                    return False, f"Resource '{resource_pattern}' nicht gefunden. Verfügbar: {short_uris}"
    except Exception as e:
        # Catch and simplify TaskGroup errors
        msg = str(e)
        if "TaskGroup" in msg:
            msg = "Fehler beim Verarbeiten der Antwort (TaskGroup Error). Aber Server ist erreichbar."
        return False, f"Fehler: {msg}"
    

async def simulate_security_check(attack_prompt):
    await asyncio.sleep(1.0)
    trace_steps = []
    
    # Step 1: Input
    trace_steps.append({
        "step": 1, "icon": "😈", "title": "Malicious Input", 
        "simple_desc": f"User versucht: '{attack_prompt}'", 
        "visual_type": "status", "data": {"intent": "unauthorized_action"}
    })

    # Step 2: Router Analysis
    trace_steps.append({
        "step": 2, "icon": "🧠", "title": "Router (LLM)", 
        "simple_desc": "Das LLM analysiert den Prompt. Es sucht nach passenden Tools.", 
        "visual_type": "decision", "data": {
            "action": "unknown", 
            "reasoning": "User wants to DELETE/UPDATE data. No tool exists for 'delete_grades' or 'execute_sql'.",
            "safety_flag": True
        }
    })

    # Step 3: Zod/System Rejection
    trace_steps.append({
        "step": 3, "icon": "🛡️", "title": "MCP Gatekeeper", 
        "simple_desc": "Der Server lehnt die Anfrage ab. Keine passende Funktion im Schema gefunden.", 
        "visual_type": "error", "data": "Error: Tool not found or Operation not permitted by Schema."
    })

    final_res = "🚫 **I cannot fulfill this request.** I only have read-access to grades, schedules, and news. I cannot modify data."
    return trace_steps, final_res

# --- NEW: SIMULATE CHAINING (MULTI-HOP) ---
async def simulate_chaining_pipeline():
    await asyncio.sleep(1.0)
    trace_steps = []
    
    trace_steps.append({
        "step": 1, "icon": "🤔", "title": "Planung (Chain of Thought)", 
        "simple_desc": "Zerlege die komplexe Frage: 'Wann hat der Prof meiner schlechtesten Note Vorlesung?'", 
        "visual_type": "status", "data": {
            "sub_goal_1": "Finde schlechteste Note & Professor.",
            "sub_goal_2": "Finde Stundenplan dieses Professors."
        }
    })

    # FIXED: Added "action": "tool" and "name" to match UI requirements
    trace_steps.append({
        "step": 2, "icon": "🛠️", "title": "Hop 1: get_student_grades", 
        "simple_desc": "Suche Noten für s1001...", 
        "visual_type": "decision", 
        "data": {"action": "tool", "name": "get_student_grades", "args": {"query": "s1001"}}
    })
    
    grades_extract = [
        {"module": "Web Eng", "grade": 1.3, "prof": "Harsh"},
        {"module": "Math", "grade": 5.0, "prof": "Weber"}
    ]
    trace_steps.append({
        "step": 3, "icon": "📉", "title": "Zwischenergebnis", 
        "simple_desc": "Analyse: Schlechteste Note ist 5.0 in Mathe bei Prof. Weber.", 
        "visual_type": "code", "data": json.dumps(grades_extract, indent=2)
    })

    # FIXED: Added "action": "tool" and "name"
    trace_steps.append({
        "step": 4, "icon": "🛠️", "title": "Hop 2: get_schedule", 
        "simple_desc": "Suche nun den Stundenplan für Mathe/Weber.", 
        "visual_type": "decision", 
        "data": {"action": "tool", "name": "get_schedule", "args": {"course_name": "Informatik"}}
    })

    trace_steps.append({
        "step": 5, "icon": "✅", "title": "Synthese", 
        "simple_desc": "Prof. Weber liest 'Calculus II' am Donnerstag um 09:00 Uhr.", 
        "visual_type": "status", "data": {"answer_found": True}
    })

    final_res = "Deine schlechteste Note ist eine **5.0** in Mathe bei **Dr. E. Weber**. \n\nSeine nächste Vorlesung ('Calculus II') findet am **Donnerstag von 09:00 - 12:15** in Raum C.4.10 statt. Vielleicht solltest du hingehen? 😉"
    return trace_steps, final_res