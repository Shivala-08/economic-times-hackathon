"""Knowledge Explorer — Interactive graph visualization page.

An Obsidian-style graph view over the existing NetworkX knowledge graph.
Users browse entities (equipment, permits, regulations, SOPs, incidents, documents)
and their relationships visually.

New features:
- Path-finding between any two entities
- Graph statistics dashboard
- Interactive color legend with toggle filters
- Breadcrumb navigation trail
- Relationship table view
- Export graph data
"""

import streamlit as st
import requests
import json
import os
from urllib.parse import quote

try:
    from streamlit_agraph import agraph, Node, Edge, Config
    AGRAPH_AVAILABLE = True
except ImportError:
    AGRAPH_AVAILABLE = False

# ── Page Config ──
st.set_page_config(
    page_title="Knowledge Explorer — Industrial Knowledge Intelligence",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = os.getenv("API_URL", "http://localhost:8000")

# ── Node type definitions ──
ALL_NODE_TYPES = [
    "equipment", "regulation", "plant", "permit", "work_order",
    "incident", "inspection", "person", "hazard", "permit_type", "incident_type",
]

NODE_TYPE_LABELS = {
    "equipment": "⚙️ Equipment", "regulation": "📜 Regulation",
    "plant": "🏭 Plant / Location", "permit": "🎫 Permit",
    "work_order": "📋 Work Order", "incident": "🚨 Incident",
    "inspection": "🔍 Inspection", "person": "👤 Person",
    "hazard": "⚠️ Hazard", "permit_type": "🏷️ Permit Type",
    "incident_type": "🏷️ Incident Type",
}

NODE_TYPE_COLORS = {
    "equipment": "#3b82f6", "regulation": "#ef4444", "plant": "#10b981",
    "permit": "#f59e0b", "work_order": "#8b5cf6", "incident": "#ec4899",
    "inspection": "#06b6d4", "person": "#f97316", "hazard": "#dc2626",
    "permit_type": "#d97706", "incident_type": "#db2777",
}

# ── Custom CSS ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Outfit', 'Inter', sans-serif !important;
    }

    .ke-header {
        background: linear-gradient(135deg, #090d16 0%, #1e1b4b 50%, #120636 100%);
        padding: 1.75rem 2.25rem; border-radius: 16px; color: white;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(99, 102, 241, 0.35);
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }
    .ke-header h1 {
        margin: 0; font-size: 2.1rem; font-weight: 800; letter-spacing: -0.02em;
        background: linear-gradient(90deg, #ffffff 0%, #c7d2fe 50%, #818cf8 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .ke-header p { margin: 0.4rem 0 0 0; opacity: 0.85; font-size: 1rem; color: #cbd5e1; }

    .entity-card {
        background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(12px);
        border: 1px solid rgba(99, 102, 241, 0.3); border-left: 5px solid #818cf8;
        border-radius: 14px; padding: 1.25rem 1.5rem; margin-bottom: 1rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); color: #f8fafc;
    }
    .entity-card:hover {
        transform: translateY(-3px); border-color: rgba(99, 102, 241, 0.5);
        box-shadow: 0 12px 28px rgba(99, 102, 241, 0.25);
    }

    .stat-chip {
        display: inline-flex; align-items: center; gap: 0.45rem;
        background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 9999px; padding: 0.35rem 0.8rem; font-size: 0.82rem;
        font-weight: 600; color: #e2e8f0; margin-right: 0.4rem; margin-bottom: 0.4rem;
        transition: all 0.2s ease;
    }
    .stat-chip:hover { background: rgba(30, 41, 59, 0.95); border-color: rgba(255, 255, 255, 0.15); }
    .stat-chip .dot {
        width: 9px; height: 9px; border-radius: 50%; display: inline-block;
        box-shadow: 0 0 6px currentColor;
    }

    .neighbor-row {
        padding: 0.7rem 0.9rem; border-radius: 10px; margin-bottom: 0.45rem;
        font-size: 0.88rem; display: flex; align-items: center; gap: 0.6rem;
        background: rgba(30, 41, 59, 0.35); border: 1px solid rgba(255, 255, 255, 0.04);
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1); color: #e2e8f0;
    }
    .neighbor-row:hover {
        background: rgba(99, 102, 241, 0.12); border-color: rgba(99, 102, 241, 0.3);
        transform: translateX(5px);
    }
    .neighbor-row .n-dot {
        width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
        box-shadow: 0 0 6px currentColor;
    }
    .neighbor-row .n-relation {
        color: #cbd5e1; font-size: 0.75rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.04em; margin-left: auto;
        background: rgba(30, 41, 59, 0.85); padding: 0.15rem 0.45rem;
        border-radius: 5px; border: 1px solid rgba(255,255,255,0.06);
    }

    /* Stats dashboard cards */
    .stats-grid {
        display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.6rem;
        margin-bottom: 1rem;
    }
    .stats-card {
        background: rgba(15, 23, 42, 0.65); backdrop-filter: blur(10px);
        border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 10px;
        padding: 0.75rem 1rem; text-align: center; transition: all 0.2s ease;
    }
    .stats-card:hover { border-color: rgba(99, 102, 241, 0.4); transform: translateY(-2px); }
    .stats-card .stats-value {
        font-size: 1.4rem; font-weight: 800;
        background: linear-gradient(135deg, #818cf8, #6366f1);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .stats-card .stats-label { font-size: 0.72rem; color: #94a3b8; margin-top: 0.2rem; text-transform: uppercase; letter-spacing: 0.05em; }

    /* Path result card */
    .path-result {
        background: rgba(16, 185, 129, 0.06); border: 1px solid rgba(16, 185, 129, 0.25);
        border-radius: 12px; padding: 1rem 1.25rem; margin-top: 0.75rem;
    }
    .path-node {
        display: inline-flex; align-items: center; gap: 0.3rem;
        background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px; padding: 0.25rem 0.6rem; font-size: 0.82rem;
        font-weight: 600; color: #e2e8f0;
    }
    .path-arrow { color: #6366f1; font-size: 1.1rem; margin: 0 0.2rem; }

    /* Breadcrumb trail */
    .breadcrumb-trail {
        display: flex; flex-wrap: wrap; gap: 0.3rem; margin-bottom: 1rem;
        padding: 0.5rem 0.75rem; background: rgba(15, 23, 42, 0.5);
        border-radius: 10px; border: 1px solid rgba(255,255,255,0.06);
    }
    .breadcrumb-item {
        font-size: 0.78rem; color: #94a3b8; cursor: pointer;
        transition: color 0.2s;
    }
    .breadcrumb-item:hover { color: #818cf8; }
    .breadcrumb-sep { color: #4b5563; font-size: 0.78rem; }

    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(156, 163, 175, 0.25); border-radius: 9999px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(156, 163, 175, 0.45); }

    div.stButton > button {
        background: linear-gradient(90deg, #4f46e5 0%, #6366f1 100%) !important;
        color: white !important; border: none !important; border-radius: 10px !important;
        font-weight: 600 !important; font-size: 0.92rem !important;
        padding: 0.55rem 1.4rem !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.25) !important;
    }
    div.stButton > button:hover {
        transform: scale(1.015) translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(79, 70, 229, 0.4) !important;
    }
    div.stButton > button:active { transform: scale(0.98) !important; }
</style>
""", unsafe_allow_html=True)

# ── Initialize session state ──
defaults = {
    "ke_visible_nodes": set(), "ke_visible_edges": [], "ke_expanded_nodes": set(),
    "ke_selected_node": None, "ke_node_metadata_cache": {}, "ke_graph_data_cache": None,
    "ke_ai_query": None, "ke_ai_show_result": False, "ke_breadcrumb": [],
    "ke_graph_stats": None, "ke_show_table": False, "ke_path_source": "",
    "ke_path_target": "", "ke_path_result": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Helper functions ──
def fetch_json(url, timeout=10, use_cache=True):
    if use_cache and hasattr(st.session_state, '_fetch_cache'):
        if url in st.session_state._fetch_cache:
            return st.session_state._fetch_cache[url]
    elif use_cache:
        st.session_state._fetch_cache = {}
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            if use_cache:
                if not hasattr(st.session_state, '_fetch_cache'):
                    st.session_state._fetch_cache = {}
                st.session_state._fetch_cache[url] = data
            return data
    except Exception:
        pass
    return None


def load_initial_graph():
    data = fetch_json(f"{API_URL}/graph/top?n=40")
    if data and data.get("nodes"):
        st.session_state.ke_visible_nodes = {n["id"] for n in data["nodes"]}
        st.session_state.ke_visible_edges = data.get("edges", [])
        st.session_state.ke_graph_data_cache = data
        for n in data["nodes"]:
            st.session_state.ke_expanded_nodes.add(n["id"])
            st.session_state.ke_node_metadata_cache[n["id"]] = n


def expand_node(node_id):
    if node_id in st.session_state.ke_expanded_nodes:
        return
    data = fetch_json(f"{API_URL}/graph/node/{quote(node_id)}")
    if not data or "error" in data:
        return
    st.session_state.ke_node_metadata_cache[node_id] = data
    st.session_state.ke_visible_nodes.add(node_id)
    for n in data.get("neighbors", []):
        st.session_state.ke_visible_nodes.add(n["id"])
    existing_edge_keys = {(e.get("from", ""), e.get("to", "")) for e in st.session_state.ke_visible_edges}
    for n in data.get("neighbors", []):
        key, rev_key = (node_id, n["id"]), (n["id"], node_id)
        if key not in existing_edge_keys and rev_key not in existing_edge_keys:
            st.session_state.ke_visible_edges.append({"from": node_id, "to": n["id"], "relation": n.get("relation", "related_to")})
            existing_edge_keys.add(key)
    st.session_state.ke_expanded_nodes.add(node_id)


def focus_on_node(node_id):
    data = fetch_json(f"{API_URL}/graph/node/{quote(node_id)}")
    if not data or "error" in data:
        return
    st.session_state.ke_node_metadata_cache[node_id] = data
    st.session_state.ke_visible_nodes = {node_id}
    st.session_state.ke_visible_edges = []
    for n in data.get("neighbors", []):
        st.session_state.ke_visible_nodes.add(n["id"])
        st.session_state.ke_node_metadata_cache[n["id"]] = {
            "id": n["id"], "type": n.get("type", "unknown"),
            "color": n.get("color", "#6b7280"), "degree": 0,
        }
        st.session_state.ke_visible_edges.append({
            "from": node_id, "to": n["id"], "relation": n.get("relation", "related_to"),
        })
    st.session_state.ke_expanded_nodes = {node_id}
    st.session_state.ke_selected_node = node_id
    # Update breadcrumb
    bc = st.session_state.ke_breadcrumb
    if not bc or bc[-1] != node_id:
        bc.append(node_id)
        if len(bc) > 15:
            bc.pop(0)


def load_graph_stats():
    stats = fetch_json(f"{API_URL}/graph/stats", use_cache=False)
    if stats:
        st.session_state.ke_graph_stats = stats


# ── HEADER ──
st.markdown("""
<div class="ke-header">
    <h1>🕸️ Knowledge Explorer</h1>
    <p>Interactive graph visualization of industrial entities and their relationships</p>
</div>
""", unsafe_allow_html=True)

if not hasattr(st.session_state, '_fetch_cache'):
    st.session_state._fetch_cache = {}

health = fetch_json(f"{API_URL}/health", timeout=3, use_cache=False)
if not health:
    st.error("⚠️ Cannot connect to the FastAPI backend. Please start the server first.")
    st.stop()

if not st.session_state.ke_visible_nodes:
    with st.spinner("Loading initial graph..."):
        load_initial_graph()

# Load stats if not cached
if not st.session_state.ke_graph_stats:
    load_graph_stats()

# ═══════════════════════════════════════════════
# MAIN LAYOUT: Sidebar | Graph | Detail Panel
# ═══════════════════════════════════════════════

sidebar_col, graph_col, detail_col = st.columns([1, 3, 1.5])

# ── SIDEBAR ──
with sidebar_col:
    st.markdown("### 🔍 Search & Filter")
    with st.form("ke_search_form", clear_on_submit=False):
        search_query = st.text_input("Search entity", placeholder="e.g. P-101, OISD-118...", key="ke_search")
        search_submitted = st.form_submit_button("🔍 Search")

    # Interactive color legend with toggle checkboxes
    st.markdown("#### 🎨 Node Types")
    enabled_types = []
    for ntype in ALL_NODE_TYPES:
        label = NODE_TYPE_LABELS.get(ntype, ntype)
        color = NODE_TYPE_COLORS.get(ntype, "#6b7280")
        if st.checkbox(label, value=True, key=f"ke_filter_{ntype}"):
            enabled_types.append(ntype)

    st.markdown("---")

    # Graph stats mini dashboard
    stats = st.session_state.ke_graph_stats
    if stats:
        st.markdown("#### 📊 Graph Stats")
        st.markdown(f"""
        <div class="stats-grid">
            <div class="stats-card">
                <div class="stats-value">{stats.get('total_nodes', 0)}</div>
                <div class="stats-label">Total Nodes</div>
            </div>
            <div class="stats-card">
                <div class="stats-value">{stats.get('total_edges', 0)}</div>
                <div class="stats-label">Total Edges</div>
            </div>
            <div class="stats-card">
                <div class="stats-value">{stats.get('avg_degree', 0)}</div>
                <div class="stats-label">Avg Connections</div>
            </div>
            <div class="stats-card">
                <div class="stats-value">{stats.get('connected_components', 0)}</div>
                <div class="stats-label">Components</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Node type breakdown
        nt = stats.get("node_types", {})
        if nt:
            with st.expander("📋 Entity Breakdown", expanded=False):
                for etype, cnt in sorted(nt.items(), key=lambda x: -x[1]):
                    color = NODE_TYPE_COLORS.get(etype, "#6b7280")
                    label = NODE_TYPE_LABELS.get(etype, etype)
                    st.markdown(
                        f'<span style="display:flex;align-items:center;gap:0.4rem;margin-bottom:0.3rem;">'
                        f'<span style="width:8px;height:8px;border-radius:50%;background:{color};display:inline-block;"></span>'
                        f'<span style="font-size:0.82rem;color:#e2e8f0;">{label}: <strong>{cnt}</strong></span></span>',
                        unsafe_allow_html=True,
                    )

    st.markdown("---")

    # Visible graph counts
    num_nodes = len(st.session_state.ke_visible_nodes)
    num_edges = len(st.session_state.ke_visible_edges)
    st.metric("Visible Nodes", num_nodes)
    st.metric("Visible Edges", num_edges)

    st.markdown("---")

    # Action buttons
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔄 Reset", use_container_width=True):
            for k in defaults:
                st.session_state[k] = defaults[k] if not isinstance(defaults[k], set) else set()
            st.session_state.ke_breadcrumb = []
            st.session_state.ke_path_result = None
            if hasattr(st.session_state, '_fetch_cache'):
                st.session_state._fetch_cache = {}
            st.rerun()
    with col_b:
        if st.button("📥 Full Graph", use_container_width=True):
            if hasattr(st.session_state, '_fetch_cache'):
                st.session_state._fetch_cache = {}
            data = fetch_json(f"{API_URL}/graph?max_nodes=500", use_cache=False)
            if data and data.get("nodes"):
                st.session_state.ke_visible_nodes = {n["id"] for n in data["nodes"]}
                st.session_state.ke_visible_edges = data.get("edges", [])
                for n in data["nodes"]:
                    st.session_state.ke_expanded_nodes.add(n["id"])
                st.rerun()

    # ── Path Finding Panel ──
    st.markdown("---")
    st.markdown("#### 🔗 Path Finder")
    st.caption("Find shortest path between two entities")

    path_source = st.text_input("From entity", placeholder="e.g. COMP-C01", key="ke_path_src")
    path_target = st.text_input("To entity", placeholder="e.g. OISD-116", key="ke_path_tgt")

    if st.button("🔍 Find Path", use_container_width=True, key="ke_find_path_btn"):
        if path_source and path_target:
            with st.spinner(f"Finding path: {path_source} → {path_target}..."):
                path_result = fetch_json(
                    f"{API_URL}/graph/path?source={quote(path_source)}&target={quote(path_target)}",
                    use_cache=False, timeout=10,
                )
                st.session_state.ke_path_result = path_result
        else:
            st.warning("Please enter both source and target entity IDs.")

    # Display path result
    pr = st.session_state.ke_path_result
    if pr:
        if "error" in pr:
            st.error(pr["error"])
            if st.button("✕ Clear result", use_container_width=True, key="ke_clear_path_err"):
                st.session_state.ke_path_result = None
                st.rerun()
        elif pr.get("path"):
            path_len = pr.get("length", 0)
            path_nodes = pr.get("path", [])
            st.success(f"✅ Path found! **{path_len} hop(s)**")
            st.markdown('<div class="path-result">', unsafe_allow_html=True)
            for i, node_id in enumerate(path_nodes):
                color = "#6b7280"
                for pn in pr.get("path_nodes", []):
                    if pn["id"] == node_id:
                        color = pn.get("color", "#6b7280")
                        break
                st.markdown(
                    f'<span class="path-node">'
                    f'<span style="width:8px;height:8px;border-radius:50%;background:{color};display:inline-block;"></span>'
                    f'{node_id}</span>',
                    unsafe_allow_html=True,
                )
                if i < len(path_nodes) - 1:
                    st.markdown('<span class="path-arrow">→</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Show edge relations
            path_edges = pr.get("path_edges", [])
            if path_edges:
                with st.expander("🔗 Relationship details"):
                    for pe in path_edges:
                        st.markdown(f"**{pe['from']}** — *{pe['relation']}* → **{pe['to']}**")

            # Visualize path in graph
            col_path_viz, col_path_clear = st.columns(2)
            with col_path_viz:
                if st.button("📊 Visualize Path", use_container_width=True, key="ke_viz_path_btn"):
                    st.session_state.ke_visible_nodes = set(path_nodes)
                    st.session_state.ke_visible_edges = []
                    for pe in path_edges:
                        st.session_state.ke_visible_edges.append(pe)
                    # Expand all path nodes
                    for node_id in path_nodes:
                        st.session_state.ke_expanded_nodes.add(node_id)
                        meta = fetch_json(f"{API_URL}/graph/node/{quote(node_id)}", timeout=5)
                        if meta and "error" not in meta:
                            st.session_state.ke_node_metadata_cache[node_id] = meta
                    st.rerun()
            with col_path_clear:
                if st.button("✕ Clear", use_container_width=True, key="ke_clear_path_result"):
                    st.session_state.ke_path_result = None
                    st.rerun()
        else:
            st.info("No path found between these entities.")
            if st.button("✕ Clear", key="ke_clear_path_notfound"):
                st.session_state.ke_path_result = None
                st.rerun()

    # ── Export Graph ──
    st.markdown("---")
    st.markdown("#### 📤 Export")
    # Filter nodes by enabled_types before export
    filtered_nodes = []
    for nid in st.session_state.ke_visible_nodes:
        meta = st.session_state.ke_node_metadata_cache.get(nid, {})
        ntype = meta.get("type", "unknown")
        if ntype in enabled_types:
            filtered_nodes.append({"id": nid, **meta})
    filtered_node_ids = {n["id"] for n in filtered_nodes}
    filtered_edges = [
        e for e in st.session_state.ke_visible_edges
        if e.get("from") in filtered_node_ids and e.get("to") in filtered_node_ids
    ]
    export_data = {
        "nodes": filtered_nodes,
        "edges": filtered_edges,
        "applied_filters": {"enabled_types": enabled_types, "total_visible": len(st.session_state.ke_visible_nodes)},
    }
    st.download_button(
        "📥 Export Graph (JSON)",
        data=json.dumps(export_data, indent=2, default=str),
        file_name="knowledge_graph_export.json",
        mime="application/json",
        use_container_width=True,
    )
    st.caption(f"Exporting {len(filtered_nodes)} nodes / {len(filtered_edges)} edges (filtered by enabled types)")

# ── Handle search ──
if search_query and search_submitted:
    st.session_state.ke_ai_query = None
    st.session_state.ke_ai_show_result = False
    search_data = fetch_json(f"{API_URL}/graph/search?q={quote(search_query)}&limit=20")
    if search_data and search_data.get("results"):
        top_result = search_data["results"][0]
        with st.spinner(f"Focusing on {top_result['id']}..."):
            focus_on_node(top_result["id"])
        if len(search_data["results"]) > 1:
            with sidebar_col:
                st.markdown("#### 🎯 Search Results")
                for r in search_data["results"][:10]:
                    if st.button(f"{r['id']} ({r['type']}, ⬡ {r['degree']})", key=f"ke_sr_{r['id']}"):
                        focus_on_node(r["id"])
                        st.rerun()
    elif search_data and search_data.get("count", 0) == 0:
        st.info(f"No entities found matching '{search_query}'")


# ── Breadcrumb Trail ──
with graph_col:
    if st.session_state.ke_breadcrumb:
        bc_html = ""
        for i, bid in enumerate(st.session_state.ke_breadcrumb):
            bc_html += f'<span class="breadcrumb-item" onclick="">{bid}</span>'
            if i < len(st.session_state.ke_breadcrumb) - 1:
                bc_html += '<span class="breadcrumb-sep"> › </span>'
        st.markdown(f'<div class="breadcrumb-trail">📍 {bc_html}</div>', unsafe_allow_html=True)


# ── GRAPH CANVAS ──
with graph_col:
    if not st.session_state.ke_visible_nodes:
        st.info("Use the sidebar to search, or click **Full Graph** to start.")
    elif not AGRAPH_AVAILABLE:
        st.warning("streamlit-agraph is not installed. Showing data as table.")
        visible_list = list(st.session_state.ke_visible_nodes)
        st.write(f"**{len(visible_list)} visible nodes**")
        st.dataframe([{"id": nid} for nid in sorted(visible_list)[:50]], use_container_width=True, height=400)
    else:
        all_nodes_data = {}
        if st.session_state.ke_graph_data_cache:
            for n in st.session_state.ke_graph_data_cache.get("nodes", []):
                all_nodes_data[n["id"]] = n

        agraph_nodes, agraph_edges, displayed_node_ids = [], [], set()

        for nid in st.session_state.ke_visible_nodes:
            ndata = all_nodes_data.get(nid)
            if not ndata and nid in st.session_state.ke_node_metadata_cache:
                meta = st.session_state.ke_node_metadata_cache[nid]
                ndata = {"id": nid, "type": meta.get("type", "unknown"), "color": meta.get("color", "#6b7280"), "size": meta.get("degree", 5) + 5}
            if not ndata:
                ndata = {"id": nid, "type": "unknown", "color": "#6b7280", "size": 10}

            ntype = ndata.get("type", "unknown")
            if ntype not in enabled_types:
                continue

            color = ndata.get("color", NODE_TYPE_COLORS.get(ntype, "#6b7280"))
            degree = ndata.get("size", 10) - 5 if isinstance(ndata.get("size"), (int, float)) else 5

            if nid == st.session_state.ke_selected_node:
                color = "#fbbf24"
                size = max(degree * 3, 25)
            else:
                size = max(degree * 2, 12)

            label = nid if len(nid) <= 22 else nid[:20] + ".."
            agraph_nodes.append(Node(id=nid, label=label, color=color, size=size,
                                     title=f"{nid}\nType: {ntype}\nConnections: {degree}",
                                     borderWidth=3 if nid == st.session_state.ke_selected_node else 1))
            displayed_node_ids.add(nid)

        for edge in st.session_state.ke_visible_edges:
            src, tgt = edge.get("from", ""), edge.get("to", "")
            if src in displayed_node_ids and tgt in displayed_node_ids:
                agraph_edges.append(Edge(source=src, target=tgt,
                                         label=edge.get("relation", "")[:18],
                                         title=edge.get("relation", "")))

        if not agraph_nodes:
            st.info("No nodes match the current filters. Adjust filters in the sidebar.")
        else:
            st.caption(f"Showing **{len(agraph_nodes)}** nodes · **{len(agraph_edges)}** edges  ·  Click a node to expand & see details →")

            config = Config(
                width="100%", height=620, directed=False, hierarchical=False,
                node={"font": {"size": 11, "color": "#374151"}},
                edge={"font": {"size": 9, "color": "#9ca3af"}, "smooth": {"type": "continuous"}},
                physics={"enabled": True, "solver": "barnesHut",
                         "barnesHut": {"gravitationalConstant": -4000, "centralGravity": 0.12,
                                       "springLength": 120, "springConstant": 0.04, "damping": 0.09, "avoidOverlap": 0.6},
                         "stabilization": {"enabled": True, "iterations": 150, "fit": True}, "minVelocity": 0.75},
                interaction={"hover": True, "tooltipDelay": 100},
            )

            returned_value = agraph(nodes=agraph_nodes, edges=agraph_edges, config=config)

            if returned_value is not None:
                clicked_id = None
                try:
                    if isinstance(returned_value, str):
                        clicked_id = returned_value
                    elif isinstance(returned_value, dict):
                        clicked_id = returned_value.get("id")
                        if not clicked_id and "nodes" in returned_value:
                            nodes_val = returned_value["nodes"]
                            if isinstance(nodes_val, list) and nodes_val:
                                clicked_id = nodes_val[0]
                    elif isinstance(returned_value, list) and returned_value:
                        clicked_id = returned_value[0]
                except Exception:
                    pass

                if clicked_id and clicked_id in displayed_node_ids and clicked_id != st.session_state.ke_selected_node:
                    st.session_state.ke_ai_query = None
                    st.session_state.ke_ai_show_result = False
                    st.session_state.ke_selected_node = clicked_id
                    with st.spinner(f"Expanding {clicked_id}..."):
                        expand_node(clicked_id)
                    st.rerun()

    # ── Toggle Relationship Table View ──
    if st.session_state.ke_visible_edges:
        st.markdown("---")
        if st.button("📋 Toggle Relationship Table", key="ke_toggle_table"):
            st.session_state.ke_show_table = not st.session_state.ke_show_table

        if st.session_state.ke_show_table:
            st.markdown("#### 📋 Relationships")
            edge_data = []
            for e in st.session_state.ke_visible_edges:
                edge_data.append({
                    "Source": e.get("from", ""),
                    "Relation": e.get("relation", ""),
                    "Target": e.get("to", ""),
                })
            if edge_data:
                st.dataframe(edge_data, use_container_width=True, height=300)


# ── DETAIL PANEL ──
with detail_col:
    selected = st.session_state.ke_selected_node

    if selected:
        st.markdown("### 📋 Entity Details")

        meta = st.session_state.ke_node_metadata_cache.get(selected)
        if not meta:
            with st.spinner("Loading details..."):
                meta = fetch_json(f"{API_URL}/graph/node/{quote(selected)}")
                if meta and "error" not in meta:
                    st.session_state.ke_node_metadata_cache[selected] = meta

        if meta and "error" not in meta:
            ntype = meta.get("type", "unknown")
            color = meta.get("color", NODE_TYPE_COLORS.get(ntype, "#6b7280"))
            degree = meta.get("degree", 0)
            doc_id = meta.get("doc_id")

            st.markdown(f"""
            <div class="entity-card">
                <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;">
                    <span style="width:14px;height:14px;border-radius:50%;background:{color};display:inline-block;"></span>
                    <strong style="font-size:1.1rem;">{selected}</strong>
                </div>
                <div style="display:flex;gap:0.5rem;flex-wrap:wrap;">
                    <span class="stat-chip"><span class="dot" style="background:{color};"></span>{ntype.replace('_', ' ').title()}</span>
                    <span class="stat-chip">⬡ {degree} connections</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if doc_id:
                st.markdown(f"**📄 Source Document:** `{doc_id}`")

            st.markdown("---")

            # Connected entities grouped by type
            st.markdown("#### 🔗 Connected Entities")
            neighbor_types = meta.get("neighbor_types", {})
            if neighbor_types:
                for ntype_key, nids in sorted(neighbor_types.items()):
                    ncolor = NODE_TYPE_COLORS.get(ntype_key, "#6b7280")
                    label = NODE_TYPE_LABELS.get(ntype_key, ntype_key)
                    st.markdown(f"**{label}** ({len(nids)})")
                    for nid in nids[:15]:
                        relation = ""
                        for nb in meta.get("neighbors", []):
                            if nb["id"] == nid:
                                relation = nb.get("relation", "")
                                break
                        st.markdown(f"""
                        <div class="neighbor-row">
                            <span class="n-dot" style="background:{ncolor};"></span>
                            <span><strong>{nid}</strong></span>
                            <span class="n-relation">{relation}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"→ {nid}", key=f"ke_nav_{nid}", help=f"Focus on {nid}"):
                            focus_on_node(nid)
                            st.rerun()
                    if len(nids) > 15:
                        st.caption(f"...and {len(nids) - 15} more")
            else:
                st.info("No direct connections found.")

            st.markdown("---")

            # Quick path from selected node
            st.markdown("#### 🔗 Quick Path")
            path_target_quick = st.text_input("Find path to...", placeholder="e.g. OISD-116", key="ke_quick_path")
            if st.button("🔍 Find Path", key="ke_quick_path_btn", use_container_width=True):
                if path_target_quick:
                    with st.spinner(f"Finding path: {selected} → {path_target_quick}..."):
                        pr = fetch_json(
                            f"{API_URL}/graph/path?source={quote(selected)}&target={quote(path_target_quick)}",
                            use_cache=False, timeout=10,
                        )
                        if pr and "error" not in pr and pr.get("path"):
                            st.success(f"✅ Path: **{pr['length']} hop(s)**")
                            path_display = " → ".join(pr["path"])
                            st.markdown(f"`{path_display}`")
                        elif pr:
                            st.error(pr.get("error", "No path found"))

            st.markdown("---")

            # Ask AI
            st.markdown("#### 🤖 Ask AI")
            entity_context = f"Tell me about {selected} ({ntype}). What are its relationships, regulations, and history?"
            if st.button("🤖 Ask AI about this", key="ke_ask_ai", use_container_width=True):
                st.session_state.ke_ai_query = entity_context
                st.session_state.ke_ai_show_result = True
                st.rerun()

            if st.session_state.get("ke_ai_show_result") and st.session_state.get("ke_ai_query"):
                ai_query = st.session_state.ke_ai_query
                st.info(f"**Querying:** {ai_query}")
                with st.spinner("AI is analyzing this entity..."):
                    try:
                        resp = requests.post(f"{API_URL}/query", json={"question": ai_query, "top_k": 5}, timeout=120)
                        if resp.status_code == 200:
                            data = resp.json()
                            st.markdown(f"**Confidence:** `{data.get('confidence', 'Unknown')}`")
                            if data.get("entities_used"):
                                st.markdown(f"**Entities referenced:** {', '.join(data['entities_used'][:5])}")
                            st.markdown(data.get("answer", "No answer found."))
                            if data.get("sources"):
                                with st.expander("📚 View Sources"):
                                    for idx, src in enumerate(data["sources"]):
                                        st.markdown(f"**[{idx+1}] {src['citation']}** (Distance: `{src.get('distance', 0):.4f}`)")
                                        st.caption(f'Excerpt: *"{src.get("excerpt", "")[:200]}..."*')
                        else:
                            st.error(f"Query failed (Status {resp.status_code})")
                    except Exception as e:
                        st.error(f"Failed to query AI: {e}")

                if st.button("Clear", key="ke_ai_clear"):
                    st.session_state.ke_ai_query = None
                    st.session_state.ke_ai_show_result = False
                    st.rerun()

        elif meta and "error" in meta:
            st.error(f"Entity not found: {meta['error']}")
        else:
            st.warning("Could not load entity details.")
    else:
        st.markdown("### 📋 Entity Details")
        st.info("Click a node in the graph to see its details here.")
        st.markdown("---")
        st.markdown("""
**How to use Knowledge Explorer:**

1. 🔍 **Search** for an entity by name in the sidebar
2. ☑️ **Filter** by node type using the color legend checkboxes
3. 🖱️ **Click** a node to expand its neighbors and see details
4. 🔗 **Path Finder** — find shortest path between any two entities
5. 📊 **Stats** — view graph statistics in the sidebar
6. 📋 **Relationship Table** — toggle to see all edges in a table
7. 📤 **Export** — download the visible graph as JSON
8. 📍 **Breadcrumbs** — navigate back through your exploration trail
        """)
