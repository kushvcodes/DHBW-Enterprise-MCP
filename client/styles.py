import streamlit as st

def apply_custom_styles():
    st.markdown("""
    <style>
        /* General App Styling */
        .stApp { background-color: #f8f9fa; }
        
        /* DIAGRAM CONTAINER */
        .diagram-container {
            display: flex; align-items: center; justify-content: space-between;
            background: #ffffff; padding: 40px; border-radius: 20px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.05); margin-bottom: 30px;
            border: 1px solid #e2e8f0; position: relative; overflow: hidden;
            min-height: 200px;
        }

        .node { display: flex; flex-direction: column; align-items: center; z-index: 5; width: 140px; position: relative; }
        .node-icon {
            font-size: 3.5rem; margin-bottom: 10px; background: #f1f5f9; border-radius: 50%;
            width: 90px; height: 90px; display: flex; align-items: center; justify-content: center;
            border: 4px solid #cbd5e1; transition: all 0.3s ease;
        }
        .node-label { font-weight: bold; color: #475569; font-family: sans-serif; font-size: 1.1rem; }
        .server-active { animation: serverPulse 1s ease-out; }

        /* PHASE 1: SIMPLE PACKETS */
        .connection-line { flex-grow: 1; height: 12px; background: #e2e8f0; margin: 0 30px; position: relative; border-radius: 6px; }
        .packet { position: absolute; top: -14px; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; background: white; border-radius: 50%; box-shadow: 0 2px 5px rgba(0,0,0,0.2); z-index: 4; }
        .packet-request { animation: flowRight 2s infinite linear; border: 2px solid #3b82f6; }
        .packet-response { animation: flowLeft 2s infinite linear; border: 2px solid #10b981; background-color: #ecfdf5; }
        
        @keyframes flowRight { 0% { left: 0%; opacity: 0; transform: scale(0.8); } 10% { opacity: 1; } 90% { opacity: 1; } 100% { left: 92%; opacity: 0; transform: scale(0.8); } }
        @keyframes flowLeft { 0% { left: 92%; opacity: 0; transform: scale(0.8); } 10% { opacity: 1; } 90% { opacity: 1; } 100% { left: 0%; opacity: 0; transform: scale(0.8); } }
        @keyframes serverPulse { 0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7); border-color: #3b82f6; transform: scale(1); } 50% { box-shadow: 0 0 0 20px rgba(59, 130, 246, 0); border-color: #60a5fa; transform: scale(1.1); } 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); border-color: #cbd5e1; transform: scale(1); } }

        /* PHASE 1b: TRANSPORT ANIMATIONS */
        
        /* STDIO: The Pipe */
        .pipe-connection {
            flex-grow: 1; height: 40px; background: #475569; margin: 0 10px; position: relative;
            border-radius: 4px; overflow: hidden; border: 2px solid #334155;
        }
        .stdio-packet {
            position: absolute; top: 5px; width: 30px; height: 30px; background: #facc15; border-radius: 50%;
            animation: fastPipe 1s infinite cubic-bezier(0.4, 0, 0.2, 1);
        }
        @keyframes fastPipe { 0% { left: -10%; } 100% { left: 110%; } }

        /* SSE: The Stream */
        .sse-connection {
            flex-grow: 1; height: 4px; background: transparent; border-bottom: 4px dashed #3b82f6; margin: 0 30px; position: relative;
        }
        .sse-pulse {
            position: absolute; top: -18px; font-size: 20px;
            animation: flowRight 3s infinite linear;
        }

        /* CLOUD: The Middleman */
        .cloud-middle {
            font-size: 4rem; color: #60a5fa; margin: 0 20px; animation: floatCloud 3s infinite ease-in-out;
        }
        @keyframes floatCloud { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }

        /* ZOD & BUILDER STYLES */
        .zod-container { background: #1e1e1e; padding: 30px; border-radius: 15px; color: white; display: flex; align-items: center; justify-content: space-around; margin-bottom: 20px; }
        .zod-bouncer { font-size: 4rem; text-align: center; }
        .zod-arrow { font-size: 2rem; color: #569cd6; }
        .zod-bad { color: #f87171; text-decoration: line-through; opacity: 0.6; }
        .zod-good { color: #4ade80; font-weight: bold; }
        
        .code-builder-container { background-color: #1e1e1e; color: #d4d4d4; padding: 20px; border-radius: 10px; font-family: 'Consolas', 'Monaco', monospace; font-size: 1.1rem; border: 2px solid #3c3c3c; }
        .code-line { margin-bottom: 5px; min-height: 25px; display: flex; align-items: center; }
        .keyword { color: #569cd6; } .variable { color: #9cdcfe; } .string { color: #ce9178; } .method { color: #dcdcaa; }
        .slot-empty { border: 2px dashed #569cd6; background-color: rgba(86, 156, 214, 0.1); color: #569cd6; padding: 2px 8px; border-radius: 4px; font-size: 0.9rem; margin: 0 5px; animation: pulse-dashed 2s infinite; }
        .slot-filled { background-color: #264f78; color: white; padding: 2px 8px; border-radius: 4px; border: 1px solid #569cd6; animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); }

        .feature-box { background-color: #1e293b; color: white; padding: 20px; border-radius: 12px; margin-top: 10px; border: 2px solid #475569; animation: fadeIn 0.5s ease-in; }
        .learning-card { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 15px; border-left: 5px solid #3b82f6; }
        .card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
        .card-icon { font-size: 1.5rem; background-color: #eff6ff; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 50%; }
        .card-title { color: #1e3a8a; font-size: 1.1rem; font-weight: 700; }
        
        .result-btn button { background-color: #10b981 !important; color: white !important; animation: pulse-green 2s infinite; font-weight: bold !important; border: none !important; }
        .action-btn button { background-color: #3b82f6 !important; color: white !important; border: 1px solid #60a5fa !important; }
        div[data-testid="stStatusWidget"] { display: none; }
    </style>
    """, unsafe_allow_html=True)