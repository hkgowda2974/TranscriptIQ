import os
import sys
from pathlib import Path
import streamlit as st

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.config import DATA_DIR
from backend.app.schemas import (
    CustomQARequest,
    InterviewQuestion,
    ExpertMetadata,
    QuestionAnswerResult,
    SynthesisResult,
    RAGAnswerResponse
)
from backend.app.services.parser import parse_interview_guide, parse_transcript
from backend.app.services.chunker import create_turn_chunks
from backend.app.services.vector_store import vector_store
from backend.app.services.rag_engine import rag_engine

# Page Configuration
st.set_page_config(
    page_title="Dovetail Intelligence | Hasamex Expert Transcript Analyzer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dovetail Platform Design System CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #0F172A;
    }

    /* Top Navigation / Brand Banner */
    .dovetail-banner {
        background: linear-gradient(135deg, #4F46E5 0%, #3730A3 100%);
        color: #FFFFFF;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);
    }
    .dovetail-banner h1 {
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .dovetail-banner p {
        font-size: 1rem;
        color: #E0E7FF;
        margin-top: 0.4rem;
        margin-bottom: 0;
    }

    /* Dovetail Cards */
    .dt-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: all 0.2s ease-in-out;
    }
    .dt-card:hover {
        border-color: #6366F1;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.08);
    }

    /* Highlight Quote Blocks - Dovetail Style */
    .dt-highlight {
        background-color: #FEF9C3;
        border-left: 4px solid #CA8A04;
        border-radius: 4px;
        padding: 0.8rem 1rem;
        margin: 0.6rem 0;
        font-size: 0.95rem;
        color: #1E293B;
        font-style: italic;
    }

    /* Badges & Tags */
    .dt-badge {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 9999px;
        margin-right: 6px;
        margin-bottom: 4px;
    }
    .dt-badge-uk { background-color: #E0F2FE; color: #0369A1; }
    .dt-badge-de { background-color: #FEF3C7; color: #92400E; }
    .dt-badge-fr { background-color: #FCE7F3; color: #9D174D; }
    .dt-badge-time { background-color: #EEF2FF; color: #4338CA; border: 1px solid #C7D2FE; }
    .dt-badge-verified { background-color: #DCFCE7; color: #15803D; border: 1px solid #BBF7D0; }
    .dt-badge-conflict { background-color: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }

    /* Custom Input styling */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #CBD5E1;
        padding: 0.6rem 1rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_dovetail_data():
    """Initializes and indexes transcript files into vector store."""
    guide_path = DATA_DIR / "interview_guide.txt"
    objective = ""
    questions = []
    if guide_path.exists():
        objective, questions = parse_interview_guide(guide_path.read_text(encoding="utf-8"))

    experts = []
    all_chunks = []
    raw_transcripts = {}

    vector_store.clear()
    transcript_files = list(DATA_DIR.glob("expert_*.txt"))

    for tf in sorted(transcript_files):
        content = tf.read_text(encoding="utf-8")
        raw_transcripts[tf.name] = content
        parsed = parse_transcript(content, tf.name)
        metadata = parsed["metadata"]
        experts.append(metadata)
        chunks = create_turn_chunks(parsed)
        all_chunks.extend(chunks)
        vector_store.add_chunks(chunks)

    return {
        "objective": objective,
        "questions": questions,
        "experts": experts,
        "all_chunks": all_chunks,
        "raw_transcripts": raw_transcripts
    }


state = load_dovetail_data()

# Session State Initializations
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "selected_explorer_doc" not in st.session_state:
    st.session_state["selected_explorer_doc"] = "expert_1.txt"
if "matrix_results" not in st.session_state:
    st.session_state["matrix_results"] = None
if "synthesis_results" not in st.session_state:
    st.session_state["synthesis_results"] = rag_engine.synthesize_themes_and_disagreements(state["all_chunks"])

# Sidebar - Dovetail Workspace Navigator
with st.sidebar:
    st.markdown("## ⚡ Dovetail AI")
    st.caption("Customer Intelligence & Transcript Platform")
    st.divider()

    st.markdown("### 📁 Project Workspace")
    st.markdown(f"**Project**: European Robotic Surgery Market")
    st.markdown(f"**Transcripts Ingested**: {len(state['experts'])}")
    st.markdown(f"**Guide Questions**: {len(state['questions'])}")
    st.markdown(f"**Highlight Chunks**: {len(state['all_chunks'])}")
    st.divider()

    st.markdown("### 🏷️ Participant Tags")
    for exp in state["experts"]:
        badge_class = "dt-badge-fr" if "france" in exp.market.lower() else ("dt-badge-de" if "germany" in exp.market.lower() else "dt-badge-uk")
        st.markdown(f'<span class="dt-badge {badge_class}">{exp.market}</span> <b>{exp.name}</b>', unsafe_allow_html=True)
        st.caption(exp.role)

# Dovetail Banner
st.markdown(f"""
<div class="dovetail-banner">
    <h1>Dovetail Customer Intelligence Hub</h1>
    <p>Project: European Robotic Surgery Adoption | Objective: {state['objective']}</p>
</div>
""", unsafe_allow_html=True)

# Dovetail Platform Navigation Tabs
tab_ask, tab_guide, tab_synthesis, tab_explorer = st.tabs([
    "💬 Ask Across Interviews (AI Canvas)",
    "📋 Interview Guide Matrix",
    "💡 Themes & Conflict Insights",
    "📄 Transcript & Highlight Explorer"
])

# TAB 1: ASK ACROSS INTERVIEWS (AI CANVAS)
with tab_ask:
    st.subheader("Interactive AI Insight Canvas")
    st.caption("Ask natural-language questions across all interview transcripts. Extracted highlights are verified against original source recordings.")

    col_q, col_btn = st.columns([4, 1])
    with col_q:
        user_query = st.text_input(
            "Search across interview calls...",
            placeholder="e.g. Compare purchasing timelines and approval barriers between Germany and UK"
        )
    with col_btn:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        search_clicked = st.button("Generate Insight", type="primary")

    if search_clicked and user_query:
        with st.spinner("Searching transcript vectors & verifying quote highlights..."):
            response: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query=user_query)

        st.session_state["chat_history"].append({
            "query": user_query,
            "response": response
        })

    # Render History as Dovetail Insight Cards
    if st.session_state["chat_history"]:
        st.divider()
        st.markdown("### Recent AI Insights & Highlight Cards")
        
        for item in reversed(st.session_state["chat_history"]):
            res: RAGAnswerResponse = item["response"]
            
            st.markdown(f"""
            <div class="dt-card">
                <h3>🔍 Question: <i>"{item['query']}"</i></h3>
                <p><b>AI Summary:</b> {res.answer}</p>
                <small>Confidence: <b>{res.confidence}</b> | Context Grounded: <b>{res.is_grounded}</b></small>
            </div>
            """, unsafe_allow_html=True)

            if res.evidence:
                st.markdown("**Verbatim Highlight Cards:**")
                cols = st.columns(len(res.evidence) if len(res.evidence) <= 3 else 3)
                for i, ev in enumerate(res.evidence):
                    with cols[i % 3]:
                        badge_class = "dt-badge-fr" if "france" in ev.expert.lower() else ("dt-badge-de" if "germany" in ev.expert.lower() else "dt-badge-uk")
                        st.markdown(f"""
                        <div class="dt-card">
                            <span class="dt-badge {badge_class}">{ev.expert}</span>
                            <span class="dt-badge dt-badge-time">⏱️ {ev.timestamp}</span>
                            <span class="dt-badge dt-badge-verified">✓ {ev.verification_status}</span>
                            <div class="dt-highlight">"{ev.quote}"</div>
                            <small>Source: <code>{ev.source}</code></small>
                        </div>
                        """, unsafe_allow_html=True)
            st.divider()

# TAB 2: INTERVIEW GUIDE MATRIX
with tab_guide:
    st.subheader("Interview-Guide Response Matrix")
    st.caption("Compare structured responses across participants for canonical research questions.")

    col_b, col_empty = st.columns([1, 2])
    with col_b:
        if st.button("⚡ Run Full Matrix Analysis", type="primary"):
            with st.spinner("Evaluating all questions across 3 expert transcripts..."):
                results = {}
                for q in state["questions"]:
                    q_res = []
                    for expert in state["experts"]:
                        ans = rag_engine.answer_guided_question(q, expert, state["all_chunks"])
                        q_res.append(ans)
                    results[q.question_id] = q_res
                st.session_state["matrix_results"] = results
                st.success("Matrix analysis generated successfully!")

    matrix_data = st.session_state.get("matrix_results", None)

    if matrix_data:
        selected_q_id = st.selectbox(
            "Select Question Matrix View:",
            options=[q.question_id for q in state["questions"]],
            format_func=lambda qid: next(f"Q{q.question_id}: {q.question_text}" for q in state["questions"] if q.question_id == qid)
        )

        q_obj = next(q for q in state["questions"] if q.question_id == selected_q_id)
        st.markdown(f"### Q{q_obj.question_id}: *{q_obj.question_text}*")

        cols = st.columns(len(state["experts"]))
        q_results = matrix_data[selected_q_id]

        for idx, expert_ans in enumerate(q_results):
            with cols[idx]:
                badge_class = "dt-badge-fr" if "france" in expert_ans.market.lower() else ("dt-badge-de" if "germany" in expert_ans.market.lower() else "dt-badge-uk")
                st.markdown(f"""
                <div class="dt-card">
                    <h3>{expert_ans.expert_name}</h3>
                    <span class="dt-badge {badge_class}">{expert_ans.market}</span>
                    <p><b>Summary:</b> {expert_ans.summary_answer}</p>
                </div>
                """, unsafe_allow_html=True)

                if expert_ans.evidence:
                    for ev in expert_ans.evidence:
                        st.markdown(f"""
                        <div class="dt-card">
                            <span class="dt-badge dt-badge-time">⏱️ {ev.timestamp}</span>
                            <span class="dt-badge dt-badge-verified">✓ {ev.verification_status}</span>
                            <div class="dt-highlight">"{ev.quote}"</div>
                            <small>Source File: <code>{ev.source}</code></small>
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.info("Click **[⚡ Run Full Matrix Analysis]** to populate the response grid across participants.")

# TAB 3: THEMES & CONFLICT INSIGHTS
with tab_synthesis:
    st.subheader("Synthesized Themes & Market Conflicts")
    st.caption("Cross-interview consensus clusters and divergent market realities.")

    synth_data: SynthesisResult = st.session_state["synthesis_results"]

    col_t, col_d = st.columns(2)

    with col_t:
        st.markdown("### 🤝 Common Consensus Themes")
        for theme in synth_data.common_themes:
            with st.expander(f"🔹 {theme.theme_title}", expanded=True):
                st.write(theme.description)
                st.markdown(f"**Supporting Participants:** {', '.join(theme.supporting_experts)}")
                
                for pe in theme.per_expert_evidence:
                    badge_class = "dt-badge-fr" if "france" in pe.market.lower() else ("dt-badge-de" if "germany" in pe.market.lower() else "dt-badge-uk")
                    st.markdown(f"""
                    <div class="dt-card">
                        <span class="dt-badge {badge_class}">{pe.expert_name} ({pe.market})</span>
                        <p><i>{pe.position_summary}</i></p>
                    </div>
                    """, unsafe_allow_html=True)
                    for ev in pe.evidence_quotes:
                        st.markdown(f"""
                        <div class="dt-highlight">"{ev.quote}" (⏱️ {ev.timestamp})</div>
                        """, unsafe_allow_html=True)

    with col_d:
        st.markdown("### ⚡ Disagreements & Divergent Stances")
        for dis in synth_data.disagreements:
            with st.expander(f"🔸 Topic: {dis.topic}", expanded=True):
                st.markdown(f'<span class="dt-badge dt-badge-conflict">Relationship: {dis.relationship_type}</span>', unsafe_allow_html=True)
                st.write(dis.description)

                for pos in dis.expert_positions:
                    badge_class = "dt-badge-fr" if "france" in pos.market.lower() else ("dt-badge-de" if "germany" in pos.market.lower() else "dt-badge-uk")
                    st.markdown(f"""
                    <div class="dt-card">
                        <span class="dt-badge {badge_class}">{pos.expert_name} ({pos.market})</span>
                        <p><b>Stance:</b> {pos.position_summary}</p>
                        <div class="dt-highlight">"{pos.verbatim_quote}"</div>
                        <span class="dt-badge dt-badge-time">⏱️ {pos.timestamp}</span>
                    </div>
                    """, unsafe_allow_html=True)

# TAB 4: TRANSCRIPT & HIGHLIGHT EXPLORER
with tab_explorer:
    st.subheader("Raw Transcript & Highlight Viewer")
    st.caption("Inspect raw interview recordings, timestamps, and full dialogue context.")

    doc_options = ["interview_guide.txt"] + list(state["raw_transcripts"].keys())
    selected_doc = st.selectbox(
        "Select Participant Transcript:",
        options=doc_options,
        index=doc_options.index(st.session_state["selected_explorer_doc"]) if st.session_state["selected_explorer_doc"] in doc_options else 0
    )

    if selected_doc == "interview_guide.txt":
        guide_text = (DATA_DIR / "interview_guide.txt").read_text(encoding="utf-8")
        st.text_area("Interview Guide Content", guide_text, height=450)
    else:
        raw_text = state["raw_transcripts"].get(selected_doc, "")
        parsed_doc = parse_transcript(raw_text, selected_doc)
        meta = parsed_doc["metadata"]

        badge_class = "dt-badge-fr" if "france" in meta.market.lower() else ("dt-badge-de" if "germany" in meta.market.lower() else "dt-badge-uk")
        st.markdown(f"""
        <div class="dt-card">
            <h2>{meta.name}</h2>
            <span class="dt-badge {badge_class}">Market: {meta.market}</span>
            <span class="dt-badge dt-badge-time">Role: {meta.role}</span>
        </div>
        """, unsafe_allow_html=True)

        st.text_area("Raw Transcript Content", raw_text, height=500)
