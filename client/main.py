import streamlit as st
from config import LEARNING_SCENARIOS
from styles import apply_custom_styles
from utils import load_db, get_text, get_or_create_eventloop
from backend_logik import execute_mcp_pipeline
from learning_phases import (
    render_intro_phase, render_transports_phase, render_analysis_phase, 
    render_zod_phase, render_builder_phase, render_simulation_phase, 
    render_exercise_phase,
    render_resource_intro, render_resource_builder, render_resource_exercise,
    render_security_phase, render_agent_intro
)
from benchmark_page import show_benchmark_results 
from info_page import show_info_page # <--- NEW IMPORT

# Setup Page
st.set_page_config(page_title="DHBW Enterprise Assistant", page_icon="🏛️", layout="wide")
apply_custom_styles()

# --- STATE INITIALIZATION ---
if "messages" not in st.session_state: st.session_state.messages = [{"role": "assistant", "content": get_text("app_welcome")}]
if "current_view" not in st.session_state: st.session_state.current_view = "learning_trail" 

# ... [KEEP ALL OTHER STATE INITIALIZATIONS SAME AS BEFORE] ...
if "learning_active" not in st.session_state: st.session_state.learning_active = False
if "learning_phase" not in st.session_state: st.session_state.learning_phase = "intro"
if "trace_data" not in st.session_state: st.session_state.trace_data = None
if "final_res" not in st.session_state: st.session_state.final_res = None
if "current_trace_type" not in st.session_state: st.session_state.current_trace_type = None 
if "current_demo_query" not in st.session_state: st.session_state.current_demo_query = None
if "show_tool_sample" not in st.session_state: st.session_state.show_tool_sample = False
if "show_resource_sample" not in st.session_state: st.session_state.show_resource_sample = False
if "selected_transport" not in st.session_state: st.session_state.selected_transport = None
if "builder_step" not in st.session_state: st.session_state.builder_step = 0
if "builder_input" not in st.session_state: st.session_state.builder_input = None
if "builder_desc" not in st.session_state: st.session_state.builder_desc = None
if "res_builder_step" not in st.session_state: st.session_state.res_builder_step = 0
if "res_uri_part" not in st.session_state: st.session_state.res_uri_part = "???"
if "ex1_solved" not in st.session_state: st.session_state.ex1_solved = False
if "ex2_solved" not in st.session_state: st.session_state.ex2_solved = False
if "language" not in st.session_state: st.session_state.language = "German"

# --- SIDEBAR ---
with st.sidebar:
    st.header("DHBW Assistant")
    
    # UPDATED NAVIGATION MENU
    view_mode = st.radio(
        "Navigation", 
        ["Learning Trail", "Benchmarks", "Info & Credits", "Settings"], # Added Info & Credits
        key="nav_radio"
    )
    
    st.divider()

    if view_mode == "Learning Trail":
        st.markdown("### 🎓 Lernpfad Steuerung")
        if not st.session_state.learning_active:
            if st.button("🚀 Lernpfad starten", type="primary", use_container_width=True):
                st.session_state.learning_active = True
                st.session_state.learning_phase = "intro"
                st.session_state.trace_data = None
                st.rerun()
        else:
            st.success(f"Phase: {st.session_state.learning_phase}")
            if st.button("❌ Beenden", use_container_width=True):
                st.session_state.learning_active = False
                st.session_state.learning_phase = "intro"
                st.session_state.trace_data = None
                st.rerun()
    
    elif view_mode == "Benchmarks":
        st.info("Hier sehen Sie die Performance-Daten Ihrer MCP-Implementierung.")
        
    elif view_mode == "Info & Credits":
        st.info("Hintergründe zur Integrationsseminararbeit.")

    elif view_mode == "Settings":
        st.caption("Datenbank Vorschau")
        st.json(load_db(), expanded=False)
        st.markdown("---")
        if st.button("🔄 App zurücksetzen", use_container_width=True):
            st.session_state.clear()
            st.rerun()

# --- MAIN CONTENT ROUTING ---

if view_mode == "Benchmarks":
    show_benchmark_results()

elif view_mode == "Info & Credits": # NEW ROUTE
    show_info_page()

elif view_mode == "Learning Trail":
    st.title(get_text("app_title"))

    # Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    # Learning Phases Logic
    if st.session_state.learning_active:
        phase = st.session_state.learning_phase
        
        if phase == "intro": render_intro_phase()
        elif phase == "transports": render_transports_phase()
        elif phase == "analysis": render_analysis_phase()
        
        elif phase == "zod_intro": render_zod_phase()
        elif phase == "creation": render_builder_phase()
        elif phase == "simulation": render_simulation_phase()
        elif phase == "exercise_intro": render_exercise_phase()
        
        elif phase == "resource_intro": render_resource_intro()
        elif phase == "resource_builder": render_resource_builder()
        elif phase == "resource_exercise": render_resource_exercise()
        
        elif phase == "security_check": render_security_phase()
        elif phase == "agent_intro": render_agent_intro()

    # Normal Chat Input
    elif prompt := st.chat_input(get_text("chat_input_placeholder")):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Antworte..."):
                loop = get_or_create_eventloop()
                _, res = loop.run_until_complete(execute_mcp_pipeline(prompt, st.session_state.language))
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})

elif view_mode == "Settings":
    st.title("⚙️ Einstellungen & Debug")
    st.write("Verwenden Sie die Sidebar, um die Datenbank zu inspizieren oder den State zurückzusetzen.")