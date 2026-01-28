import streamlit as st
import asyncio
import json
import time
import httpx
import traceback
import os
from dotenv import load_dotenv

# Load environment variables
script_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(script_dir, '.env')):
    load_dotenv(os.path.join(script_dir, '.env'))
elif os.path.exists(os.path.join(script_dir, '..', '.env')):
    load_dotenv(os.path.join(script_dir, '..', '.env'))

from mcp import ClientSession
from mcp.client.sse import sse_client
import google.generativeai as genai

# --- CONFIG ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = 'gemini-2.0-flash'

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

MCP_URL = "http://localhost:3000/sse"
USE_DEEPSEEK = True 

if not USE_DEEPSEEK and GOOGLE_API_KEY: 
    genai.configure(api_key=GOOGLE_API_KEY)

st.set_page_config(page_title="DHBW Enterprise Assistant", page_icon="🏛️", layout="wide")

# --- DATABASE HELPER ---
DB_PATH = os.path.join(script_dir, "..", "src", "db.json")

def load_db():
    try:
        paths_to_try = [
            DB_PATH,
            os.path.join(script_dir, "db.json"),
            os.path.join(os.getcwd(), "src", "db.json")
        ]
        for p in paths_to_try:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
        return {"error": "Database file not found."}
    except Exception as e:
        return {"error": str(e)}

# --- TRANSLATION SYSTEM ---
@st.cache_data
def load_translations(language):
    try:
        lang_code = "de" if language == "German" else "en"
        filename = f"{lang_code}.json"
        
        # Build a reliable path to the translations directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        translations_dir = os.path.join(script_dir, "..", "translations")
        file_path = os.path.join(translations_dir, filename)
        
        if not os.path.exists(file_path):
            # Fallback for running directly in the client folder
            translations_dir = os.path.join(script_dir, "translations")
            file_path = os.path.join(translations_dir, filename)

        if not os.path.exists(file_path):
             return {}

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

if "language" not in st.session_state:
    st.session_state.language = "German"

current_translations = load_translations(st.session_state.language)

def get_text(key):
    return current_translations.get(key, f"[{key}]")

def get_or_create_eventloop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

async def call_deepseek_model(prompt_text: str, model_name: str, api_key: str):
    if not api_key:
        return "Error: DEEPSEEK_API_KEY not found."
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    messages = [{"role": "user", "content": prompt_text}]
    payload = {"model": model_name, "messages": messages}
    async with httpx.AsyncClient(base_url=DEEPSEEK_BASE_URL) as client:
        response = await client.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload, timeout=60.0)
        if response.status_code != 200:
            return f"Error from DeepSeek (Status {response.status_code}): {response.text}"
        response_json = response.json()
        return response_json["choices"][0]["message"]["content"]

# --- PAGE SHOW FUNCTIONS ---

def show_about_mcp():
    st.title(get_text("about_title"))
    st.markdown(get_text("about_intro"))
    st.markdown(get_text("about_desc"))
    st.markdown(get_text("about_how_title"))
    st.markdown(get_text("about_step1"))
    st.markdown(get_text("about_step2"))
    st.markdown(get_text("about_step3"))
    st.markdown(get_text("about_step4"))

