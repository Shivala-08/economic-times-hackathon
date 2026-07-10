"""Knowledge Explorer — Interactive graph visualization page.

An Obsidian-style graph view over the existing NetworkX knowledge graph.
Users browse entities (equipment, permits, regulations, SOPs, incidents, documents)
and their relationships visually.
"""

import streamlit as st
import requests
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
    "equipment",
    "regulation",
    "plant",
    "permit",
    "work_order",
    "incident",
    "inspection",
    "person",
    "hazard",
    "permit_type",
    "incident_type",
]

NODE_TYPE_LABELS = {
    "equipment": "⚙️ Equipment",
    "regulation": "📜 Regulation",
    "plant": "🏭 Plant / Location",
    "permit": "🎫 Permit",
    "work_order": "📋 Work Order",
    "incident": "🚨 Incident",
    "inspection": "🔍 Inspection",
    "person": "👤 Person",
    "hazard": "⚠️ Hazard",
    "permit_type": "🏷️ Permit Type",
    "incident_type": "🏷️ Incident Type",
}

NODE_TYPE_COLORS = {
    "equipment": "#3b82f6",
    "regulation": "#ef4444",
    "plant": "#10b981",
    "permit": "#f59e0b",
    "work_order": "#8b5cf6",
    "incident": "#ec4899",
    "inspection": "#06b6d4",
    "person": "#f97316",
    "hazard": "#dc2626",
    "permit_type": "#d97706",
    "incident_type": "#db2777",
}

