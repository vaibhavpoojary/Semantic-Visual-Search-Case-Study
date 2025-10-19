# """
# Production Streamlit UI for Visual Semantic Search.
# Connects to FastAPI backend for all operations.
# """

# import streamlit as st
# import requests
# import pandas as pd
# from typing import Dict, Any
# import os

# # =========================
# # CONFIGURATION
# # =========================

# API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
# APP_VERSION = "1.0.0"

# st.set_page_config(
#     page_title="Visual Semantic Search",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # =========================
# # API CLIENT FUNCTIONS
# # =========================

# @st.cache_data(ttl=60)
# def get_health_status() -> Dict[str, Any]:
#     """Fetch system health from API."""
#     try:
#         response = requests.get(f"{API_BASE}/health", timeout=5)
#         response.raise_for_status()
#         return response.json()
#     except Exception as e:
#         st.error(f"Failed to connect to API: {e}")
#         return {}


# def search_images(query: str, top_k: int, threshold: float, use_enhancement: bool) -> Dict[str, Any]:
#     """Call search API endpoint."""
#     try:
#         payload = {
#             "query": query,
#             "top_k": top_k,
#             "threshold": threshold,
#             "use_enhancement": use_enhancement
#         }
#         response = requests.post(f"{API_BASE}/search", json=payload, timeout=30)
#         response.raise_for_status()
#         return response.json()
#     except requests.exceptions.RequestException as e:
#         st.error(f"Search failed: {e}")
#         return {}


# def reload_index() -> Dict[str, Any]:
#     """Call admin reload endpoint."""
#     try:
#         response = requests.post(f"{API_BASE}/admin/reload", timeout=60)
#         response.raise_for_status()
#         return response.json()
#     except Exception as e:
#         st.error(f"Reload failed: {e}")
#         return {}


# # =========================
# # SESSION STATE
# # =========================

# if "search_results" not in st.session_state:
#     st.session_state.search_results = None

# # =========================
# # HEADER
# # =========================

# st.title("🖼️ Visual Semantic Search")

# # Get system status
# health = get_health_status()

# if health:
#     col1, col2 = st.columns([3, 1])
#     with col1:
#         st.markdown(f"**AI-Powered Image Retrieval** | Model: {health.get('model', 'N/A')} | Images: {health.get('total_images', 0):,}")
#     with col2:
#         device_color = "#2ecc71" if health.get('device') == 'cuda' else "#3498db"
#         st.markdown(
#             f"<div style='text-align:right'><span style='background:{device_color};color:white;padding:4px 10px;border-radius:12px;font-size:0.85em'>{health.get('device', 'N/A').upper()}</span></div>",
#             unsafe_allow_html=True
#         )

# st.markdown("---")

# # =========================
# # SIDEBAR
# # =========================

# with st.sidebar:
#     st.header("⚙️ Search Parameters")
    
#     query = st.text_input(
#         "Query",
#         placeholder="e.g., sunset over mountains",
#         help="Enter natural language description"
#     )
    
#     use_enhancement = st.toggle("Query Enhancement", value=True, help="Enable automatic query expansion")
    
#     top_k = st.slider("Top K Results", 1, 20, 5)
#     threshold = st.slider("Score Threshold", 0.0, 0.6, 0.2, 0.01)
    
#     st.markdown("---")
    
#     search_clicked = st.button("🔍 Search", type="primary", use_container_width=True)
    
#     st.markdown("---")
#     st.subheader("System")
    
#     if health:
#         st.caption(f"**Vectors:** {health.get('vectors_indexed', 0):,}")
#         st.caption(f"**Index:** {health.get('index_type', 'N/A')}")
    
#     if st.button("🔄 Reload Index", use_container_width=True):
#         with st.spinner("Reloading..."):
#             result = reload_index()
#             if result.get("status") == "success":
#                 st.success(f"Reloaded in {result.get('load_time_seconds', 0):.2f}s")
#                 st.cache_data.clear()

# # =========================
# # MAIN AREA
# # =========================

# tab1, tab2 = st.tabs(["🔎 Search", "📊 System Status"])

# # --- SEARCH TAB ---
# with tab1:
#     if search_clicked and query.strip():
#         with st.spinner(f"Searching for '{query}'..."):
#             response = search_images(query, top_k, threshold, use_enhancement)
        
#         if response:
#             st.session_state.search_results = response
#             st.toast(f"Search completed in {response.get('timing_ms', 0):.1f}ms", icon="⚡")
    
#     if st.session_state.search_results:
#         data = st.session_state.search_results
#         results = data.get("results", [])
        
#         # Metrics
#         st.subheader("Search Metrics")
#         m1, m2, m3, m4 = st.columns(4)
        
#         timing = data.get("timing_ms", 0)
#         top1_score = results[0]["similarity_score"] if results else 0
#         avg_score = sum(r["similarity_score"] for r in results) / len(results) if results else 0
        
