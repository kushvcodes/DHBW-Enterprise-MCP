import streamlit as st

def show_info_page():
    st.title("ℹ️ Über dieses Projekt")
    
    st.markdown("""
    ### 🏛️ DHBW Enterprise Assistant
    Dieses Projekt ist das Ergebnis einer **Integrationsseminararbeit** an der **DHBW Stuttgart** (Studiengang Wirtschaftsinformatik, Kurs WWI2023V).
    
    Ziel der Arbeit war es, nicht nur theoretisch über das **Model Context Protocol (MCP)** zu schreiben, sondern einen funktionierenden, **didaktischen Prototyp** zu entwickeln, der die unsichtbare Kommunikationsschicht zwischen KI und Systemen sichtbar macht.
    """)

    st.divider()

    # --- TEAM SECTION ---
    st.subheader("👨‍💻 Das Entwickler-Team")
    st.markdown("Dieses Projekt wurde von folgendem Team realisiert:")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.success("**Harsh Kushwaha**\n\nDeveloper & Co-Author")
    with c2:
        st.info("**Markus Duong**\n\nCo-Author & Research")
    with c3:
        st.info("**Sven Fritzler**\n\nCo-Author & Research")
    with c4:
        st.info("**Michael Bobkov**\n\nCo-Author & Research")

    st.caption("Betreut von: Prof. Dr. Thomas Kessel")

    st.divider()

    # --- MOTIVATION & CONCEPT ---
    col_left, col_right = st.columns([1.5, 1])
    
    with col_left:
        st.subheader("🎯 Die Motivation")
        st.markdown("""
        **Das Problem:** Moderne LLMs sind beeindruckend, aber isoliert. Sie haben:
        * Keinen Zugriff auf Live-Daten (Datenbanken, APIs).
        * Keine "Ohren" für Ereignisse.
        * Schwierigkeiten bei der Integration in Firmennetze ("MxN"-Problem).
        
        **Die Lösung (MCP):** Ein offener Standard, der wie ein **"USB-C für KI"** funktioniert. Er standardisiert, wie KIs mit Tools und Ressourcen sprechen.
        """)

    with col_right:
        st.subheader("⚙️ Die Technik")
        st.markdown("""
        **Architektur:** "Split-Stack"
        * **Frontend:** Python (Streamlit) für Orchestrierung.
        * **Backend:** Node.js MCP-Server.
        * **Security:** In-Memory DB & Zod-Validierung.
        * **Didaktik:** "Active Inspection" statt Black Box.
        """)

    # --- METHODOLOGY ---
    st.divider()
    st.subheader("🔬 Methodik: Design Science Research")
    st.markdown("""
    Die Entwicklung folgte dem **Design Science Research (DSR)** Ansatz nach Hevner et al. (2004). 
    Das Projekt besteht aus einem methodischen Dreiklang:
    
    1.  **Prototyping:** Bau eines echten Enterprise-Agenten.
    2.  **Learning Trail:** Ein interaktives Tutorial (diese App), um die Protokoll-Mechanik zu lehren.
    3.  **Evaluation:** Messung von Latenzen (SSE vs. Stdio) und Sicherheit.
    """)

    st.info("""
    **Zitat aus der Arbeit:**
    "Der 'Interactive Mode' des Prototyps bricht diese Illusion auf, indem er die unsichtbare Kommunikationsschicht visualisiert... Anstatt lediglich das Endergebnis einer Anfrage anzuzeigen, exponiert das System den gesamten Entscheidungsprozess."
    """)