# ── Custom CSS ──
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global Typography Override */
    html, body, [class*="css"], .stApp {
        font-family: 'Outfit', 'Inter', sans-serif !important;
    }

    /* Immersive Animated Gradient Header */
    .ke-header {
        background: linear-gradient(135deg, #090d16 0%, #1e1b4b 50%, #120636 100%);
        padding: 1.75rem 2.25rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        border: 1px solid rgba(99, 102, 241, 0.35);
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
    }
    .ke-header h1 {
        margin: 0;
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(90deg, #ffffff 0%, #c7d2fe 50%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .ke-header p {
        margin: 0.4rem 0 0 0;
        opacity: 0.85;
        font-size: 1rem;
        color: #cbd5e1;
    }

    /* Glassmorphic Entity Detail Card */
    .entity-card {
        background: rgba(15, 23, 42, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-left: 5px solid #818cf8;
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        color: #f8fafc;
    }
    .entity-card:hover {
        transform: translateY(-3px);
        border-color: rgba(99, 102, 241, 0.5);
        box-shadow: 0 12px 28px rgba(99, 102, 241, 0.25);
        border-left-color: #6366f1;
    }

    /* Premium Stat Chips */
    .stat-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 9999px;
        padding: 0.35rem 0.8rem;
        font-size: 0.82rem;
        font-weight: 600;
        color: #e2e8f0;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
        transition: all 0.2s ease;
    }
    .stat-chip:hover {
        background: rgba(30, 41, 59, 0.95);
        border-color: rgba(255, 255, 255, 0.15);
    }
    .stat-chip .dot {
        width: 9px;
        height: 9px;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 6px currentColor;
    }

    /* Sleek Neighbor Relation Rows */
    .neighbor-row {
        padding: 0.7rem 0.9rem;
        border-radius: 10px;
        margin-bottom: 0.45rem;
        font-size: 0.88rem;
        display: flex;
        align-items: center;
        gap: 0.6rem;
        background: rgba(30, 41, 59, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.04);
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        color: #e2e8f0;
    }
    .neighbor-row:hover {
        background: rgba(99, 102, 241, 0.12);
        border-color: rgba(99, 102, 241, 0.3);
        transform: translateX(5px);
    }
    .neighbor-row .n-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        flex-shrink: 0;
        box-shadow: 0 0 6px currentColor;
    }
    .neighbor-row .n-relation {
        color: #cbd5e1;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-left: auto;
        background: rgba(30, 41, 59, 0.85);
        padding: 0.15rem 0.45rem;
        border-radius: 5px;
        border: 1px solid rgba(255,255,255,0.06);
    }

    /* Custom Webkit Scrollbars */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(156, 163, 175, 0.25);
        border-radius: 9999px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(156, 163, 175, 0.45);
    }

    /* Immersive glowing buttons */
    div.stButton > button {
        background: linear-gradient(90deg, #4f46e5 0%, #6366f1 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        padding: 0.55rem 1.4rem !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.25) !important;
    }
    div.stButton > button:hover {
        transform: scale(1.015) translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(79, 70, 229, 0.4) !important;
        background: linear-gradient(90deg, #4f46e5 0%, #818cf8 100%) !important;
    }
    div.stButton > button:active {
        transform: scale(0.98) !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ── Initialize session state ──
if "ke_visible_nodes" not in st.session_state:
    st.session_state.ke_visible_nodes = set()
if "ke_visible_edges" not in st.session_state:
    st.session_state.ke_visible_edges = []
if "ke_expanded_nodes" not in st.session_state:
    st.session_state.ke_expanded_nodes = set()
if "ke_selected_node" not in st.session_state:
    st.session_state.ke_selected_node = None
if "ke_node_metadata_cache" not in st.session_state:
    st.session_state.ke_node_metadata_cache = {}
if "ke_graph_data_cache" not in st.session_state:
    st.session_state.ke_graph_data_cache = None
if "ke_ai_query" not in st.session_state:
    st.session_state.ke_ai_query = None
if "ke_ai_show_result" not in st.session_state:
    st.session_state.ke_ai_show_result = False


# ── Helper functions ──
def fetch_json(url, timeout=10, use_cache=True):
    """Fetch JSON from API with optional session state caching.
    
    Args:
        url: The API endpoint URL.
        timeout: Request timeout in seconds.
        use_cache: If True, cache GET requests in session state.
    
    Returns:
        Parsed JSON dict or None.
    """
    # Check cache first (only for GET requests)
    if use_cache and hasattr(st.session_state, '_fetch_cache'):
        if url in st.session_state._fetch_cache:
            return st.session_state._fetch_cache[url]
    elif use_cache:
        st.session_state._fetch_cache = {}
    
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            # Cache successful responses
            if use_cache:
                if not hasattr(st.session_state, '_fetch_cache'):
                    st.session_state._fetch_cache = {}
                st.session_state._fetch_cache[url] = data
            return data
    except Exception:
        pass
    return None


def load_initial_graph():
    """Load top N most-connected nodes for initial view."""
    data = fetch_json(f"{API_URL}/graph/top?n=40")
    if data and data.get("nodes"):
        st.session_state.ke_visible_nodes = {n["id"] for n in data["nodes"]}
        st.session_state.ke_visible_edges = data.get("edges", [])
        st.session_state.ke_graph_data_cache = data
        # Cache metadata for all loaded nodes so we know their types
        for n in data["nodes"]:
            st.session_state.ke_expanded_nodes.add(n["id"])
            st.session_state.ke_node_metadata_cache[n["id"]] = n


def expand_node(node_id):
    """Expand a single node: fetch its neighbors and add to visible set.

    If the node has already been expanded, this is a no-op.
    """
    if node_id in st.session_state.ke_expanded_nodes:
        return

    data = fetch_json(f"{API_URL}/graph/node/{quote(node_id)}")
    if not data or "error" in data:
        return

    # Cache full metadata (includes neighbors list)
    st.session_state.ke_node_metadata_cache[node_id] = data

    # Add center node
    st.session_state.ke_visible_nodes.add(node_id)

    # Add neighbors
    for n in data.get("neighbors", []):
        st.session_state.ke_visible_nodes.add(n["id"])

    # Add edges between center and neighbors
    existing_edge_keys = {
        (e.get("from", ""), e.get("to", "")) for e in st.session_state.ke_visible_edges
    }
    for n in data.get("neighbors", []):
        key = (node_id, n["id"])
        rev_key = (n["id"], node_id)
        if key not in existing_edge_keys and rev_key not in existing_edge_keys:
            st.session_state.ke_visible_edges.append({
                "from": node_id,
                "to": n["id"],
                "relation": n.get("relation", "related_to"),
            })
            existing_edge_keys.add(key)

    st.session_state.ke_expanded_nodes.add(node_id)


def focus_on_node(node_id):
    """Focus the graph on a specific node: expand it and its neighbors, clear rest.

    Resets visible state to only the target node and its immediate neighbors.
    """
    data = fetch_json(f"{API_URL}/graph/node/{quote(node_id)}")
    if not data or "error" in data:
        return

    st.session_state.ke_node_metadata_cache[node_id] = data
    st.session_state.ke_visible_nodes = {node_id}
    st.session_state.ke_visible_edges = []

    for n in data.get("neighbors", []):
        st.session_state.ke_visible_nodes.add(n["id"])
        # Cache neighbor metadata too (type info)
        st.session_state.ke_node_metadata_cache[n["id"]] = {
            "id": n["id"],
            "type": n.get("type", "unknown"),
            "color": n.get("color", "#6b7280"),
            "degree": 0,  # unknown until expanded
        }
        st.session_state.ke_visible_edges.append({
            "from": node_id,
            "to": n["id"],
            "relation": n.get("relation", "related_to"),
        })

    st.session_state.ke_expanded_nodes = {node_id}
    st.session_state.ke_selected_node = node_id


# ── HEADER ──
st.markdown(
    """
<div class="ke-header">
    <h1>🕸️ Knowledge Explorer</h1>
    <p>Interactive graph visualization of industrial entities and their relationships</p>
</div>
""",
    unsafe_allow_html=True,
)

# ── Initialize fetch cache if needed ──
if not hasattr(st.session_state, '_fetch_cache'):
    st.session_state._fetch_cache = {}

# ── Check backend connection ──
health = fetch_json(f"{API_URL}/health", timeout=3, use_cache=False)
if not health:
    st.error("⚠️ Cannot connect to the FastAPI backend. Please start the server first.")
    st.stop()

# ── Load initial graph if empty ──
if not st.session_state.ke_visible_nodes:
    with st.spinner("Loading initial graph..."):
        load_initial_graph()

# ═══════════════════════════════════════════════
# MAIN LAYOUT: Sidebar | Graph | Detail Panel
# ═══════════════════════════════════════════════

sidebar_col, graph_col, detail_col = st.columns([1, 3, 1.5])

# ── SIDEBAR ──
with sidebar_col:
    st.markdown("### 🔍 Search & Filter")

    # Search form with button to debounce API calls
    with st.form("ke_search_form", clear_on_submit=False):
        search_query = st.text_input(
            "Search entity",
            placeholder="e.g. P-101, OISD-118...",
            key="ke_search",
        )
        search_submitted = st.form_submit_button("🔍 Search")

    # Filter checkboxes
    st.markdown("#### Node Types")
    enabled_types = []
    for ntype in ALL_NODE_TYPES:
        label = NODE_TYPE_LABELS.get(ntype, ntype)
        color = NODE_TYPE_COLORS.get(ntype, "#6b7280")
        if st.checkbox(label, value=True, key=f"ke_filter_{ntype}"):
            enabled_types.append(ntype)

    st.markdown("---")

    # Graph stats
    num_nodes = len(st.session_state.ke_visible_nodes)
    num_edges = len(st.session_state.ke_visible_edges)
    st.metric("Visible Nodes", num_nodes)
    st.metric("Visible Edges", num_edges)

    st.markdown("---")

    # Action buttons
    if st.button("🔄 Reset View", use_container_width=True):
        st.session_state.ke_visible_nodes = set()
        st.session_state.ke_visible_edges = []
        st.session_state.ke_expanded_nodes = set()
        st.session_state.ke_selected_node = None
        st.session_state.ke_node_metadata_cache = {}
        st.session_state.ke_graph_data_cache = None
        st.session_state.ke_ai_query = None
        st.session_state.ke_ai_show_result = False
        if hasattr(st.session_state, '_fetch_cache'):
            st.session_state._fetch_cache = {}
        st.rerun()

    if st.button("📥 Load Full Graph", use_container_width=True):
        if hasattr(st.session_state, '_fetch_cache'):
            st.session_state._fetch_cache = {}
        data = fetch_json(f"{API_URL}/graph?max_nodes=500", use_cache=False)
        if data and data.get("nodes"):
            st.session_state.ke_visible_nodes = {n["id"] for n in data["nodes"]}
            st.session_state.ke_visible_edges = data.get("edges", [])
            for n in data["nodes"]:
                st.session_state.ke_expanded_nodes.add(n["id"])
            st.rerun()


# ── Handle search (only on form submit to debounce) ──
if search_query and search_submitted:
    # Clear AI state when performing a new search
    st.session_state.ke_ai_query = None
    st.session_state.ke_ai_show_result = False
    search_data = fetch_json(
        f"{API_URL}/graph/search?q={quote(search_query)}&limit=20"
    )
    if search_data and search_data.get("results"):
        # Focus on first result
        top_result = search_data["results"][0]
        with st.spinner(f"Focusing on {top_result['id']}..."):
            focus_on_node(top_result["id"])

        # Show other matches in sidebar
        if len(search_data["results"]) > 1:
            with sidebar_col:
                st.markdown("#### 🎯 Search Results")
                for r in search_data["results"][:10]:
                    if st.button(
                        f"{r['id']} ({r['type']}, ⬡ {r['degree']})",
                        key=f"ke_sr_{r['id']}",
                    ):
                        focus_on_node(r["id"])
                        st.rerun()

    elif search_data and search_data.get("count", 0) == 0:
        st.info(f"No entities found matching '{search_query}'")

# ── Handle node click (from agraph return value) ──
# We pass a selected_node via session state from the graph section below


# ── GRAPH CANVAS ──
with graph_col:
    if not st.session_state.ke_visible_nodes:
        st.info("Use the sidebar to search, or click **Load Full Graph** to start.")
    elif not AGRAPH_AVAILABLE:
        st.warning("streamlit-agraph is not installed. Showing data as table.")
        visible_list = list(st.session_state.ke_visible_nodes)
        st.write(f"**{len(visible_list)} visible nodes**")
        st.dataframe(
            [{"id": nid} for nid in sorted(visible_list)[:50]],
            use_container_width=True,
            height=400,
        )
    else:
        # Filter visible nodes by enabled types
        all_nodes_data = {}
        # Build a quick lookup from the graph data cache
        if st.session_state.ke_graph_data_cache:
            for n in st.session_state.ke_graph_data_cache.get("nodes", []):
                all_nodes_data[n["id"]] = n

        # Re-fetch visible nodes metadata if not in cache
        # For efficiency, we store minimal data in visible_nodes set
        # and need to get type info from either cache or metadata
        agraph_nodes = []
        agraph_edges = []
        displayed_node_ids = set()

        for nid in st.session_state.ke_visible_nodes:
            # Try to get type from cache
            ndata = all_nodes_data.get(nid)

            # Also check node metadata cache
            if not ndata and nid in st.session_state.ke_node_metadata_cache:
                meta = st.session_state.ke_node_metadata_cache[nid]
                ndata = {
                    "id": nid,
                    "type": meta.get("type", "unknown"),
                    "color": meta.get("color", "#6b7280"),
                    "size": meta.get("degree", 5) + 5,
                }

            if not ndata:
                # Fallback: minimal node
                ndata = {"id": nid, "type": "unknown", "color": "#6b7280", "size": 10}

            ntype = ndata.get("type", "unknown")
            if ntype not in enabled_types:
                continue

            color = ndata.get("color", NODE_TYPE_COLORS.get(ntype, "#6b7280"))
            degree = ndata.get("size", 10) - 5 if isinstance(ndata.get("size"), (int, float)) else 5

            # Highlight selected node
            if nid == st.session_state.ke_selected_node:
                color = "#fbbf24"  # gold
                size = max(degree * 3, 25)
            else:
                size = max(degree * 2, 12)

            label = nid if len(nid) <= 22 else nid[:20] + ".."

            agraph_nodes.append(Node(
                id=nid,
                label=label,
                color=color,
                size=size,
                title=f"{nid}\nType: {ntype}\nConnections: {degree}",
                borderWidth=3 if nid == st.session_state.ke_selected_node else 1,
            ))
            displayed_node_ids.add(nid)

        # Filter edges
        for edge in st.session_state.ke_visible_edges:
            src = edge.get("from", "")
            tgt = edge.get("to", "")
            if src in displayed_node_ids and tgt in displayed_node_ids:
                agraph_edges.append(Edge(
                    source=src,
                    target=tgt,
                    label=edge.get("relation", "")[:18],
                    title=edge.get("relation", ""),
                ))

        if not agraph_nodes:
            st.info("No nodes match the current filters. Adjust filters in the sidebar.")
        else:
            st.caption(f"Showing **{len(agraph_nodes)}** nodes · **{len(agraph_edges)}** edges  ·  Click a node to expand & see details →")

            physics_config = {
                "enabled": True,
                "solver": "barnesHut",
                "barnesHut": {
                    "gravitationalConstant": -4000,
                    "centralGravity": 0.12,
                    "springLength": 120,
                    "springConstant": 0.04,
                    "damping": 0.09,
                    "avoidOverlap": 0.6,
                },
                "stabilization": {
                    "enabled": True,
                    "iterations": 150,
                    "fit": True,
                },
                "minVelocity": 0.75,
            }

            config = Config(
                width="100%",
                height=620,
                directed=False,
                hierarchical=False,
                node={"font": {"size": 11, "color": "#374151"}},
                edge={"font": {"size": 9, "color": "#9ca3af"}, "smooth": {"type": "continuous"}},
                physics=physics_config,
                interaction={"hover": True, "tooltipDelay": 100},
            )

            returned_value = agraph(
                nodes=agraph_nodes,
                edges=agraph_edges,
                config=config,
            )

            # Handle node click: agraph returns the clicked node id
            # streamlit-agraph may return: str, dict with 'id' or 'nodes', or a list
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
                    # Clear AI state when selecting a different node
                    st.session_state.ke_ai_query = None
                    st.session_state.ke_ai_show_result = False
                    st.session_state.ke_selected_node = clicked_id
                    # Expand the clicked node lazily (only if not already expanded)
                    with st.spinner(f"Expanding {clicked_id}..."):
                        expand_node(clicked_id)
                    st.rerun()


# ── DETAIL PANEL ──
with detail_col:
    selected = st.session_state.ke_selected_node

    if selected:
        st.markdown("### 📋 Entity Details")

        # Fetch metadata (from cache or API)
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

            # Entity header
            st.markdown(
                f"""<div class="entity-card">
                    <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;">
                        <span style="width:14px;height:14px;border-radius:50%;background:{color};display:inline-block;"></span>
                        <strong style="font-size:1.1rem;">{selected}</strong>
                    </div>
                    <div style="display:flex;gap:0.5rem;flex-wrap:wrap;">
                        <span class="stat-chip"><span class="dot" style="background:{color};"></span>{ntype.replace('_', ' ').title()}</span>
                        <span class="stat-chip">⬡ {degree} connections</span>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

            # Source document
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
                        # Find the relation
                        relation = ""
                        for nb in meta.get("neighbors", []):
                            if nb["id"] == nid:
                                relation = nb.get("relation", "")
                                break
                        st.markdown(
                            f"""<div class="neighbor-row">
                                <span class="n-dot" style="background:{ncolor};"></span>
                                <span><strong>{nid}</strong></span>
                                <span class="n-relation">{relation}</span>
                            </div>""",
                            unsafe_allow_html=True,
                        )
                        # Click to navigate
                        if st.button(f"→ {nid}", key=f"ke_nav_{nid}", help=f"Focus on {nid}"):
                            focus_on_node(nid)
                            st.rerun()
                    if len(nids) > 15:
                        st.caption(f"...and {len(nids) - 15} more")
            else:
                st.info("No direct connections found.")

            st.markdown("---")

            # "Ask AI" button — sends entity context to /query endpoint
            st.markdown("#### 🤖 Ask AI")
            entity_context = f"Tell me about {selected} ({ntype}). What are its relationships, regulations, and history?"
            if st.button(
                "🤖 Ask AI about this",
                key="ke_ask_ai",
                use_container_width=True,
            ):
                st.session_state.ke_ai_query = entity_context
                st.session_state.ke_ai_show_result = True
                st.rerun()

            # Display AI response if available
            if st.session_state.get("ke_ai_show_result") and st.session_state.get("ke_ai_query"):
                ai_query = st.session_state.ke_ai_query
                st.info(f"**Querying:** {ai_query}")
                with st.spinner("AI is analyzing this entity..."):
                    try:
                        resp = requests.post(
                            f"{API_URL}/query",
                            json={"question": ai_query, "top_k": 5},
                            timeout=15,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            answer = data.get("answer", "No answer found.")
                            sources = data.get("sources", [])
                            confidence = data.get("confidence", "Unknown")
                            entities_used = data.get("entities_used", [])

                            st.markdown(f"**Confidence:** `{confidence}`")
                            if entities_used:
                                st.markdown(f"**Entities referenced:** {', '.join(entities_used[:5])}")
                            st.markdown(answer)

                            if sources:
                                with st.expander("📚 View Sources"):
                                    for idx, src in enumerate(sources):
                                        st.markdown(f"**[{idx+1}] {src['citation']}** (Distance: `{src['distance']:.4f}`)")
                                        st.caption(f'Excerpt: *"{src["excerpt"][:200]}..."*')
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
        st.markdown(
            """
**How to use Knowledge Explorer:**

1. 🔍 **Search** for an entity by name in the sidebar
2. ☑️ **Filter** by node type using checkboxes
3. 🖱️ **Click** a node to expand its neighbors and see details
4. 📋 **View** connected entities in the detail panel on the right
5. 🔄 **Reset** to start fresh with top-connected nodes
"""
        )