#         m1.metric("Search Time (ms)", f"{timing:.1f}")
#         m2.metric("Top-1 Score", f"{top1_score:.3f}")
#         m3.metric("Avg Score", f"{avg_score:.3f}")
#         m4.metric("Results", len(results))
        
#         st.markdown("---")
        
#         # Enhanced queries
#         if use_enhancement and data.get("enhanced_queries"):
#             with st.expander("Enhanced Queries"):
#                 st.code(", ".join(data["enhanced_queries"]))
        
#         # Results grid
#         # Results grid
#         if results:
#             st.subheader(f"Top {len(results)} Results")
            
#             cols = st.columns(5)
#             for i, item in enumerate(results):
#                 with cols[i % 5]:
#                     # Image display (placeholder if image not accessible)
#                     try:
#                         st.image(item["image_path"], use_container_width=True)  # ✅ FIXED
#                     except:
#                         st.info(f"📷 {item['filename']}")
                    
#                     rank_color = "#e74c3c" if item['rank'] == 1 else "#3498db"
#                     st.markdown(
#                         f"<span style='background:{rank_color};color:white;padding:2px 8px;border-radius:4px;font-size:0.85em'>#{item['rank']}</span>",
#                         unsafe_allow_html=True
#                     )
#                     st.caption(f"**{item['filename']}**")
#                     st.caption(f"Score: `{item['similarity_score']:.3f}`")
#                     st.caption(f"Confidence: {item['confidence_percentage']}")

# # --- SYSTEM TAB ---
# with tab2:
#     st.subheader("System Status")
    
#     if health:
#         col1, col2 = st.columns(2)
        
#         col1.markdown("**Model:**")
#         col2.markdown(f"`{health.get('model', 'N/A')}`")
        
#         col1.markdown("**Embedding Dim:**")
#         col2.markdown(f"`{health.get('embedding_dim', 0)}`")
        
#         col1.markdown("**Vectors Indexed:**")
#         col2.markdown(f"`{health.get('vectors_indexed', 0):,}`")
        
#         col1.markdown("**Total Images:**")
#         col2.markdown(f"`{health.get('total_images', 0):,}`")
        
#         col1.markdown("**Index Type:**")
#         col2.markdown(f"`{health.get('index_type', 'N/A')}`")
        
#         col1.markdown("**Device:**")
#         col2.markdown(f"`{health.get('device', 'N/A')}`")
        
#         st.markdown("---")
#         st.success("✅ System operational")
#     else:
#         st.error("❌ Cannot connect to API")

# st.markdown("---")
# st.markdown(
#     f"<div style='text-align:center;color:gray;font-size:0.8em'>Visual Semantic Search v{APP_VERSION} | API: {API_BASE}</div>",
#     unsafe_allow_html=True
# )


"""
Production Streamlit UI for Visual Semantic Search.
Clean, professional design with prominent image display.
"""

import streamlit as st
import requests
import pandas as pd
from typing import Dict, Any
import os

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
APP_VERSION = "1.0.0"

