import streamlit as st
from langgraph.types import Command
from graph import app # We import your compiled state machine

# 1. Page Configuration & Custom CSS Styling
st.set_page_config(page_title="Deep Research Meta-Agent", layout="wide", page_icon="🕵️")

st.markdown("""
<style>
    /* Modern Slate Dark Theme Overrides */
    .stApp { background-color: #0E1117; }
    .hitl-card { background-color: #2D2305; padding: 25px; border-radius: 12px; border-left: 5px solid #FFC107; margin-bottom: 25px; }
    .report-card { background-color: #161A22; padding: 35px; border-radius: 12px; border-left: 5px solid #00F0FF; margin-top: 30px; box-shadow: 0px 4px 15px rgba(0,0,0,0.2); }
    h1, h2, h3 { font-family: 'Inter', sans-serif; }
</style>
""", unsafe_allow_html=True)

st.title("🧠 Deep Research Meta-Agent")
st.markdown("Enterprise-grade multi-agent architecture with Map-Reduce parallelism and HITL safety gates.")

# 2. Sidebar Configuration (Managing the Database Thread)
with st.sidebar:
    st.header("⚙️ System Config")
    thread_id = st.text_input("Session Thread ID", value="portfolio_run_1")
    st.markdown("*Changing the Thread ID creates a new isolated database memory state.*")
    if st.button("Reset Current Memory", type="secondary"):
        st.session_state.clear()
        st.rerun()

config = {"configurable": {"thread_id": thread_id}}

# 3. Read the Database: Is the graph currently paused?
graph_state = app.get_state(config)
is_paused = len(graph_state.next) > 0

# --- THE MAIN LOGIC ---

if not is_paused:
    # If the system is ready, show the input bar
    question = st.chat_input("Enter your complex research topic...")
    
    if question:
        initial_state = {
            "question": question, 
            "sub_topics": [], 
            "research_notes": [], 
            "final_report": "", 
            "is_complete": False,
            "iteration_count": 0,
            "critique": ""
        }
        
        # 4. Stream the execution live to the UI
        with st.status("🚀 Agents Dispatched...", expanded=True) as status:
            for event in app.stream(initial_state, config):
                for node, state_update in event.items():
                    if node == "supervisor":
                        st.write("👨‍💼 Supervisor drafted the execution plan.")
                    elif node == "__interrupt__":
                        st.write("⚠️ Safety Gate Triggered!")
                    elif node == "searcher":
                        st.write("⚡ Parallel Search Agents executing queries...")
                    elif node == "synthesizer":
                        st.write("📝 Synthesizer compiling draft report...")
                    elif node == "critic":
                        st.write(f"🧐 Critic Evaluation Complete.")
            
            # Check if the stream stopped because of our safety gate
            new_state = app.get_state(config)
            if len(new_state.next) > 0:
                status.update(label="Awaiting Human Authorization", state="error")
                st.rerun()
            else:
                status.update(label="Research Complete!", state="complete")

else:
    # 5. The Human-in-the-Loop UI
    pending_task = graph_state.tasks[0]
    interrupt_value = pending_task.interrupts[0].value
    planned_queries = interrupt_value.get("planned_queries", [])
    
    st.markdown('''
    <div class="hitl-card">
        <h3>⚠️ Human Authorization Required</h3>
        <p>The Supervisor agent wants to execute the following parallel search queries. Please review them before allowing the system to spend compute resources.</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Allow the user to edit the queries directly in the UI
    edited_queries = st.text_area("Edit the queries (comma separated) or approve as-is:", value=", ".join(planned_queries))
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Approve & Dispatch Agents", type="primary", use_container_width=True):
            with st.status("🚀 Resuming Graph Execution...", expanded=True) as status:
                # If the human changed the text, send the new text. Otherwise, send "approve".
                resume_cmd = "approve" if edited_queries == ", ".join(planned_queries) else edited_queries
                
                # Resume the graph using the Command object
                for event in app.stream(Command(resume=resume_cmd), config):
                    for node, state_update in event.items():
                        if node == "searcher":
                            st.write("⚡ Parallel Search Agents scraping the web...")
                        elif node == "synthesizer":
                            st.write("📝 Synthesizer compiling draft report...")
                        elif node == "critic":
                            st.write(f"🧐 Critic evaluating the draft...")
                status.update(label="Research Complete!", state="complete")
            st.rerun()

# 6. Render the Final Report
current_memory = app.get_state(config).values
if "final_report" in current_memory and current_memory["final_report"] != "":
    if not is_paused: 
        st.markdown("### 📄 Final Synthesized Report")
        st.markdown(f'<div class="report-card">{current_memory["final_report"]}</div>', unsafe_allow_html=True)