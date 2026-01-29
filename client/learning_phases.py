import streamlit as st
import json
import random
# WICHTIG: Hier müssen SECURITY_SCENARIOS und CHAIN_SCENARIO importiert werden!
from config import SAMPLE_TOOL_DEF, SAMPLE_RESOURCE_DEF, LEARNING_SCENARIOS, SECURITY_SCENARIOS, CHAIN_SCENARIO
from backend_logik import (
    execute_mcp_pipeline, simulate_news_pipeline, verify_real_server_has_tool, 
    verify_real_server_has_resource, simulate_security_check, simulate_chaining_pipeline
)
from ui_components import render_learning_step
from utils import get_or_create_eventloop

# === PHASE 1: INTRO ===
def render_intro_phase():
    st.markdown("---")
    st.subheader("🎓 Phase 1: Die Infrastruktur verstehen")
    
    server_class = "node-icon"
    packet_html = '<div class="packet packet-request">⚡</div>'
    if st.session_state.show_tool_sample:
        server_class += " server-active"
        packet_html = '<div class="packet packet-response">🆔</div>'
    elif st.session_state.show_resource_sample:
        server_class += " server-active"
        packet_html = '<div class="packet packet-response">📄</div>'

    st.markdown(f"""
    <div class="diagram-container">
        <div class="node"><div class="node-icon">🤖</div><div class="node-label">Client (KI)</div></div>
        <div class="connection-line">{packet_html}</div>
        <div class="node"><div class="{server_class}">🖥️</div><div class="node-label">MCP Server</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Erklärung:** Der Server blinkt und antwortet, wenn du unten ein Feature auswählst.")
    col_t, col_r = st.columns(2)
    with col_t:
        st.markdown('<div class="action-btn">', unsafe_allow_html=True)
        if st.button("🛠️ Fach 1: Tools (Werkzeuge)", use_container_width=True):
            st.session_state.show_tool_sample = True
            st.session_state.show_resource_sample = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with col_r:
        st.markdown('<div class="action-btn">', unsafe_allow_html=True)
        if st.button("📄 Fach 2: Resources (Notizen)", use_container_width=True):
            st.session_state.show_tool_sample = False
            st.session_state.show_resource_sample = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.show_tool_sample:
        st.markdown("""<div class="feature-box"><h3>🛠️ Das Tool-Fach (Actions)</h3><p>Hier liegen Werkzeuge. Ein Tool ist eine <b>Aktion</b>, die der Server ausführen kann. <br><i>Beispiel: "Berechne eine Note" oder "Sende eine E-Mail".</i><br><b>Rückgabe:</b> Eine ID oder ein Statuswert.</p></div>""", unsafe_allow_html=True)
        st.code(json.dumps(SAMPLE_TOOL_DEF, indent=2), language="json")
    if st.session_state.show_resource_sample:
        st.markdown("""<div class="feature-box"><h3>📄 Das Resource-Fach (Knowledge)</h3><p>Hier liegt Wissen. Eine Resource ist wie eine <b>Datei</b>, die die KI lesen kann. <br><i>Beispiel: "Ein Lehrplan PDF" oder "Die Mensa-Speisekarte".</i><br><b>Rückgabe:</b> Der volle Textinhalt.</p></div>""", unsafe_allow_html=True)
        st.code(json.dumps(SAMPLE_RESOURCE_DEF, indent=2), language="json")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="result-btn">', unsafe_allow_html=True)
    if st.button("Wie kommen die Daten rüber? (Transport) ➡️", type="primary", use_container_width=True):
        st.session_state.learning_phase = "transports"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# === PHASE 1b: TRANSPORTS ===
def render_transports_phase():
    st.markdown("---")
    st.subheader("🎓 Phase 1b: Transport-Ebenen")
    st.info("MCP funktioniert überall. Aber wie reisen die Daten? Wähle einen Modus:")

    cols = st.columns(3)
    if cols[0].button("1. Stdio (Lokal)"): st.session_state.selected_transport = "stdio"
    if cols[1].button("2. SSE (Web)"): st.session_state.selected_transport = "sse"
    if cols[2].button("3. Cloud (Remote)"): st.session_state.selected_transport = "cloud"

    if st.session_state.selected_transport == "stdio":
        st.markdown("#### 1. Stdio: Der direkte Draht")
        st.markdown("Client und Server laufen auf **demselben Computer** (z.B. Terminal). Sie sind wie mit einem Rohr verbunden. Sehr schnell, aber nur lokal.")
        st.markdown("""<div class="diagram-container"><div class="node"><div class="node-icon">🤖</div><div class="node-label">Prozess A</div></div><div class="pipe-connection"><div class="stdio-packet"></div></div><div class="node"><div class="node-icon">🖥️</div><div class="node-label">Prozess B</div></div></div>""", unsafe_allow_html=True)

    elif st.session_state.selected_transport == "sse":
        st.markdown("#### 2. SSE: Der Live-Ticker")
        st.markdown("Server-Sent Events. Funktioniert über **HTTP (Internet)**. Der Client sendet Briefe (POST-Requests), der Server antwortet mit einem dauerhaften Datenstrom (Stream). Das nutzen wir hier!")
        st.markdown("""<div class="diagram-container"><div class="node"><div class="node-icon">🌍</div><div class="node-label">Browser</div></div><div class="sse-connection"><div class="sse-pulse">📡  📡  📡</div></div><div class="node"><div class="node-icon">☁️</div><div class="node-label">Server</div></div></div>""", unsafe_allow_html=True)

    elif st.session_state.selected_transport == "cloud":
        st.markdown("#### 3. Cloud: Die Sicherheits-Schleuse")
        st.markdown("Wenn Server sensibel sind (z.B. Bankdaten), steht ein **OAuth-Wächter** dazwischen. Wie bei einer Grenzkontrolle oder einem Login mit Google.")
        st.markdown("""<div class="diagram-container"><div class="node"><div class="node-icon">💻</div></div><div class="connection-line"></div><div class="cloud-middle">☁️🔒</div><div class="connection-line"></div><div class="node"><div class="node-icon">🏦</div></div></div>""", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="result-btn">', unsafe_allow_html=True)
    if st.button("Verstanden! Weiter zur Live-Analyse ➡️", type="primary", use_container_width=True):
        st.session_state.learning_phase = "analysis"
        st.session_state.trace_data = None
        q = random.choice(LEARNING_SCENARIOS)
        st.session_state.current_demo_query = q
        st.session_state.messages.append({"role": "user", "content": q})
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# === PHASE 2: ANALYSIS ===
def render_analysis_phase():
    if st.session_state.trace_data is None or st.session_state.get("current_trace_type") == "simulation":
        loading_ph = st.empty()
        with loading_ph.container():
            st.info(f"🤖 **Analysiere Anfrage:** '{st.session_state.current_demo_query}'")
            loop = get_or_create_eventloop()
            trace, final = loop.run_until_complete(execute_mcp_pipeline(st.session_state.current_demo_query, "German"))
            st.session_state.trace_data = trace
            st.session_state.final_res = final
            st.session_state.current_trace_type = "analysis"
        loading_ph.empty() 
        st.rerun()

    if st.session_state.trace_data:
        st.markdown("---")
        st.subheader("🎓 Phase 2: Live-Verfolgung")
        for step in st.session_state.trace_data: render_learning_step(step)
        
        st.divider()
        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.markdown('<div class="action-btn">', unsafe_allow_html=True)
            if st.button("🔄 Neue zufällige Anfrage", use_container_width=True):
                new_q = random.choice(LEARNING_SCENARIOS)
                st.session_state.current_demo_query = new_q
                st.session_state.messages.append({"role": "user", "content": new_q})
                st.session_state.trace_data = None
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_right:
            st.markdown('<div class="result-btn">', unsafe_allow_html=True)
            if st.button("🚀 Nächste Stufe: Tool-Designer", use_container_width=True):
                st.session_state.learning_phase = "zod_intro"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# === PHASE 3a: ZOD ELI5 ===
def render_zod_phase():
    st.markdown("---")
    st.subheader("🎓 Phase 3a: Der Türsteher (Zod)")
    st.info("Bevor wir Code schreiben: **Validierung**.")

    st.markdown("""
    <div class="zod-container">
        <div style="text-align:center;"><div style="font-size:3rem;">🎲 🍏 🚗</div><div>Chaos Input</div></div>
        <div class="zod-arrow">➡️</div>
        <div style="text-align:center;"><div class="zod-bouncer">👮‍♂️ ZOD</div><div style="color:#60a5fa; font-weight:bold;">"Nur Autos!"</div></div>
        <div class="zod-arrow">➡️</div>
        <div style="text-align:center;"><div style="font-size:3rem;">🚗</div><div>Sauberer Output</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Was ist Zod?** Ein Türsteher für Daten. Er schützt den Server vor Quatsch-Input.")
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="result-btn">', unsafe_allow_html=True)
    if st.button("Verstanden! Lass uns den Code bauen 🛠️", type="primary", use_container_width=True):
        st.session_state.learning_phase = "creation"
        st.session_state.builder_step = 0
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# === PHASE 3b: BUILDER ===
def render_builder_phase():
    st.markdown("---")
    st.subheader("🎓 Phase 3b: Tool Architect")
    st.info("Wir bauen jetzt das `GetNewsSchema`. Definiere die Regeln!")

    slot_input = f'<span class="slot-filled">{st.session_state.builder_input}</span>' if st.session_state.builder_input else '<span class="slot-empty">INPUT?</span>'
    slot_desc = f'<span class="slot-filled">"{st.session_state.builder_desc}"</span>' if st.session_state.builder_desc else '<span class="slot-empty">BESCHREIBUNG?</span>'

    code_html = f"""
    <div class="code-builder-container">
        <div class="code-line"><span class="keyword">import</span> {{ z }} <span class="keyword">from</span> <span class="string">"zod"</span>;</div>
        <br>
        <div class="code-line"><span class="keyword">export const</span> <span class="method">GetNewsSchema</span> = z.object({{</div>
        <div class="code-line">&nbsp;&nbsp;<span class="variable">query</span>: z.string().describe(</div>
        <div class="code-line">&nbsp;&nbsp;&nbsp;&nbsp;{slot_desc}</div>
        <div class="code-line">&nbsp;&nbsp;),</div>
        <div class="code-line">&nbsp;&nbsp;<span class="variable">category</span>: {slot_input}</div>
        <div class="code-line">}});</div>
    </div>
    """
    st.markdown(code_html, unsafe_allow_html=True)

    st.markdown("<div class='builder-controls'>", unsafe_allow_html=True)
    if st.session_state.builder_step == 0:
        st.markdown("#### Schritt 1: Welchen Datentyp verlangt Zod?")
        c1, c2, c3 = st.columns(3)
        if c1.button("🔢 z.number()"): st.error("Falsch")
        if c2.button("🔤 z.string()"):
            st.session_state.builder_input = "z.string().optional()"
            st.session_state.builder_step = 1
            st.rerun()
        if c3.button("📅 z.date()"): st.error("Falsch")
    elif st.session_state.builder_step == 1:
        st.markdown("#### Schritt 2: Prompt Engineering")
        if st.button("✅ 'Search keywords'"):
            st.session_state.builder_desc = "Search keywords"
            st.session_state.builder_step = 2
            st.rerun()
    elif st.session_state.builder_step == 2:
        st.success("🎉 Kompilierung erfolgreich!")
        st.markdown('<div class="result-btn">', unsafe_allow_html=True)
        if st.button("🚀 Tool jetzt testen (Simulation)", type="primary", use_container_width=True):
            st.session_state.learning_phase = "simulation"
            st.session_state.trace_data = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# === PHASE 4: SIMULATION ===
def render_simulation_phase():
    st.markdown("---")
    st.subheader("🎓 Phase 4: Dein Tool im Einsatz (Simulation)")
    st.info("Query: **'Gibt es Neuigkeiten vom Campus?'**")

    if st.session_state.trace_data is None or st.session_state.get("current_trace_type") != "simulation":
        loading_ph = st.empty()
        with loading_ph.container():
            st.info("🤖 **Simuliere Netzwerkverkehr...**")
            loop = get_or_create_eventloop()
            trace, final = loop.run_until_complete(simulate_news_pipeline("News?"))
            st.session_state.trace_data = trace
            st.session_state.final_res = final
            st.session_state.current_trace_type = "simulation"
        loading_ph.empty()
        st.rerun()
    
    if st.session_state.trace_data:
        for step in st.session_state.trace_data: render_learning_step(step)
        
        st.markdown("---")
        st.markdown('<div class="result-btn">', unsafe_allow_html=True)
        if st.button("⚠️ Aber... Moment mal!", key="sim_next", use_container_width=True):
            st.session_state.learning_phase = "exercise_intro"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.caption("Achtung: Dies ist nur eine Simulation. Das Tool verschwindet bei Reload!")

# === PHASE 5: EXERCISE 1 (TOOL) ===
def render_exercise_phase():
    st.markdown("---")
    st.subheader("🛠️ Übung 1: Die Realität")
    
    st.markdown("""
    **Mission:** Bring dem echten Server bei, News zu liefern!
    1.  Stoppe den Server.
    2.  Bearbeite `src/schema.ts` (Schema hinzufügen).
    3.  Bearbeite `src/index.ts` (Tool-Logik hinzufügen).
    4.  Starte den Server neu (`npm start`).
    """)
    
    if "ex1_solved" not in st.session_state: st.session_state.ex1_solved = False

    if st.button("Verifizieren: Läuft das News-Tool?", type="primary", use_container_width=True):
        with st.spinner("Prüfe Server..."):
            loop = get_or_create_eventloop()
            success, msg = loop.run_until_complete(verify_real_server_has_tool())
            
            if success:
                st.session_state.ex1_solved = True
                st.balloons()
            else:
                st.error(f"❌ {msg}")

    if st.session_state.ex1_solved:
        st.success("✅ ERFOLG: Tool gefunden!")
        st.markdown("---")
        st.markdown("### 🎉 Super! Level 1 geschafft.")
        st.markdown('<div class="result-btn">', unsafe_allow_html=True)
        if st.button("Weiter zu Level 2: Resources 📚", type="primary", use_container_width=True):
            st.session_state.learning_phase = "resource_intro"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# === PHASE 6: RESOURCE INTRO ===
def render_resource_intro():
    st.markdown("---")
    st.subheader("🎓 Phase 6: Was sind Resources?")
    
    col1, col2 = st.columns([1, 2])
    with col1: st.markdown("# 📚")
    with col2:
        st.markdown("""
        **Tools = Kellner** (Bestellen -> Liefern).
        **Resources = Speisekarte** (Liegt da -> Lesen).
        
        * Tools: "Aktiv" (Funktion)
        * Resources: "Passiv" (Daten/Kontext)
        """)
    
    st.info("Resources haben URIs: `dhbw://mensa/monday`.")
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="result-btn">', unsafe_allow_html=True)
    if st.button("Alles klar! Lass uns eine Resource bauen 🛠️", type="primary", use_container_width=True):
        st.session_state.learning_phase = "resource_builder"
        st.session_state.res_builder_step = 0
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# === PHASE 7: RESOURCE BUILDER ===
def render_resource_builder():
    st.markdown("---")
    st.subheader("🎓 Phase 7: Resource Architect")
    st.info("Wie soll die Mensa-Adresse aussehen?")

    if "res_builder_step" not in st.session_state: st.session_state.res_builder_step = 0
    if "res_uri_part" not in st.session_state: st.session_state.res_uri_part = "???"

    st.markdown(f"""
    <div style="background:#1e293b; color:white; padding:20px; border-radius:10px; font-family:monospace; font-size:1.5em; text-align:center;">
        dhbw://mensa/<span style="color:#facc15;">{st.session_state.res_uri_part}</span>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.res_builder_step == 0:
        st.markdown("#### Wähle den Parameter:")
        c1, c2 = st.columns(2)
        if c1.button("🆔 {id}"): st.warning("Zu technisch.")
        if c2.button("📅 {day}"):
            st.session_state.res_uri_part = "{day}"
            st.session_state.res_builder_step = 1
            st.rerun()
            
    elif st.session_state.res_builder_step == 1:
        st.success("✅ URI-Template steht.")
        st.markdown('<div class="result-btn">', unsafe_allow_html=True)
        if st.button("Ab zur Implementierung (Übung 2) 💻", type="primary", use_container_width=True):
            st.session_state.learning_phase = "resource_exercise"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# === PHASE 8: RESOURCE EXERCISE ===
def render_resource_exercise():
    st.markdown("---")
    st.subheader("🛠️ Übung 2: Mensa-Daten einspeisen")
    
    st.markdown("""
    **Mission:** Füge den Mensa-Plan hinzu!
    1. **Daten:** In `src/db.json` neuen Key `"mensa"` anlegen.
    2. **Code:** In `src/index.ts` `server.resource("mensa"...)` hinzufügen.
    3. **Restart:** Server neu starten.
    """)
    
    if "ex2_solved" not in st.session_state: st.session_state.ex2_solved = False

    if st.button("Verifizieren: Gibt es die Mensa-Resource?", type="primary", use_container_width=True):
        with st.spinner("Scanne Server Resources..."):
            loop = get_or_create_eventloop()
            success, msg = loop.run_until_complete(verify_real_server_has_resource("mensa"))
            
            if success:
                st.session_state.ex2_solved = True
                st.balloons()
            else:
                st.error(f"❌ {msg}")

    if st.session_state.ex2_solved:
        st.success("✅ ERFOLG: Mensa-Resource gefunden!")
        st.markdown("### 🎓 Level 2 geschafft.")
        
        st.markdown('<div class="result-btn">', unsafe_allow_html=True)
        if st.button("Weiter zu Level 3: Security 🛡️", type="primary", use_container_width=True):
            st.session_state.learning_phase = "security_check"
            st.session_state.trace_data = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# === PHASE 9: SECURITY (THE FIREWALL) ===
def render_security_phase():
    st.markdown("---")
    st.subheader("🛡️ Phase 9: Security & Safety")
    
    st.markdown("""
    In deiner Arbeit (Kapitel 6) geht es um Sicherheit. 
    Was passiert, wenn ein User versucht, das System anzugreifen ("Prompt Injection")?
    
    **Das Szenario:** Ein Hacker will Noten manipulieren.
    """)
    
    attack = st.selectbox("Wähle einen Angriff:", SECURITY_SCENARIOS)
    
    if st.button("🔥 Angriff starten (Simulation)", type="primary", use_container_width=True):
        with st.status("🚨 Intrusion Detection System active..."):
            loop = get_or_create_eventloop()
            trace, final = loop.run_until_complete(simulate_security_check(attack))
            st.session_state.trace_data = trace
            st.session_state.final_res = final
    
    if st.session_state.trace_data:
        for step in st.session_state.trace_data:
            render_learning_step(step)
            
        st.markdown("---")
        st.success("✅ **System Secure:** Der Angriff wurde abgewehrt.")
        st.info("Warum? Weil wir im Schema (`schema.ts`) nur **Lese-Zugriff** definiert haben. Es gibt kein Tool `update_grade`. Das LLM kann nicht halluzinieren, was es nicht gibt.")
        
        st.markdown('<div class="result-btn">', unsafe_allow_html=True)
        if st.button("Weiter zum Finale: The Agent 🤖", type="primary", use_container_width=True):
            st.session_state.learning_phase = "agent_intro"
            st.session_state.trace_data = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# === PHASE 10: AGENTIC CHAINING ===
def render_agent_intro():
    st.markdown("---")
    st.subheader("🤖 Phase 10: The Agent (Multi-Hop)")
    
    st.markdown("""
    Bisher haben wir einfache Fragen gestellt (1 Frage -> 1 Tool).
    Die wahre Power von MCP entsteht durch **Chaining** (Verkettung).
    
    **Die komplexe Frage:**
    > *"Wann hat der Professor meiner schlechtesten Note seine nächste Vorlesung?"*
    
    Das LLM muss:
    1.  Noten prüfen (`get_student_grades`)
    2.  Schlechteste finden (Logik)
    3.  Stundenplan des Profs suchen (`get_schedule`)
    """)
    
    if st.button("🧠 Agent starten (Reasoning Loop)", type="primary", use_container_width=True):
        with st.status("Agent denkt nach..."):
            loop = get_or_create_eventloop()
            trace, final = loop.run_until_complete(simulate_chaining_pipeline())
            st.session_state.trace_data = trace
            st.session_state.final_res = final
            
    if st.session_state.trace_data:
        for step in st.session_state.trace_data:
            render_learning_step(step)
            
        st.markdown("---")
        st.chat_message("assistant").markdown(st.session_state.final_res)
        
        st.balloons()
        st.markdown("### 🏆 Gratulation!")
        st.markdown("Du hast den **DHBW Enterprise MCP Learning Trail** erfolgreich absolviert.")
        
        if st.button("🔄 Alles zurücksetzen", use_container_width=True):
            st.session_state.clear()
            st.rerun()