st.set_page_config(
    page_title="Visual Semantic Search",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data(ttl=60)
def get_health_status() -> Dict[str, Any]:
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Failed to connect to API: {e}")
        return {}

def search_images(query: str, top_k: int, threshold: float, use_enhancement: bool) -> Dict[str, Any]:
    try:
        payload = dict(query=query, top_k=top_k, threshold=threshold, use_enhancement=use_enhancement)
        r = requests.post(f"{API_BASE}/search", json=payload, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Search failed: {e}")
        return {}

def reload_index() -> Dict[str, Any]:
    try:
        r = requests.post(f"{API_BASE}/admin/reload", timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Reload failed: {e}")
        return {}

if "search_results" not in st.session_state:
    st.session_state.search_results = None

st.title("Visual Semantic Search")
health = get_health_status()

if health:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            f"**AI-Powered Image Retrieval** | Model: {health.get('model', 'N/A')} | "
            f"Images: {health.get('total_images', 0):,}"
        )
    with col2:
        device_color = "#2ecc71" if health.get('device') == 'cuda' else "#3498db"
        st.markdown(
            f"<div style='text-align:right'><span style='background:{device_color};"
            f"color:white;padding:4px 10px;border-radius:12px;font-size:0.85em'>"
            f"{health.get('device', 'N/A').upper()}</span></div>",
            unsafe_allow_html=True
        )

st.markdown("---")

with st.sidebar:
    st.header("Search Parameters")
    query = st.text_input(
        "Query",
        placeholder="e.g., sunset over mountains",
        help="Enter natural language description"
    )
    use_enhancement = st.toggle(
        "Query Enhancement",
        value=True,
        help="Enable automatic query expansion"
    )
    top_k = st.slider("Top K Results", 1, 20, 5)
    threshold = st.slider("Score Threshold", 0.0, 0.6, 0.2, 0.01)
    st.markdown("---")
    search_clicked = st.button("Search", type="primary", use_container_width=True)
    st.markdown("---")
    st.subheader("System")
    if health:
        st.caption(f"**Vectors:** {health.get('vectors_indexed', 0):,}")
        st.caption(f"**Index:** {health.get('index_type', 'N/A')}")
    if st.button("Reload Index", use_container_width=True):
        with st.spinner("Reloading..."):
            result = reload_index()
            if result.get("status") == "success":
                st.success(f"Reloaded in {result.get('load_time_seconds', 0):.2f}s")
                st.cache_data.clear()

tab1, tab2 = st.tabs(["Search Results", "System Status"])

with tab1:
    if search_clicked and query.strip():
        with st.spinner(f"Searching for '{query}'..."):
            response = search_images(query, top_k, threshold, use_enhancement)
        if response:
            st.session_state.search_results = response

    if st.session_state.search_results:
        data = st.session_state.search_results
        results = data.get("results", [])
        
        if results:
            st.subheader(f"Top {len(results)} Results")
            
            # Image grid - NO border container for larger images
            cols = st.columns(5)
            for i, item in enumerate(results):
                with cols[i % 5]:
                    # Image takes full column width - no container constraint
                    try:
                        st.image(item["image_path"], use_container_width=True)
                    except Exception:
                        st.info(f"{item['filename']}")
                    
                    # Compact metric box below
                    rank_color = "#E74C3C" if item["rank"] == 1 else "#4577ED"
                    st.markdown(
                        f"""
                        <div style="
                            background: #f8f9fa;
                            border-radius: 8px;
                            padding: 8px;
                            margin-top: 6px;
                            text-align: center;
                            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                        ">
                            <span style="
                                background: {rank_color};
                                color: white;
                                padding: 3px 12px;
                                border-radius: 12px;
                                font-size: 0.9em;
                                font-weight: 600;
                            ">Rank #{item["rank"]}</span>
                            <div style="
                                font-weight: 600;
                                font-size: 0.95em;
                                color: #2c3e50;
                                margin: 6px 0 4px 0;
                                word-break: break-word;
                            ">{item["filename"]}</div>
                            <div style="color: #34495e; font-size: 0.88em; margin: 2px 0;">
                                <strong>Score:</strong> {item["similarity_score"]:.3f}
                            </div>
                            <div style="color: #7f8c8d; font-size: 0.82em; margin: 2px 0;">
                                Confidence: {item["confidence_percentage"]}
                            </div>
                            <div style="color: #95a5a6; font-size: 0.76em;">
                                Matches: {item["num_query_matches"]}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            
            # Metrics below images
            st.markdown("---")
            st.subheader("Search Metrics")
            m1, m2, m3, m4 = st.columns(4)
            timing = data.get("timing_ms", 0)
            top1_score = results[0]["similarity_score"] if results else 0
            avg_score = sum(r["similarity_score"] for r in results) / len(results) if results else 0
            m1.metric("Search Time (ms)", f"{timing:.1f}")
            m2.metric("Top-1 Score", f"{top1_score:.3f}")
            m3.metric("Avg Score", f"{avg_score:.3f}")
            m4.metric("Results Count", len(results))
            
            st.markdown("---")
            
            # Enhanced queries
            if use_enhancement and data.get("enhanced_queries"):
                with st.expander("Enhanced Queries"):
                    st.code(", ".join(data["enhanced_queries"]))
            
            # Detailed table
            with st.expander("Detailed Results Table"):
                df = pd.DataFrame(results)
                display_cols = ['rank', 'filename', 'similarity_score', 
                               'confidence_percentage', 'num_query_matches']
                st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Results (CSV)",
                    data=csv,
                    file_name=f"search_results_{query.replace(' ', '_')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.info("No results found. Try lowering the threshold or adjusting your query.")
    else:
        st.info("Enter a query and click Search to begin visual retrieval.")

with tab2:
    st.subheader("System Status")
    if health:
        col1, col2 = st.columns(2)
        col1.markdown("**Model:**")
        col2.markdown(f"`{health.get('model', 'N/A')}`")
        col1.markdown("**Embedding Dimension:**")
        col2.markdown(f"`{health.get('embedding_dim', 0)}`")
        col1.markdown("**Vectors Indexed:**")
        col2.markdown(f"`{health.get('vectors_indexed', 0):,}`")
        col1.markdown("**Total Images:**")
        col2.markdown(f"`{health.get('total_images', 0):,}`")
        col1.markdown("**Index Type:**")
        col2.markdown(f"`{health.get('index_type', 'N/A')}`")
        col1.markdown("**Device:**")
        col2.markdown(f"`{health.get('device', 'N/A')}`")
        st.markdown("---")
        st.success("System operational")
    else:
        st.error("Cannot connect to API")

st.markdown("---")
st.markdown(
    f"<div style='text-align:center;color:gray;font-size:0.8em'>"
    f"Visual Semantic Search v{APP_VERSION} | API: {API_BASE}"
    f"</div>",
    unsafe_allow_html=True
)