def show_app():
    # --- SIDEBAR: CONTROL CENTER (Sticky by default) ---
    with st.sidebar:
        st.header(get_text("settings_header"))
        lang_choice = st.radio(get_text("lang_label"), ["German", "English"], key="lang_main")
        if lang_choice != st.session_state.language:
            st.session_state.language = lang_choice
            st.rerun()
        
        st.divider()
        st.subheader("📚 Enterprise Context")
        
        # Scrollable container for DB inspection
        # This keeps the sidebar fixed but lets you scroll through long JSON
        with st.container(height=400):
            side_tabs = st.tabs(["🗄️ Database", "📖 Theory"])
            
            with side_tabs[0]:
                st.caption("Read-Only View of Enterprise Data")
                db_data = load_db()
                if "error" in db_data:
                    st.error(db_data["error"])
                else:
                    cat_options = list(db_data.keys()) if db_data else []
                    selected_cat = st.selectbox("Select Table", cat_options, key="side_cat")
                    if selected_cat:
                        st.json(db_data[selected_cat], expanded=False)

            with side_tabs[1]:
                st.caption("Academic References")
                st.markdown("""
                **Architecture:**
                > "The architectural structure follows the Client-Host-Server pattern... ensuring a separation of concerns."
                
                **Security:**
                > "By utilizing a volatile In-Memory-Database, the protocol layer is effectively decoupled from the physical file system."
                
                **Validation:**
                > "Strict schema validation acts as an application firewall against malicious payloads."
                """)

    # --- MAIN CHAT AREA ---
    st.title(get_text("app_title"))

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": get_text("app_welcome")}]

    # Render History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    # Chat Input (Always stays at bottom)
    if prompt := st.chat_input(get_text("chat_input_placeholder")):
        # 1. Add User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        # 2. Generate Assistant Response
        with st.chat_message("assistant"):
            # Containers for "Thinking" process
            status = st.status(get_text("status_processing"), expanded=True)
            protocol_container = st.expander("🛠️ MCP Protocol Inspector", expanded=False)
            
            # Placeholder for the final text
            response_placeholder = st.empty()

            async def run_chat_logic():
                try:
                    status.write(get_text("status_connecting"))
                    async with sse_client(MCP_URL) as streams:
                        async with ClientSession(streams[0], streams[1]) as session:
                            # A. INITIALIZE
                            await session.initialize()
                            with protocol_container:
                                st.subheader("1. Lifecycle: initialize")
                                st.json({"jsonrpc": "2.0", "method": "initialize"})
                            
                            # B. DISCOVERY
                            status.write(get_text("status_routing"))
                            tool_response = await session.list_tools()
                            tools_for_prompt = [
                                {"name": t.name, "description": t.description, "input_schema": t.inputSchema}
                                for t in tool_response.tools
                            ]
                            with protocol_container:
                                st.subheader("2. Discovery: tools/list")
                                st.json([{"name": t.name} for t in tool_response.tools])

                            # C. ROUTING
                            history_text = ""
                            relevant_history = st.session_state.messages[:-1]
                            if relevant_history:
                                history_text = "HISTORY:\n" + "\n".join([f"- {m['role']}: {m['content']}" for m in relevant_history])

                            router_prompt = f"""
                            You are the DHBW System Router.
                            Language: {st.session_state.language}.
                            {history_text}
                            Query: "{prompt}"
                            TOOLS: {json.dumps(tools_for_prompt, indent=2)}
                            RESOURCES:
                            - dhbw://syllabus/{{code}}
                            - dhbw://news/{{article_id}}
                            - dhbw://publications/{{prof_id}}
                            OUTPUT JSON ONLY:
                            {{ "action": "tool|resource|chat", "name|uri": "...", "args": {{...}} }}
                            """
                            
                            if USE_DEEPSEEK:
                                raw_response = await call_deepseek_model(router_prompt, DEEPSEEK_MODEL, DEEPSEEK_API_KEY)
                            else:
                                model = genai.GenerativeModel(GEMINI_MODEL)
                                res_gemini = await model.generate_content_async(router_prompt)
                                raw_response = res_gemini.text
                            
                            try:
                                decision = json.loads(raw_response.replace("```json","").replace("```", "").strip())
                            except:
                                decision = {"action": "chat", "response": raw_response}

                            with protocol_container:
                                st.subheader("3. Decision")
                                st.json(decision)

                            # D. EXECUTION
                            data = ""
                            if decision.get("action") == "tool":
                                tool_name = decision.get("name", "N/A")
                                args = decision.get("args", {})
                                status.write(get_text("status_executing").format(tool_name=tool_name))
                                try:
                                    res = await session.call_tool(tool_name, args)
                                    data = res.content[0].text if res.content else "No output."
                                    with protocol_container:
                                        st.subheader("4. Execution")
                                        st.json({"result": data})
                                except Exception as e:
                                    data = f"Error: {e}"
                                
                            elif decision.get("action") == "resource":
                                uri = decision.get("uri", "N/A")
                                status.write(get_text("status_fetching").format(uri=uri))
                                try:
                                    res = await session.read_resource(uri)
                                    data = res.contents[0].text if res.contents else "Empty."
                                except Exception as e:
                                    data = f"Error: {e}"

                            elif decision.get("action") == "chat":
                                status.update(label="Complete", state="complete", expanded=False)
                                return decision.get("response", "I am not sure.")

                            # E. SYNTHESIS
                            status.write(get_text("status_formatting"))
                            final_prompt = f"""
                            Role: University Assistant.
                            Lang: {st.session_state.language}
                            User: "{prompt}"
                            Data: {data}
                            Task: Answer using data. Suggest learning next step.
                            """

                            if USE_DEEPSEEK:
                                final_res = await call_deepseek_model(final_prompt, DEEPSEEK_MODEL, DEEPSEEK_API_KEY)
                            else:
                                model = genai.GenerativeModel(GEMINI_MODEL)
                                final_res_gemini = await model.generate_content_async(final_prompt)
                                final_res = final_res_gemini.text
                            
                            status.update(label="Complete", state="complete", expanded=False)
                            return final_res
                
                except Exception as e:
                    status.update(label="Error", state="error")
                    return f"System Error: {str(e)}"

            # Run the logic
            loop = get_or_create_eventloop()
            res = loop.run_until_complete(run_chat_logic())
            
            # Display final result
            st.markdown(res)
            
            # Save to history
            st.session_state.messages.append({"role": "assistant", "content": res})


# --- NAVIGATION PAGES (PRESERVED) ---

