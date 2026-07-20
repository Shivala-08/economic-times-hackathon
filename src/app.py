"""Streamlit UI for Industrial Knowledge Intelligence — Day 4.

Day 4 upgrades:
  • Real Ollama LLM answers rendered in Markdown
  • Key-points bullet display
  • 👍 / 👎 feedback buttons wired to /feedback
  • ⚡ Benchmark tab with live progress
  • LLM / Ollama status in sidebar
  • 120 s query timeout for local LLM
"""

import streamlit as st
import requests
import json
import os
from datetime import datetime

try:
    from streamlit_agraph import agraph, Node, Edge, Config
    AGRAPH_AVAILABLE = True
except ImportError:
    AGRAPH_AVAILABLE = False

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Industrial Knowledge Intelligence",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = os.getenv("API_URL", "http://localhost:8000")

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Outfit', 'Inter', sans-serif !important;
        background-color: #060813 !important;
    }
    .main .block-container { padding-top: 2rem; padding-bottom: 3rem; }

    /* ── Header Toolbar ── */
    div[data-testid="stHeader"] {
        background-color: rgba(6, 8, 19, 0.5) !important;
        backdrop-filter: blur(10px) !important;
    }

    /* ── Sidebar Styling ── */
    section[data-testid="stSidebar"] {
        background-color: #04050b !important;
        border-right: 1px solid rgba(99, 102, 241, 0.2) !important;
        box-shadow: 5px 0 25px rgba(0, 0, 0, 0.4) !important;
    }
    section[data-testid="stSidebar"] .stMarkdown h3 {
        font-weight: 700 !important;
        letter-spacing: -0.02em;
        color: #f1f5f9 !important;
        margin-top: 1.5rem !important;
        border-left: 3px solid #818cf8;
        padding-left: 0.5rem;
    }

    /* ── Custom Selectboxes & Input Elements ── */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
        background-color: rgba(13, 17, 33, 0.7) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 12px !important;
        color: #f1f5f9 !important;
        font-weight: 500 !important;
        padding: 0.4rem 0.8rem !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus-within, .stNumberInput input:focus {
        border-color: rgba(99, 102, 241, 0.6) !important;
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.3) !important;
        background-color: rgba(15, 23, 42, 0.9) !important;
    }
    
    /* Dropdown list items */
    ul[data-baseweb="menu"] {
        background-color: #0f172a !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        border-radius: 10px !important;
    }
    li[role="option"] {
        color: #e2e8f0 !important;
        font-family: 'Outfit', sans-serif !important;
        transition: background 0.15s ease !important;
    }
    li[role="option"]:hover {
        background-color: rgba(99, 102, 241, 0.15) !important;
    }

    /* ── Navigation Tabs ── */
    div[data-role="tablist"] {
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
        gap: 0.5rem !important;
    }
    button[data-baseweb="tab"] {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #64748b !important;
        background-color: transparent !important;
        border: none !important;
        padding: 0.75rem 1.6rem !important;
        border-radius: 12px 12px 0 0 !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        margin-bottom: -1px !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #cbd5e1 !important;
        background-color: rgba(255, 255, 255, 0.03) !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #818cf8 !important;
        border-bottom: 2px solid #818cf8 !important;
        background-color: rgba(99, 102, 241, 0.08) !important;
        box-shadow: inset 0 -2px 0 #818cf8 !important;
    }

    /* ── Premium Metric Cards ── */
    div[data-testid="stMetricValue"] {
        font-weight: 800 !important;
        font-size: 2.2rem !important;
        letter-spacing: -0.03em !important;
        background: linear-gradient(135deg, #ffffff, #a5b4fc) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: #64748b !important;
        font-weight: 600 !important;
    }
    div[data-testid="metric-container"] {
        background: rgba(13, 17, 33, 0.6) !important;
        border: 1px solid rgba(99, 102, 241, 0.15) !important;
        border-radius: 16px !important;
        padding: 1.2rem 1.5rem !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2) !important;
    }

    /* ── Cards & Panels ── */
    .doc-card {
        background: rgba(13, 17, 33, 0.65); backdrop-filter: blur(12px);
        border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px;
        padding: 1.4rem 1.8rem; margin-bottom: 1.2rem;
        box-shadow: 0 12px 40px rgba(0,0,0,0.25);
        transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1); color: #f8fafc;
    }
    .doc-card:hover { 
        transform: translateY(-4px); 
        border-color: rgba(99, 102, 241, 0.55);
        box-shadow: 0 16px 50px rgba(99, 102, 241, 0.15);
    }

    /* ── Citation Cards ── */
    .citation-card {
        background: rgba(10, 12, 22, 0.7); backdrop-filter: blur(10px);
        border: 1px solid rgba(99, 102, 241, 0.2); border-left: 5px solid #818cf8;
        border-radius: 12px; padding: 1.2rem 1.5rem; margin-bottom: 0.9rem;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    .citation-card .cite-header { 
        font-size: 0.82rem; color: #818cf8; font-weight: 600; margin-bottom: 0.5rem; 
        display: flex; justify-content: space-between;
    }
    .citation-card .cite-text { font-size: 0.92rem; color: #cbd5e1; line-height: 1.6; }

    /* ── Key-points box ── */
    .keypoints-box {
        background: rgba(16, 185, 129, 0.05);
        border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 12px;
        padding: 1rem 1.4rem; margin-top: 1rem;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.03);
    }
    .keypoints-box ul { margin: 0; padding-left: 1.2rem; }
    .keypoints-box li { color: #a7f3d0; font-size: 0.92rem; line-height: 1.65; }

    /* ── Badges ── */
    .badge {
        display: inline-block; padding: 0.35rem 0.85rem; border-radius: 9999px;
        font-size: 0.76rem; font-weight: 600; margin-right: 0.5rem; margin-bottom: 0.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15); border: 1px solid rgba(255,255,255,0.05);
        letter-spacing: 0.02em;
    }
    .badge-blue   { background-color: rgba(59,130,246,0.15)!important; color: #93c5fd!important; border-color: rgba(59,130,246,0.3)!important; }
    .badge-green  { background-color: rgba(16,185,129,0.15)!important; color: #6ee7b7!important; border-color: rgba(16,185,129,0.3)!important; }
    .badge-purple { background-color: rgba(139,92,246,0.15)!important; color: #c4b5fd!important; border-color: rgba(139,92,246,0.3)!important; }
    .badge-yellow { background-color: rgba(245,158,11,0.15)!important; color: #fde047!important; border-color: rgba(245,158,11,0.3)!important; }
    .badge-red    { background-color: rgba(239,68,68,0.15)!important;  color: #fca5a5!important; border-color: rgba(239,68,68,0.3)!important; }
    .badge-gray   { background-color: rgba(107,114,128,0.15)!important;color: #d1d5db!important; border-color: rgba(107,114,128,0.3)!important; }
    .badge-teal   { background-color: rgba(6,182,212,0.15)!important;  color: #67e8f9!important; border-color: rgba(6,182,212,0.3)!important; }

    /* ── Chat bubbles ── */
    .chat-bubble {
        border-radius: 20px !important;
        padding: 1.4rem 2rem !important;
        margin-bottom: 1.5rem !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        font-size: 1rem; line-height: 1.65;
    }
    .chat-user {
        background: linear-gradient(135deg, rgba(30,41,59,0.5) 0%, rgba(15,23,42,0.7) 100%) !important;
        border-left: 6px solid #6366f1 !important;
        box-shadow: 0 8px 30px rgba(99,102,241,0.06) !important;
        color: #f1f5f9;
    }
    .chat-assistant {
        background: linear-gradient(135deg, rgba(79,70,229,0.08) 0%, rgba(10,12,22,0.85) 100%) !important;
        border-left: 6px solid #818cf8 !important;
        box-shadow: 0 15px 40px rgba(99,102,241,0.15) !important;
        color: #f8fafc;
    }

    /* ── File Uploader Styling ── */
    section[data-testid="stFileUploader"] {
        background-color: rgba(13, 17, 33, 0.5) !important;
        border: 2px dashed rgba(99, 102, 241, 0.3) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        transition: all 0.25s ease !important;
    }
    section[data-testid="stFileUploader"]:hover {
        border-color: rgba(99, 102, 241, 0.7) !important;
        background-color: rgba(15, 23, 42, 0.8) !important;
    }

    /* ── Scrollbars ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(156,163,175,0.25); border-radius: 9999px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(156,163,175,0.45); }

    /* ── Premium Buttons ── */
    div.stButton > button {
        background: linear-gradient(90deg, #4f46e5 0%, #6366f1 100%) !important;
        color: white !important; border: none !important; border-radius: 12px !important;
        font-weight: 600 !important; font-size: 0.95rem !important;
        padding: 0.65rem 1.6rem !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        box-shadow: 0 6px 20px rgba(79,70,229,0.3) !important;
        letter-spacing: 0.02em !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 30px rgba(79,70,229,0.5) !important;
        border-color: transparent !important;
    }
    div.stButton > button:active { transform: translateY(0) scale(0.98) !important; }

    /* ── Benchmark table ── */
    .bench-pass { color: #34d399 !important; font-weight: 700; }
    .bench-fail { color: #f87171 !important; font-weight: 700; }

    /* ── LLM status pill ── */
    .llm-pill-on  { background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.4);
                    border-radius: 10px; padding: 0.55rem 1rem; color: #6ee7b7; font-size: 0.84rem;
                    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.08); }
    .llm-pill-off { background: rgba(245,158,11,0.12); border: 1px solid rgba(245,158,11,0.35);
                    border-radius: 10px; padding: 0.55rem 1rem; color: #fde047; font-size: 0.84rem; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

def fmt_time(iso_str: str) -> str:
    try:
        return datetime.fromisoformat(iso_str).strftime("%b %d, %Y %I:%M %p")
    except Exception:
        return iso_str


def confidence_badge(conf: str) -> str:
    colour = {"High": "green", "Medium": "blue", "Low": "yellow"}.get(conf, "gray")
    icon   = {"High": "✅", "Medium": "🔵", "Low": "⚠️"}.get(conf, "")
    return f'<span class="badge badge-{colour}">{icon} Confidence: {conf}</span>'


def post_feedback(question: str, answer: str, rating: int):
    try:
        requests.post(
            f"{API_URL}/feedback",
            json={"question": question, "answer": answer, "rating": rating},
            timeout=5,
        )
    except Exception:
        pass


@st.dialog("Knowledge Graph Subgraph", width="large")
def show_entity_graph(entity_id: str):
    st.markdown(f"### Subgraph for **{entity_id}**")
    try:
        r = requests.get(f"{API_URL}/graph/entity/{entity_id}?depth=1", timeout=15)
        if r.status_code == 200:
            data = r.json()
            center = data.get("center", {})
            neighbors = data.get("neighbors", [])
            edges = data.get("edges", [])
            
            def get_color(t):
                t = t.lower() if t else ""
                if t == "equipment": return "#ef4444"
                if t == "permit": return "#8b5cf6"
                if t == "regulation": return "#10b981"
                return "#6b7280"
                
            ag_nodes = [Node(
                id=center["id"],
                label=center.get("label", center["id"]),
                size=25,
                color=get_color(center.get("type")),
                title=f"{center['id']} ({center.get('type')})"
            )]
            
            for n in neighbors:
                ag_nodes.append(Node(
                    id=n["id"],
                    label=n.get("label", n["id"]),
                    size=15,
                    color=get_color(n.get("type")),
                    title=f"{n['id']} ({n.get('type')})"
                ))
                
            ag_edges = [Edge(
                source=e["source"],
                target=e["target"],
                label=e.get("relation_type", ""),
                title=e.get("relation_type", "")
            ) for e in edges]
            
            config = Config(
                width="100%", height=400, directed=False, hierarchical=False,
                node={"font": {"size": 12}},
                physics={
                    "enabled": True, "solver": "barnesHut",
                    "barnesHut": {
                        "gravitationalConstant": -2000,
                        "centralGravity": 0.3,
                        "springLength": 95,
                    },
                },
            )
            
            if AGRAPH_AVAILABLE:
                agraph(nodes=ag_nodes, edges=ag_edges, config=config)
            else:
                st.warning("streamlit-agraph not installed")
        else:
            st.error(f"Entity not found: {r.json().get('detail', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error loading graph: {e}")



# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 1.5rem; margin-bottom: 2rem; background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; backdrop-filter: blur(10px);">
    <div>
        <h1 style="margin: 0; font-size: 1.8rem; font-weight: 800; background: linear-gradient(90deg, #ffffff, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Industrial Knowledge Platform</h1>
        <p style="margin: 0.2rem 0 0 0; font-size: 0.9rem; color: #94a3b8; font-weight: 500;">Unified RAG & Entity Graph Knowledge Retrieval System</p>
    </div>
    <div style="display: flex; gap: 1rem;">
        <div style="text-align: right; border-right: 1px solid rgba(255, 255, 255, 0.1); padding-right: 1rem;">
            <div style="font-size: 0.75rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Engine Status</div>
            <div style="font-size: 0.9rem; color: #10b981; font-weight: 700;">ACTIVE</div>
        </div>
        <div>
            <div style="font-size: 0.75rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Security Level</div>
            <div style="font-size: 0.9rem; color: #818cf8; font-weight: 700;">ENTERPRISE</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1.5rem; padding: 1.2rem; background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(17, 24, 39, 0.8) 100%); border-radius: 14px; border: 1px solid rgba(99, 102, 241, 0.25);">
        <img src="https://img.icons8.com/isometric-line/100/factory.png" width="55" style="margin-bottom: 0.5rem; filter: drop-shadow(0 0 10px rgba(99, 102, 241, 0.5));">
        <h2 style="margin:0; font-size: 1.3rem; font-weight:800; background: linear-gradient(90deg, #818cf8, #c7d2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">IND-INTELLIGENCE</h2>
        <span style="font-size:0.7rem; color:#94a3b8; font-weight:600; letter-spacing:0.05em; text-transform:uppercase;">ET Hackathon PS8</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("### **System Status**")

    # FastAPI health
    try:
        h = requests.get(f"{API_URL}/health", timeout=15)
        if h.status_code == 200:
            st.success("⚡ FastAPI: Connected")
        else:
            st.warning("⚠️ FastAPI: Unhealthy")
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        st.error("❌ FastAPI: Offline")

    # LLM / Ollama status
    st.markdown("---")
    st.markdown("### **LLM Engine**")
    try:
        llm_resp = requests.get(f"{API_URL}/llm/status", timeout=10)
        if llm_resp.status_code == 200:
            ls = llm_resp.json()
            st.session_state["llm_status"] = ls
            nvidia_on = ls.get("nvidia_available", False)
            ollama_on = ls.get("ollama_available", False)
            if nvidia_on:
                model_name = ls.get("model", "nemotron").replace("nvidia/", "").replace("meta/", "")
                st.markdown(
                    f'<div class="llm-pill-on">🟢 NVIDIA API &nbsp;|&nbsp; <b>{model_name}</b></div>',
                    unsafe_allow_html=True,
                )
            elif ollama_on:
                st.markdown(
                    f'<div class="llm-pill-on">🟢 Ollama &nbsp;|&nbsp; <b>{ls["model"]}</b></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="llm-pill-off">🟡 Smart-Context fallback<br>'
                    '<small>Set NVIDIA_API_KEY or start Ollama</small></div>',
                    unsafe_allow_html=True,
                )
    except Exception:
        st.caption("LLM status unavailable")

    # Graph stats
    st.markdown("---")
    try:
        gr = requests.get(f"{API_URL}/entities", timeout=15)
        if gr.status_code == 200:
            gd = gr.json()
            stats = gd.get("stats", {})
            st.markdown("### **Knowledge Graph**")
            c1, c2 = st.columns(2)
            c1.metric("Nodes", stats.get("total_nodes", 0))
            c2.metric("Edges", stats.get("total_edges", 0))
            nt = stats.get("node_types", {})
            if nt:
                with st.expander("Entity Breakdown"):
                    for etype, cnt in sorted(nt.items(), key=lambda x: -x[1]):
                        st.write(f"**{etype.replace('_', ' ').title()}:** {cnt}")
    except Exception:
        pass

    st.markdown("---")
    st.caption("© 2026 Enterprise Industrial Knowledge Engine. Licensed for site operators.")


# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_chat, tab_docs, tab_graph, tab_entities, tab_bench, tab_setup = st.tabs([
    "Query Console",
    "Document Repository",
    "Knowledge Network",
    "Entity Dictionary",
    "System Evaluation",
    "Settings",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — CHAT Q&A (Day 4: real LLM, key-points, feedback)
# ══════════════════════════════════════════════════════════════════════════════
with tab_chat:
    st.subheader("Interactive Query Interface")
    llm_status = st.session_state.get("llm_status", {})
    if llm_status.get("nvidia_available"):
        caption_text = "Powered by **Vector Search + Knowledge Graph + NVIDIA LLM API**."
    elif llm_status.get("ollama_available"):
        caption_text = "Powered by **Vector Search + Knowledge Graph + Local LLM (Ollama)** — no API key required."
    else:
        caption_text = "Powered by **Vector Search + Knowledge Graph + Smart Context Fallback**."
    st.caption(caption_text)

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_answer" not in st.session_state:
        st.session_state.last_answer = None

    # ── Chat history ──────────────────────────────────────────────────────────
    for idx, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-bubble chat-user"><b>You:</b><br>{msg["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            # Answer bubble with markdown
            with st.container():
                conf_badge = confidence_badge(msg.get("confidence", "Medium"))
                model_badge = f'<span class="badge badge-teal">🤖 {msg.get("model_used","")}</span>'
                latency_badge = f'<span class="badge badge-gray">⏱ {msg.get("latency_ms", 0)} ms</span>'
                st.markdown(
                    f'<div class="chat-bubble chat-assistant">'
                    f'<b>System:</b><br>'
                    f'{conf_badge} {model_badge} {latency_badge}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(msg["content"])  # render markdown from LLM

                # Key points
                kp = msg.get("key_points", [])
                if kp:
                    bullets = "".join(f"<li>{p}</li>" for p in kp)
                    st.markdown(
                        f'<div class="keypoints-box"><b style="color:#a7f3d0">📌 Key Points</b>'
                        f'<ul>{bullets}</ul></div>',
                        unsafe_allow_html=True,
                    )

                # Entities
                ents = msg.get("entities_used", [])
                if ents:
                    st.markdown("<small><b>Entities mentioned (click to view graph):</b></small>", unsafe_allow_html=True)
                    cols = st.columns(len(ents[:6]))
                    for i, e in enumerate(ents[:6]):
                        with cols[i]:
                            if st.button(f"⚙ {e}", key=f"ent_btn_{idx}_{i}", use_container_width=True):
                                show_entity_graph(e)

                # Sources expander
                srcs = msg.get("sources", [])
                if srcs:
                    with st.expander(f"📎 {len(srcs)} Source(s) cited", expanded=False):
                        for si, src in enumerate(srcs, 1):
                            score = round(1 - src.get("distance", 0), 3)
                            st.markdown(
                                f'<div class="citation-card">'
                                f'<div class="cite-header">'
                                f'[{si}] <b>{src.get("citation", "Unknown Source")}</b> &nbsp;|&nbsp; relevance: {score}</div>'
                                f'<div class="cite-text">{src.get("excerpt", "")[:350]}…</div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                # Feedback buttons
                q_key = f"fb_{idx}"
                c1, c2, _ = st.columns([1, 1, 8])
                if c1.button("👍", key=f"up_{idx}", help="Good answer"):
                    post_feedback(
                        msg.get("question", ""),
                        msg["content"][:300],
                        +1,
                    )
                    st.toast("Thanks for the feedback!", icon="👍")
                if c2.button("👎", key=f"dn_{idx}", help="Poor answer"):
                    post_feedback(
                        msg.get("question", ""),
                        msg["content"][:300],
                        -1,
                    )
                    st.toast("Feedback logged. We'll improve!", icon="👎")

    # ── Input ─────────────────────────────────────────────────────────────────
    user_query = st.chat_input(
        "Ask a safety or regulatory question… "
        "(e.g. 'What PPE is required for hot work near COMP-C01?')"
    )

    if user_query:
        # Show user bubble immediately
        st.markdown(
            f'<div class="chat-bubble chat-user"><b>You:</b><br>{user_query}</div>',
            unsafe_allow_html=True,
        )
        st.session_state.messages.append({"role": "user", "content": user_query})

        # ── Tier 3.1: Streaming answer via SSE ─────────────────────────────
        answer      = ""
        sources     = []
        confidence  = "Medium"
        key_points  = []
        entities    = []
        model_used  = "unknown"
        latency_ms  = 0

        # Create placeholder for streaming content
        stream_placeholder = st.empty()
        streaming_text = ""

        try:
            import httpx
            with httpx.Client(timeout=120) as client:
                with client.stream(
                    "POST",
                    f"{API_URL}/query/stream",
                    json={"question": user_query, "top_k": 5},
                    headers={"Accept": "text/event-stream"},
                ) as resp:
                    if resp.status_code != 200:
                        st.error(f"API error {resp.status_code}")
                    else:
                        for line in resp.iter_lines():
                            line = line.strip()
                            if not line or not line.startswith("data:"):
                                continue
                            payload_str = line[5:].strip()
                            if not payload_str:
                                continue
                            try:
                                event = json.loads(payload_str)
                            except json.JSONDecodeError:
                                continue

                            etype = event.get("type")
                            content = event.get("content", "")

                            if etype == "token":
                                streaming_text += content
                                stream_placeholder.markdown(streaming_text)
                            elif etype == "metadata":
                                answer      = content.get("answer", streaming_text)
                                sources     = content.get("sources", [])
                                confidence  = content.get("confidence", "Medium")
                                key_points  = content.get("key_points", [])
                                entities    = content.get("entities_used", [])
                                model_used  = content.get("model_used", "unknown")
                                latency_ms  = content.get("latency_ms", 0)
                            elif etype == "error":
                                st.error(f"LLM error: {content}")

        except ImportError:
            # Fallback to non-streaming if httpx not installed
            with st.spinner("🧠 Generating answer…"):
                try:
                    resp = requests.post(
                        f"{API_URL}/query",
                        json={"question": user_query, "top_k": 5},
                        timeout=120,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        answer      = data.get("answer", "")
                        sources     = data.get("sources", [])
                        confidence  = data.get("confidence", "Medium")
                        key_points  = data.get("key_points", [])
                        entities    = data.get("entities_used", [])
                        model_used  = data.get("model_used", "unknown")
                        latency_ms  = data.get("latency_ms", 0)
                        stream_placeholder.markdown(answer)
                    else:
                        st.error(f"API error {resp.status_code}: {resp.text[:200]}")
                except Exception as e:
                    st.error(f"Error: {e}")

        except requests.exceptions.Timeout:
            st.error(
                "⏳ Request timed out (>120 s). If using Ollama for the first time, "
                "it may be loading the model — please try again in a moment."
            )
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot reach the FastAPI server at `localhost:8000`. "
                     "Start it with: `PYTHONPATH=. uvicorn src.main:app --reload`")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

        # ── Render metadata after streaming is complete ─────────────────────
        if answer:
            conf_badge   = confidence_badge(confidence)
            model_badge  = f'<span class="badge badge-teal">🤖 {model_used}</span>'
            latency_badge = f'<span class="badge badge-gray">⏱ {latency_ms} ms</span>'
            st.markdown(
                f'<div class="chat-bubble chat-assistant">'
                f'<b>System:</b><br>{conf_badge} {model_badge} {latency_badge}'
                f'</div>',
                unsafe_allow_html=True,
            )

            if key_points:
                bullets = "".join(f"<li>{p}</li>" for p in key_points)
                st.markdown(
                    f'<div class="keypoints-box"><b style="color:#a7f3d0">📌 Key Points</b>'
                    f'<ul>{bullets}</ul></div>',
                    unsafe_allow_html=True,
                )

            if entities:
                st.markdown("<small><b>Entities mentioned (click to view graph):</b></small>", unsafe_allow_html=True)
                cols = st.columns(len(entities[:6]))
                for i, e in enumerate(entities[:6]):
                    with cols[i]:
                        if st.button(f"⚙ {e}", key=f"ent_btn_live_{i}", use_container_width=True):
                            show_entity_graph(e)

            if sources:
                with st.expander(f"📎 {len(sources)} Source(s) cited", expanded=True):
                    for si, src in enumerate(sources, 1):
                        score = round(1 - src.get("distance", 0), 3)
                        st.markdown(
                            f'<div class="citation-card">'
                            f'<div class="cite-header">'
                            f'[{si}] <b>{src.get("citation", "Unknown Source")}</b> &nbsp;|&nbsp; relevance: {score}</div>'
                            f'<div class="cite-text">{src.get("excerpt", "")[:350]}…</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

            # Save to session
            st.session_state.messages.append({
                "role":        "assistant",
                "content":     answer,
                "confidence":  confidence,
                "key_points":  key_points,
                "entities_used": entities,
                "model_used":  model_used,
                "latency_ms":  latency_ms,
                "sources":     sources,
                "question":    user_query,
            })
            st.session_state.last_answer = answer

    if st.session_state.messages:
        if st.button("🗑️ Clear Chat", use_container_width=False):
            st.session_state.messages = []
            st.session_state.last_answer = None
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DOCUMENT LIBRARY
# ══════════════════════════════════════════════════════════════════════════════
with tab_docs:
    st.subheader("Ingested Documents")
    st.write("Browse regulatory templates and structured plant logs currently indexed in the search index.")

    try:
        docs_resp = requests.get(f"{API_URL}/documents", timeout=5)
        if docs_resp.status_code == 200:
            docs = docs_resp.json()
            if not docs:
                st.info("No documents indexed yet. Go to the **Control Panel** tab to initialise.")
            else:
                file_types = sorted(set(d["type"] for d in docs))
                sel_types  = st.multiselect("Filter by Type", file_types, default=file_types)
                search_q   = st.text_input("Search document names", "")
                filtered   = [
                    d for d in docs
                    if d["type"] in sel_types
                    and (not search_q or search_q.lower() in d["filename"].lower())
                ]
                st.write(f"Showing **{len(filtered)}** of {len(docs)} documents")
                st.markdown("---")

                for doc in filtered:
                    with st.container():
                        st.markdown(f"""
                        <div class="doc-card">
                            <h4 style="margin:0;color:#c7d2fe;">📄 {doc['filename']}</h4>
                            <div style="margin-top:0.5rem;">
                                <span class="badge badge-purple">{doc['type'].upper()}</span>
                                <span class="badge badge-blue">{doc['chunk_count']} chunks</span>
                                <span class="badge badge-gray">📅 {fmt_time(doc['upload_date'])}</span>
                                <span class="badge badge-green">🏷 {doc.get('entities_found', 0)} entities</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        with st.expander(f"Inspect chunks — {doc['filename']}"):
                            if st.button("Load Chunks", key=f"btn_{doc['doc_id']}"):
                                try:
                                    cr = requests.get(f"{API_URL}/documents/{doc['doc_id']}", timeout=5)
                                    if cr.status_code == 200:
                                        cd = cr.json()
                                        st.write(f"**{len(cd['chunks'])} chunks**")
                                        for c in cd["chunks"]:
                                            st.info(
                                                f"Chunk {c['metadata'].get('chunk_index',0)} "
                                                f"· `{c['chunk_id']}`"
                                            )
                                            st.code(c["text"], language=None)
                                    else:
                                        st.error(cr.text)
                                except Exception as err:
                                    st.error(str(err))
                        st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.error(f"Failed to fetch documents: {docs_resp.status_code}")
    except Exception as e:
        st.error(f"Could not connect to API: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — KNOWLEDGE GRAPH
# ══════════════════════════════════════════════════════════════════════════════
with tab_graph:
    st.subheader("Knowledge Graph Visualisation")
    st.write("Interactive entity-relationship graph extracted from the document corpus.")

    try:
        gr = requests.get(f"{API_URL}/graph?max_nodes=200", timeout=10)
        if gr.status_code == 200:
            gd    = gr.json()
            nodes = gd.get("nodes", [])
            edges = gd.get("edges", [])

            if not nodes:
                st.info("Graph is empty. Initialise the corpus first.")
            else:
                st.write(f"**{len(nodes)} nodes** · **{len(edges)} edges**")
                # Format nodes and edges to JSON for HTML injection
                nodes_json = json.dumps(nodes)
                edges_json = json.dumps(edges)
                
                html_code = """
                <div id="3d-graph" style="width: 100%; height: 600px; border-radius: 12px; overflow: hidden; border: 1px solid rgba(99, 102, 241, 0.25); background: #090d16; position: relative;"></div>
                <script>
                  function initGraph() {
                    const elem = document.getElementById('3d-graph');
                    if (!elem) {
                      setTimeout(initGraph, 50);
                      return;
                    }

                    const rawNodes = {nodes_json};
                    const rawEdges = {edges_json};

                    const links = rawEdges.map(e => ({
                      source: e.from,
                      target: e.to,
                      relation: e.relation || 'linked_to'
                    }));

                    const degrees = {};
                    links.forEach(l => {
                      degrees[l.source] = (degrees[l.source] || 0) + 1;
                      degrees[l.target] = (degrees[l.target] || 0) + 1;
                    });

                    const nodes = rawNodes.map(n => ({
                      id: n.id,
                      label: n.id,
                      type: n.type,
                      color: n.color || '#6366f1',
                      val: Math.max(Math.sqrt(degrees[n.id] || 1) * 3, 2.5)
                    }));

                    const Graph = ForceGraph3D()(elem)
                      .graphData({ nodes, links })
                      .backgroundColor('#090d16')
                      .nodeColor(node => node.color)
                      .nodeVal(node => node.val)
                      .nodeLabel(node => {
                        const typeLabel = node.type.replace('_', ' ').toUpperCase();
                        const nodeColor = node.color || '#6366f1';
                        const connCount = degrees[node.id] || 0;
                        return `
                          <div style="
                            background: rgba(9, 13, 22, 0.96);
                            backdrop-filter: blur(12px);
                            border: 1px solid ${nodeColor};
                            box-shadow: 0 10px 25px rgba(0,0,0,0.6), 0 0 12px ${nodeColor}33;
                            border-radius: 10px;
                            padding: 12px 16px;
                            min-width: 180px;
                            color: #f1f5f9;
                            font-family: sans-serif;
                            font-size: 12px;
                            pointer-events: none;
                            line-height: 1.5;
                          ">
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 6px;">
                              <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: ${nodeColor}; box-shadow: 0 0 8px ${nodeColor};"></span>
                              <strong style="color: #fff; font-size: 13px;">${node.id}</strong>
                            </div>
                            <div style="color: #94a3b8; font-size: 10px; margin-bottom: 4px;">
                              CLASS: <span style="color: ${nodeColor}; font-weight: 700; letter-spacing: 0.03em;">${typeLabel}</span>
                            </div>
                            <div style="color: #cbd5e1; font-size: 10px;">
                              CONNECTIONS: <strong style="color: #fff;">${connCount}</strong>
                            </div>
                          </div>
                        `;
                      })
                      .linkLabel(link => `<div style="background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 4px; padding: 4px 8px; color: #cbd5e1; font-family: sans-serif; font-size: 11px;">${link.relation}</div>`)
                      .linkWidth(1.2)
                      .linkColor(() => 'rgba(99, 102, 241, 0.25)')
                      .linkDirectionalParticles(4)
                      .linkDirectionalParticleSpeed(0.007)
                      .linkDirectionalParticleWidth(2.0)
                      .linkDirectionalParticleColor(() => '#a5b4fc');

                    Graph.controls().autoRotate = true;
                    Graph.controls().autoRotateSpeed = 0.6;

                    let rotationTimeout;
                    const controls = Graph.controls();
                    controls.addEventListener('start', () => {
                      controls.autoRotate = false;
                      clearTimeout(rotationTimeout);
                    });
                    controls.addEventListener('end', () => {
                      rotationTimeout = setTimeout(() => {
                        controls.autoRotate = true;
                      }, 5000);
                    });

                    Graph.onNodeClick(node => {
                      const distance = 50;
                      const distRatio = 1 + distance/Math.hypot(node.x, node.y, node.z);

                      Graph.cameraPosition(
                        { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
                        node,
                        2000
                      );

                      let overlay = document.getElementById('node-info-overlay');
                      if (!overlay) {
                        overlay = document.createElement('div');
                        overlay.id = 'node-info-overlay';
                        overlay.style.position = 'absolute';
                        overlay.style.bottom = '15px';
                        overlay.style.right = '15px';
                        overlay.style.background = 'rgba(15, 23, 42, 0.95)';
                        overlay.style.backdropFilter = 'blur(10px)';
                        overlay.style.border = '1px solid rgba(99, 102, 241, 0.4)';
                        overlay.style.borderRadius = '12px';
                        overlay.style.padding = '15px';
                        overlay.style.width = '240px';
                        overlay.style.color = '#fff';
                        overlay.style.fontFamily = 'sans-serif';
                        overlay.style.fontSize = '12px';
                        overlay.style.boxShadow = '0 10px 30px rgba(0,0,0,0.5)';
                        overlay.style.pointerEvents = 'auto';
                        overlay.style.zIndex = '999';
                        elem.appendChild(overlay);
                      }
                      overlay.innerHTML = `
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
                          <strong style="font-size:14px; color:#818cf8;">${node.id}</strong>
                          <span style="font-size:10px; font-weight:600; text-transform:uppercase; padding: 2px 6px; background: rgba(99, 102, 241, 0.2); border-radius: 4px; color: #a5b4fc;">${node.type}</span>
                        </div>
                        <div style="border-top: 1px solid rgba(255,255,255,0.08); padding-top: 8px; color: #94a3b8; line-height: 1.5;">
                          Degree (Connections): <strong>${degrees[node.id] || 0}</strong><br>
                          Status: <span style="color:#10b981;">CONNECTED</span>
                        </div>
                        <div style="margin-top: 8px; text-align: right;">
                          <button onclick="document.getElementById('node-info-overlay').remove()" style="background:transparent; border:none; color:#ef4444; font-size:10px; font-weight:600; cursor:pointer;">Dismiss</button>
                        </div>
                      `;
                    });
                  }
                </script>
                <script src="https://cdn.jsdelivr.net/npm/3d-force-graph" onload="initGraph()"></script>
                """.replace("{nodes_json}", nodes_json).replace("{edges_json}", edges_json)
                import streamlit.components.v1 as components
                components.html(html_code, height=620)
        else:
            st.error(f"Graph API error {gr.status_code}")
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach FastAPI server.")
    except Exception as e:
        st.error(f"Error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — ENTITY EXPLORER
# ══════════════════════════════════════════════════════════════════════════════
with tab_entities:
    st.subheader("Entity Explorer")
    st.write("Browse entities extracted from the document corpus.")

    try:
        er = requests.get(f"{API_URL}/entities", timeout=10)
        if er.status_code == 200:
            ed  = er.json()
            ebt = ed.get("entities", {})
            stats = ed.get("stats", {})

            if not ebt:
                st.info("No entities found. Initialise the corpus first.")
            else:
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Nodes", stats.get("total_nodes", 0))
                c2.metric("Total Edges", stats.get("total_edges", 0))
                c3.metric("Graph Density", f"{stats.get('density', 0):.4f}")
                st.markdown("---")

                sel = st.selectbox(
                    "Filter by Entity Type",
                    sorted(ebt.keys()),
                    format_func=lambda x: x.replace("_", " ").title(),
                )
                if sel:
                    elist = ebt[sel]
                    srch  = st.text_input("Search entities", "", key="ent_srch")
                    if srch:
                        elist = [e for e in elist if srch.lower() in e.lower()]
                    st.write(f"**{len(elist)}** {sel.replace('_',' ').title()} entities")

                    for eid in elist[:50]:
                        with st.container():
                            st.markdown(f"**{eid}**")
                            if st.button("View relationships", key=f"sub_{eid}"):
                                try:
                                    sr = requests.get(
                                        f"{API_URL}/graph/entity/{eid}?depth=1", timeout=5
                                    )
                                    if sr.status_code == 200:
                                        sd = sr.json()
                                        nb = sd.get("neighbors", [])
                                        if nb:
                                            st.write(f"**{len(nb)} connections:**")
                                            for n in nb:
                                                st.markdown(
                                                    f"• *{n['relation']}* → **{n['id']}** ({n['type']})"
                                                )
                                        else:
                                            st.info("No direct connections.")
                                except Exception as ex:
                                    st.error(str(ex))
                            st.markdown("---")

                    if len(elist) > 50:
                        st.info(f"Showing first 50 of {len(elist)} entities.")
        else:
            st.error(f"Entities API error {er.status_code}")
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach FastAPI server.")
    except Exception as e:
        st.error(f"Error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — BENCHMARK  (NEW in Day 4)
# ══════════════════════════════════════════════════════════════════════════════
with tab_bench:
    st.subheader("Accuracy & Latency Metrics Evaluation")
    st.write(
        "Runs the ground-truth verification suite against the active pipeline to evaluate "
        "context retrieval precision, LLM generation semantic similarity, and P95 latency."
    )

    col_run, col_n = st.columns([3, 1])
    with col_n:
        max_q = st.number_input("Questions to run", min_value=1, max_value=18, value=18, step=1)
    with col_run:
        run_btn = st.button("Run Verification Suite", use_container_width=True)

    if run_btn:
        prog_bar = st.progress(0, text="Starting benchmark…")
        with st.spinner(f"Running {max_q} questions against the RAG engine…"):
            try:
                resp = requests.get(
                    f"{API_URL}/benchmark/run?max_questions={max_q}",
                    timeout=600,   # can take a while with Ollama
                )
                if resp.status_code == 200:
                    bdata   = resp.json()
                    total   = bdata["total"]
                    correct = bdata["correct"]
                    acc     = bdata["accuracy_pct"]
                    avg_ms  = bdata["avg_latency_ms"]
                    model   = bdata.get("model_used", "unknown")
                    results = bdata.get("results", [])
                    prog_bar.progress(1.0, text="Done!")

                    # Headline metrics
                    st.markdown("---")
                    mc1, mc2, mc3, mc4 = st.columns(4)
                    mc1.metric("✅ Accuracy", f"{acc}%")
                    mc2.metric("🎯 Correct", f"{correct} / {total}")
                    mc3.metric("⏱ Avg Latency", f"{avg_ms} ms")
                    mc4.metric("🤖 Model", model)

                    # Results table
                    st.markdown("### Detailed Results")
                    for r in results:
                        icon = "✅" if r["passed"] else "❌"
                        sim_info = f" · Sim: {r['similarity']:.2f}" if "similarity" in r else ""
                        with st.expander(
                            f"{icon} [{r['id']}] {r['question']}{sim_info} · {r['latency_ms']} ms",
                            expanded=False,
                        ):
                            st.markdown(f"**Category:** `{r.get('category','')}`")
                            st.markdown(f"**Expected:** {r['expected']}")
                            st.markdown(f"**Got:** {r['got']}")
                            
                            # Semantic info and Keyword overlap info
                            cols = st.columns(2)
                            with cols[0]:
                                if "similarity" in r:
                                    st.markdown(f"**Embedding Similarity:** `{r['similarity']:.3f}`")
                            with cols[1]:
                                if "passed_keyword" in r:
                                    kw_pass = "✅ Pass" if r["passed_keyword"] else "❌ Fail"
                                    st.markdown(f"**Keyword Overlap:** {kw_pass}")

                            conf_col = "green" if r["confidence"] in ["High", 0.85] else "blue"
                            st.markdown(
                                f'<span class="badge badge-{conf_col}">Confidence: {r["confidence"]}</span>',
                                unsafe_allow_html=True,
                            )

                    # Category breakdown
                    st.markdown("### Category Breakdown")
                    from collections import defaultdict
                    cat_stats: dict = defaultdict(lambda: {"pass": 0, "fail": 0})
                    for r in results:
                        cat = r.get("category", "other")
                        if r["passed"]:
                            cat_stats[cat]["pass"] += 1
                        else:
                            cat_stats[cat]["fail"] += 1
                    for cat, s in sorted(cat_stats.items()):
                        total_cat = s["pass"] + s["fail"]
                        pct = round(s["pass"] / total_cat * 100)
                        st.markdown(
                            f"**{cat.replace('_',' ').title()}** — "
                            f"{s['pass']}/{total_cat} ({pct}%)"
                        )
                else:
                    prog_bar.empty()
                    st.error(f"Benchmark API error {resp.status_code}: {resp.text[:300]}")

            except requests.exceptions.Timeout:
                st.error("Benchmark timed out — reduce question count or check Ollama.")
            except requests.exceptions.ConnectionError:
                st.error("Cannot reach FastAPI server.")
            except Exception as e:
                st.error(f"Error: {e}")

    # Static info
    st.markdown("---")
    st.info(
        "**Scoring method:** Embedding similarity (semantic match) via `all-MiniLM-L6-v2`. "
        "A question passes if the cosine similarity is ≥ 0.55 and the expected source documents are retrieved. "
        "Keyword-overlap stats are also tracked for comparison."
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — CONTROL PANEL
# ══════════════════════════════════════════════════════════════════════════════
with tab_setup:
    st.subheader("Vector Database & Corpus Control")
    st.write("Initialise the index or upload new documents.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### **1. Core Corpus Initialisation**")
        st.write(
            "Index all pre-bundled files: OISD / DGMS / Factory Act regulatory docs "
            "plus synthetic work orders, permits, and incident reports."
        )
        if st.button("🚀 Scan & Index Default Corpus", use_container_width=True):
            with st.spinner("Parsing, embedding, and building knowledge graph… (~60 s)"):
                try:
                    r = requests.post(f"{API_URL}/ingest/initialize", timeout=180)
                    if r.status_code == 200:
                        s = r.json()["stats"]
                        st.success(
                            f"✅ Indexed **{s['files_ingested']}** documents · "
                            f"**{s['total_chunks']}** chunks"
                        )
                        st.rerun()
                    else:
                        st.error(f"Error: {r.text}")
                except Exception as e:
                    st.error(str(e))

    with col2:
        st.markdown("### **2. Upload New Documents**")
        st.write("Upload PDF, DOCX, CSV, or TXT files to add to the live search index.")
        uploaded = st.file_uploader(
            "Select Files",
            type=["txt", "pdf", "docx", "csv"],
            accept_multiple_files=True,
        )
        if uploaded:
            if st.button("📤 Ingest Selected Files", use_container_width=True):
                files_payload = [(
                    "files", (uf.name, uf.getvalue(), uf.type)
                ) for uf in uploaded]
                with st.spinner(f"Ingesting {len(uploaded)} files…"):
                    try:
                        r = requests.post(
                            f"{API_URL}/ingest/upload",
                            files=files_payload,
                            timeout=120,
                        )
                        if r.status_code == 200:
                            results = r.json()["results"]
                            ok = sum(1 for x in results if x.get("status") == "success")
                            st.success(f"✅ Uploaded and ingested {ok} file(s)")
                            for x in results:
                                if x.get("status") == "success":
                                    st.write(f"✓ **{x['doc_id']}** · {x['chunk_count']} chunks")
                                else:
                                    st.error(f"✗ **{x['doc_id']}**: {x.get('error')}")
                            st.rerun()
                        else:
                            st.error(f"Upload failed: {r.text}")
                    except Exception as e:
                        st.error(str(e))

    st.markdown("---")
    st.markdown("### **Debug: Raw Vector Search**")
    st.caption("Test retrieval quality without LLM — great for tuning chunk size / top-k.")
    dq = st.text_input("Search query (raw vector similarity)", "quarterly inspection")
    dn = st.slider("Top-k", 1, 10, 5)
    if st.button("🔍 Run Debug Search"):
        try:
            dr = requests.get(f"{API_URL}/debug/search?q={dq}&n={dn}", timeout=15)
            if dr.status_code == 200:
                dd = dr.json()
                st.write(f"**{len(dd['hits'])} hits** (total in DB: {dd['total_in_db']})")
                for h in dd["hits"]:
                    st.markdown(
                        f"**[{h['rank']}]** `{h['doc_id']}` — score: **{h['score']}**"
                    )
                    st.caption(h["excerpt"])
                    st.markdown("---")
            else:
                st.error(dr.text)
        except Exception as e:
            st.error(str(e))
