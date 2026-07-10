"""Streamlit UI for Industrial Knowledge Intelligence.

Includes chat, document library, knowledge graph visualization, entity explorer, and control panel.
"""

import streamlit as st
import requests
import os
from datetime import datetime
try:
    from streamlit_agraph import agraph, Node, Edge, Config
    AGRAPH_AVAILABLE = True
except ImportError:
    AGRAPH_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Industrial Knowledge Intelligence",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Endpoint Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Custom CSS for Premium Design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global Typography Override */
    html, body, [class*="css"], .stApp {
        font-family: 'Outfit', 'Inter', sans-serif !important;
    }

    /* Main Layout */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    
    /* Sleek Application Title Banner */
    .title-container {
        background: linear-gradient(135deg, #090d16 0%, #1e1b4b 50%, #120636 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        border: 1px solid rgba(99, 102, 241, 0.35);
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
    }
    .title-container h1 {
        margin: 0;
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 800;
        font-size: 2.3rem;
        letter-spacing: -0.02em;
        background: linear-gradient(90deg, #ffffff 0%, #c7d2fe 50%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .title-container p {
        margin: 0.5rem 0 0 0;
        font-size: 1.05rem;
        color: #cbd5e1;
        opacity: 0.9;
    }

    /* Glassmorphic Document Cards */
    .doc-card {
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        color: #f8fafc;
    }
    .doc-card:hover {
        transform: translateY(-3px);
        border-color: rgba(99, 102, 241, 0.5);
        box-shadow: 0 12px 28px rgba(99, 102, 241, 0.25);
    }
    
    /* Premium Badges */
    .badge {
        display: inline-block;
        padding: 0.3rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.05);
    }
    .badge-blue { background-color: rgba(59, 130, 246, 0.2) !important; color: #93c5fd !important; border-color: rgba(59, 130, 246, 0.3) !important; }
    .badge-green { background-color: rgba(16, 185, 129, 0.2) !important; color: #6ee7b7 !important; border-color: rgba(16, 185, 129, 0.3) !important; }
    .badge-purple { background-color: rgba(139, 92, 246, 0.2) !important; color: #c4b5fd !important; border-color: rgba(139, 92, 246, 0.3) !important; }
    .badge-yellow { background-color: rgba(245, 158, 11, 0.2) !important; color: #fde047 !important; border-color: rgba(245, 158, 11, 0.3) !important; }
    .badge-gray { background-color: rgba(107, 114, 128, 0.2) !important; color: #d1d5db !important; border-color: rgba(107, 114, 128, 0.3) !important; }
    
    /* Immersive Chat Bubbles */
    .chat-bubble {
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.25rem;
        font-size: 0.98rem;
        line-height: 1.6;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border: 1px solid transparent;
        transition: all 0.2s ease;
    }
    .chat-user {
        background-color: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 5px solid #94a3b8;
        color: #f1f5f9;
    }
    .chat-assistant {
        background-color: rgba(79, 70, 229, 0.08);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-left: 5px solid #6366f1;
        color: #f8fafc;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.08);
    }

    /* Scrollbars */
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
""", unsafe_allow_html=True)

# Helper function to format timestamp
def format_time(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%b %d, %Y %I:%M %p")
    except Exception:
        return iso_str

# Application Header
st.markdown("""
<div class="title-container">
    <h1>AI for Industrial Knowledge Intelligence</h1>
    <p>RAG-Powered Industrial Document Analysis (Vector Store + Knowledge Graph)</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/isometric-line/100/factory.png", width=60)
    st.markdown("### **System Status**")
    
    # Check health
    try:
        health_resp = requests.get(f"{API_URL}/health", timeout=3)
        if health_resp.status_code == 200:
            st.success("FastAPI Service: Connected")
        else:
            st.warning("FastAPI Service: Unhealthy")
    except requests.exceptions.ConnectionError:
        st.error("FastAPI Service: Offline")
    
    # Graph stats in sidebar
    try:
        graph_resp = requests.get(f"{API_URL}/entities", timeout=5)
        if graph_resp.status_code == 200:
            gdata = graph_resp.json()
            stats = gdata.get("stats", {})
            st.markdown("### **Knowledge Graph**")
            st.metric("Nodes", stats.get("total_nodes", 0))
            st.metric("Edges", stats.get("total_edges", 0))
            # Entity type breakdown
            node_types = stats.get("node_types", {})
            if node_types:
                with st.expander("Entity Breakdown"):
                    for etype, count in sorted(node_types.items(), key=lambda x: -x[1]):
                        st.write(f"**{etype.replace('_', ' ').title()}:** {count}")
    except Exception:
        pass
        
    st.markdown("---")
    st.markdown("### **Hackathon Phase**")
    st.info("**Day 3**: Entities & Knowledge Graph")
    st.markdown("---")
    st.caption("Developed for ET AI Hackathon 2026")

# Tabs
tab_chat, tab_docs, tab_graph, tab_entities, tab_setup = st.tabs([
    "💬 Chat Q&A", 
    "📁 Document Library", 
    "🕸️ Knowledge Graph",
    "🏷️ Entity Explorer",
    "⚙️ Control & Setup Panel"
])

# ==========================================
# 1. TAB: CHAT Q&A
# ==========================================
with tab_chat:
    st.subheader("Query System")
    st.write("Ask natural language questions about regulatory guidelines, safety manuals, work orders, or incidents.")
    st.caption("Powered by Vector Search + Knowledge Graph traversal")
    
    # Session state for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # User Input
    user_query = st.chat_input("Enter your safety or regulatory question (e.g. Which equipment requires quarterly inspection?)...")
    
    # Display Chat History
    for msg in st.session_state.messages:
        role_class = "chat-user" if msg["role"] == "user" else "chat-assistant"
        st.markdown(f'<div class="chat-bubble {role_class}"><b>{"You" if msg["role"] == "user" else "System"}:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
        
        # Display Citations if assistant message has them
        if msg["role"] == "assistant" and "sources" in msg and msg["sources"]:
            with st.expander("🔍 View Sources & Citations", expanded=False):
                for idx, src in enumerate(msg["sources"]):
                    st.markdown(f"**[{idx+1}] {src['citation']}** (Distance: `{src['distance']:.4f}`)")
                    st.caption(f"Excerpt: *\"{src['excerpt']}\"*")
                    st.markdown("---")

    # Handle Input Submission
    if user_query:
        # Display user bubble immediately
        st.markdown(f'<div class="chat-bubble chat-user"><b>You:</b><br>{user_query}</div>', unsafe_allow_html=True)
        st.session_state.messages.append({"role": "user", "content": user_query})
        
        # Query API
        with st.spinner("Analyzing document corpus and vector store..."):
            try:
                response = requests.post(
                    f"{API_URL}/query",
                    json={"question": user_query, "top_k": 5},
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    answer = data["answer"]
                    sources = data.get("sources", [])
                    confidence = data.get("confidence", "Unknown")
                    
                    # Add confidence badge to the answer
                    confidence_color = "green" if confidence == "High" else "blue" if confidence == "Medium" else "yellow"
                    entities_used = data.get("entities_used", [])
                    entities_html = ""
                    if entities_used:
                        entities_html = "<br><span class='badge badge-purple'>Graph: " + ", ".join(entities_used[:5]) + "</span>"
                    answer_html = f"{answer}<br><br><span class='badge badge-{confidence_color}'>Confidence: {confidence}</span>{entities_html}"
                    
                    # Display assistant bubble
                    st.markdown(f'<div class="chat-bubble chat-assistant"><b>System:</b><br>{answer_html}</div>', unsafe_allow_html=True)
                    
                    # Display citations
                    if sources:
                        with st.expander("🔍 View Sources & Citations", expanded=True):
                            for idx, src in enumerate(sources):
                                st.markdown(f"**[{idx+1}] {src['citation']}** (Distance: `{src['distance']:.4f}`)")
                                st.caption(f"Excerpt: *\"{src['excerpt']}\"*")
                                st.markdown("---")
                                
                    # Store in session state
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer_html,
                        "sources": sources
                    })
                else:
                    st.error(f"Error calling query API (Status {response.status_code}): {response.text}")
            except Exception as e:
                st.error(f"Failed to connect to API server: {e}")

# ==========================================
# 2. TAB: DOCUMENT LIBRARY
# ==========================================
with tab_docs:
    st.subheader("Ingested Documents")
    st.write("Browse regulatory templates and structured plant logs currently indexed in the RAG search index.")
    
    # Fetch documents
    try:
        docs_resp = requests.get(f"{API_URL}/documents", timeout=5)
        if docs_resp.status_code == 200:
            docs = docs_resp.json()
            
            if not docs:
                st.info("No documents have been indexed yet. Head to the **Control & Setup Panel** to initialize the database.")
            else:
                # Group by document type
                file_types = sorted(list(set(d["type"] for d in docs)))
                selected_type = st.multiselect("Filter by File Type", file_types, default=file_types)
                
                filtered_docs = [d for d in docs if d["type"] in selected_type]
                
                # Search Bar
                search_query = st.text_input("Search Document Names", "")
                if search_query:
                    filtered_docs = [d for d in filtered_docs if search_query.lower() in d["filename"].lower()]
                
                st.write(f"Showing {len(filtered_docs)} of {len(docs)} documents")
                st.markdown("---")
                
                # Show Documents Grid
                for doc in filtered_docs:
                    # Construct a card
                    with st.container():
                        st.markdown(f"""
                        <div class="doc-card">
                            <h4 style="margin: 0; color: #1e3a8a;">📄 {doc['filename']}</h4>
                            <div style="margin-top: 0.5rem;">
                                <span class="badge badge-purple">{doc['type'].upper()} File</span>
                                <span class="badge badge-blue">{doc['chunk_count']} Chunks</span>
                                <span class="badge badge-gray">Indexed: {format_time(doc['upload_date'])}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Add expanding chunk inspector
                        with st.expander(f"Inspect Parsed Chunks for {doc['filename']}"):
                            if st.button(f"Load Chunks", key=f"btn_{doc['doc_id']}"):
                                try:
                                    chunks_resp = requests.get(f"{API_URL}/documents/{doc['doc_id']}", timeout=5)
                                    if chunks_resp.status_code == 200:
                                        chunk_data = chunks_resp.json()
                                        st.write(f"Total chunks retrieved: {len(chunk_data['chunks'])}")
                                        for c in chunk_data["chunks"]:
                                            st.info(f"**Chunk {c['metadata'].get('chunk_index', 0)}** (ID: `{c['chunk_id']}`)")
                                            st.markdown(f"```\n{c['text']}\n```")
                                    else:
                                        st.error(f"Error fetching chunks: {chunks_resp.text}")
                                except Exception as err:
                                    st.error(f"Failed to fetch chunks: {err}")
                        st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.error(f"Failed to fetch documents (Status {docs_resp.status_code})")
    except Exception as e:
        st.error(f"Could not connect to API server: {e}")

# ==========================================
# 3. TAB: KNOWLEDGE GRAPH
# ==========================================
with tab_graph:
    st.subheader("Knowledge Graph Visualization")
    st.write("Interactive visualization of entity relationships extracted from the document corpus.")
    
    try:
        graph_resp = requests.get(f"{API_URL}/graph?max_nodes=200", timeout=10)
        if graph_resp.status_code == 200:
            graph_data = graph_resp.json()
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])
            
            if not nodes:
                st.info("Knowledge graph is empty. Initialize the corpus from the Control Panel to build the graph.")
            else:
                st.write(f"**{len(nodes)} nodes** · **{len(edges)} edges**")
                
                if AGRAPH_AVAILABLE:
                    agraph_nodes = []
                    for n in nodes:
                        agraph_nodes.append(Node(
                            id=n["id"],
                            label=n["id"] if len(n["id"]) < 20 else n["id"][:18] + "..",
                            color=n.get("color", "#6b7280"),
                            size=max(n.get("size", 5) * 2, 10),
                            title=f"{n['id']} ({n['type']})",
                        ))
                    
                    agraph_edges = []
                    for e in edges:
                        agraph_edges.append(Edge(
                            source=e["from"],
                            target=e["to"],
                            label=e.get("relation", "")[:15],
                            title=e.get("relation", ""),
                        ))
                    
                    physics_config = {
                        "enabled": True,
                        "solver": "barnesHut",
                        "barnesHut": {
                            "gravitationalConstant": -3000,
                            "centralGravity": 0.15,
                            "springLength": 100,
                            "springConstant": 0.05,
                            "damping": 0.09,
                            "avoidOverlap": 0.5
                        },
                        "stabilization": {
                            "enabled": True,
                            "iterations": 200,
                            "fit": True
                        },
                        "minVelocity": 0.75
                    }
                    
                    config = Config(
                        width="100%",
                        height=600,
                        directed=False,
                        hierarchical=False,
                        node={"font": {"size": 12}},
                        physics=physics_config
                    )
                    
                    returned_value = agraph(nodes=agraph_nodes, edges=agraph_edges, config=config)
                else:
                    st.warning("streamlit-agraph not installed. Showing graph data as tables.")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown("**Nodes**")
                        st.dataframe(
                            [{"id": n["id"], "type": n["type"], "connections": n.get("size", 5) - 5} for n in nodes[:100]],
                            use_container_width=True,
                            height=400,
                        )
                    with col_b:
                        st.markdown("**Edges**")
                        st.dataframe(
                            [{"from": e["from"], "relation": e["relation"], "to": e["to"]} for e in edges[:100]],
                            use_container_width=True,
                            height=400,
                        )
        else:
            st.error(f"Failed to fetch graph: {graph_resp.status_code}")
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to API server. Start the FastAPI server first.")
    except Exception as e:
        st.error(f"Error loading knowledge graph: {e}")

# ==========================================
# 4. TAB: ENTITY EXPLORER
# ==========================================
with tab_entities:
    st.subheader("Entity Explorer")
    st.write("Browse and search all entities extracted from the document corpus.")
    
    try:
        entities_resp = requests.get(f"{API_URL}/entities", timeout=10)
        if entities_resp.status_code == 200:
            edata = entities_resp.json()
            entities_by_type = edata.get("entities", {})
            stats = edata.get("stats", {})
            
            if not entities_by_type:
                st.info("No entities found. Initialize the corpus to extract entities.")
            else:
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Nodes", stats.get("total_nodes", 0))
                col2.metric("Total Edges", stats.get("total_edges", 0))
                col3.metric("Graph Density", f"{stats.get('density', 0):.4f}")
                
                st.markdown("---")
                
                type_options = sorted(entities_by_type.keys())
                selected_type = st.selectbox(
                    "Filter by Entity Type",
                    type_options,
                    format_func=lambda x: x.replace("_", " ").title(),
                )
                
                if selected_type:
                    entity_list = entities_by_type[selected_type]
                    st.write(f"**{len(entity_list)}** {selected_type.replace('_', ' ').title()} entities found")
                    
                    search = st.text_input("Search entities", "", key="entity_search")
                    if search:
                        entity_list = [e for e in entity_list if search.lower() in e.lower()]
                        st.write(f"Showing {len(entity_list)} matching results")
                    
                    for entity_id in entity_list[:50]:
                        with st.container():
                            st.markdown(f"**{entity_id}**")
                            if st.button(f"View relationships", key=f"sub_{entity_id}"):
                                try:
                                    sub_resp = requests.get(
                                        f"{API_URL}/graph/entity/{entity_id}?depth=1",
                                        timeout=5,
                                    )
                                    if sub_resp.status_code == 200:
                                        sub_data = sub_resp.json()
                                        neighbors = sub_data.get("neighbors", [])
                                        if neighbors:
                                            st.write(f"**{len(neighbors)} connections:**")
                                            for n in neighbors:
                                                st.markdown(
                                                    f"• {n['relation']} → **{n['id']}** ({n['type']})"
                                                )
                                        else:
                                            st.info("No direct connections found.")
                                except Exception as e:
                                    st.error(f"Error: {e}")
                            st.markdown("---")
                    
                    if len(entity_list) > 50:
                        st.info(f"Showing first 50 of {len(entity_list)} entities.")
        else:
            st.error(f"Failed to fetch entities: {entities_resp.status_code}")
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to API server. Start the FastAPI server first.")
    except Exception as e:
        st.error(f"Error loading entities: {e}")

# ==========================================
# 5. TAB: CONTROL & SETUP PANEL
# ==========================================
with tab_setup:
    st.subheader("Vector Database Ingestion Control")
    st.write("Manage document index initialization and upload new safety/regulatory guidelines.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### **1. Core Corpus Initialization**")
        st.write("Initialize the system by indexing all pre-bundled industrial files. This includes regulatory OISD guides, Factory Acts, and synthetic work orders/incidents.")
        
        if st.button("🚀 Scan & Index Default Corpus", use_container_width=True):
            with st.spinner("Parsing and embedding default corpus (this may take up to a minute)..."):
                try:
                    resp = requests.post(f"{API_URL}/ingest/initialize", timeout=120)
                    if resp.status_code == 200:
                        data = resp.json()
                        stats = data["stats"]
                        st.success(f"Success! Indexed {stats['files_ingested']} documents with a total of {stats['total_chunks']} text chunks.")
                        # Rerun to update library
                        st.rerun()
                    else:
                        st.error(f"Error initializing corpus: {resp.text}")
                except Exception as e:
                    st.error(f"Failed to trigger initialization: {e}")
                    
    with col2:
        st.markdown("### **2. Upload New Documents**")
        st.write("Upload custom text files, PDF manuals, Word documents, or CSV sheets to parse and add them to the active search index.")
        
        uploaded_files = st.file_uploader(
            "Select Files", 
            type=["txt", "pdf", "docx", "csv"], 
            accept_multiple_files=True
        )
        
        if uploaded_files:
            if st.button("📤 Ingest Selected Files", use_container_width=True):
                files_payload = []
                # Keep file pointer at beginning
                for uf in uploaded_files:
                    files_payload.append(
                        ("files", (uf.name, uf.getvalue(), uf.type))
                    )
                
                with st.spinner(f"Ingesting {len(uploaded_files)} files..."):
                    try:
                        resp = requests.post(
                            f"{API_URL}/ingest/upload",
                            files=files_payload,
                            timeout=60
                        )
                        if resp.status_code == 200:
                            results = resp.json()["results"]
                            success_count = sum(1 for r in results if r.get("status") == "success")
                            st.success(f"Successfully uploaded and ingested {success_count} files!")
                            for r in results:
                                if r.get("status") == "success":
                                    st.write(f"✓ **{r['doc_id']}** ({r['chunk_count']} chunks indexed)")
                                else:
                                    st.error(f"✗ **{r['doc_id']}** failed: {r.get('error')}")
                            # Rerun to update library
                            st.rerun()
                        else:
                            st.error(f"Upload failed: {resp.text}")
                    except Exception as e:
                        st.error(f"Failed to upload files: {e}")