def show_tool_explorer():
    st.title(get_text("explorer_title"))
    st.markdown(get_text("explorer_intro"))
    async def get_tools_async(): 
        try:
            async with sse_client(MCP_URL) as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    await session.initialize()
                    return await session.list_tools() 
        except Exception as e:
            st.error(get_text("tutorial_error").format(e=e))
            return None
    loop = get_or_create_eventloop()
    tools_response = loop.run_until_complete(get_tools_async()) 
    if tools_response and tools_response.tools: 
        for tool in tools_response.tools:
            with st.expander(f"**{tool.name}**"):
                st.markdown(f"**{get_text('tool_desc')}:** {tool.description}")
                st.json(tool.inputSchema)

def show_tutorial_page():
    st.title(get_text("tutorial_title"))
    st.header(get_text("tutorial_step1_title"))
    st.code('{"events": [{"name": "Karrieremesse", "date": "2025-10-26"}]}', language="json")

def show_model_explanation_page():
    st.title(get_text("model_title"))
    st.code("router_prompt = f'Du bist der DHBW System Router...'", language="python")

def show_learning_trail_exercise_page():
    st.title(get_text("exercise_title"))
    custom_prompt = st.text_area(get_text("exercise_custom_prompt_label"), height=300)
    if st.button(get_text("exercise_save_btn")):
        st.session_state.custom_formatter_prompt = custom_prompt

def show_benchmark_results():
    st.title("📊 Benchmark Results")

    benchmark_type = st.selectbox("Select Benchmark Type", ["SSE", "stdio"])

    if benchmark_type == "SSE":
        results_path = os.path.join(script_dir, "..", "benchmark_results.json")
    else:
        results_path = os.path.join(script_dir, "..", "benchmark_results_stdio.json")

    if not os.path.exists(results_path):
        st.warning(f"`{os.path.basename(results_path)}` not found. Please run the corresponding benchmark script first.")
        return

    with open(results_path, "r") as f:
        results = json.load(f)

    st.info(f"**Last Benchmark Run:** {results.get('last_run_utc', 'N/A')} ({results.get('type', 'N/A').upper()})")

    st.header("🛠️ Tool Benchmarks")
    st.metric("Overall Average Latency (Tools)", f"{results.get('overall_avg_latency_tools', 0):.2f} ms")
    tool_data = []
    for tool_name, tool_results in results.get("tools", {}).items():
        tool_data.append({
            "Tool": tool_name,
            "Avg Latency (ms)": f"{tool_results['avg_latency']:.2f}",
            "Total Time (ms)": f"{tool_results['total_time']:.2f}",
            "Success": tool_results['successes'],
            "Errors": tool_results['errors']
        })
    if tool_data:
        st.dataframe(tool_data)

    st.header("📚 Resource Benchmarks")
    if results.get('resources'):
        st.metric("Overall Average Latency (Resources)", f"{results.get('overall_avg_latency_resources', 0):.2f} ms")
        resource_data = []
        for resource_name, resource_results in results.get("resources", {}).items():
            resource_data.append({
                "Resource": resource_name,
                "List Latency (ms)": f"{resource_results['list_latency_ms']:.2f}",
                "List Items": resource_results['list_item_count'],
                "Read Avg Latency (ms)": f"{resource_results['read_avg_latency_ms']:.2f}"
            })
        if resource_data:
            st.dataframe(resource_data)
    else:
        st.info("Resource benchmarking is not applicable to the stdio transport type.")


# --- MAIN APP FLOW ---
# We handle the sidebar navigation logic here, but the "App" page creates its OWN sidebar content.
# To prevent conflicts, we only show navigation if NOT in App, or we structure it carefully.
# For simplicity, we put the Nav selection at the TOP of the sidebar.

with st.sidebar:
    st.title("Navigation")
    nav_options = {
        get_text("nav_app"): "App",
        get_text("nav_about"): "About MCP",
        get_text("nav_explorer"): "Tool Explorer",
        get_text("nav_create"): "Create a Tool",
        get_text("nav_model"): "The Model in MCP",
        get_text("nav_exercise"): "Learning Trail Exercise",
        "Benchmark Results": "Benchmark Results"
    }
    # Unique key for nav radio
    selected_label = st.radio(get_text("nav_goto"), list(nav_options.keys()), key="nav_radio_main")
    page_id = nav_options.get(selected_label, "App")
    st.divider() # Separation between Nav and Page-Specific Settings

PAGES = {
    "App": show_app,
    "About MCP": show_about_mcp,
    "Tool Explorer": show_tool_explorer,
    "Create a Tool": show_tutorial_page,
    "The Model in MCP": show_model_explanation_page,
    "Learning Trail Exercise": show_learning_trail_exercise_page,
    "Benchmark Results": show_benchmark_results
}

if page_id in PAGES:
    PAGES[page_id]()
else:
    show_app()
