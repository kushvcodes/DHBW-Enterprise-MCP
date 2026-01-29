import streamlit as st
import pandas as pd

def render_learning_step(step_data):
    st.markdown(f"""
    <div class="learning-card">
        <div class="card-header"><div class="card-icon">{step_data['icon']}</div><div class="card-title">{step_data['title']}</div></div>
        <div class="card-desc">{step_data['simple_desc']}</div>
    </div>
    """, unsafe_allow_html=True)
    with st.container():
        c1, c2 = st.columns([0.5, 10])
        with c2:
            if step_data['visual_type'] == "status":
                st.caption("Technische Parameter:")
                st.json(step_data['data'], expanded=False)
            elif step_data['visual_type'] == "table":
                if isinstance(step_data['data'], list): st.dataframe(pd.DataFrame(step_data['data']), hide_index=True, use_container_width=True)
                with st.expander("🔍 Vollständiges JSON-Schema ansehen"): st.code(str(step_data.get('raw_data', [])), language="json")
            elif step_data['visual_type'] == "decision":
                d = step_data['data']
                cols = st.columns(3)
                cols[0].metric("Gewählte Aktion", d.get('action').upper())
                cols[1].metric("Tool / Ressource", d.get('name', 'N/A'))
                st.info(f"💡 **Begründung der KI:** {d.get('reasoning', 'Keine Begründung verfügbar.')}")
                with st.expander("🛠️ Übergebene Argumente (Input)"): st.json(d.get('args'))
            elif step_data['visual_type'] == "code":
                st.markdown("**Vom Server empfangene Rohdaten:**")
                st.code(step_data['data'], language="json")
            elif step_data['visual_type'] == "error": st.error(f"Fehler: {step_data['data']}")