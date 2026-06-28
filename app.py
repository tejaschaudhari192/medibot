import streamlit as st
from langgraph.graph import StateGraph, END
from state import HealthBotState
from nodes import search_medical_info, generate_summary, create_quiz, grade_quiz

def search_and_summarize(state: HealthBotState) -> dict:
    search_res = search_medical_info(state)
    temp_state = {**state, **search_res}
    summary_res = generate_summary(temp_state)
    return {**search_res, **summary_res}


# Build a linear, robust graph
workflow = StateGraph(HealthBotState)
workflow.add_node("search_and_summarize", search_and_summarize)
workflow.add_node("generate_quiz", create_quiz)
workflow.add_node("grade_quiz_response", grade_quiz)

workflow.set_entry_point("search_and_summarize")
workflow.add_edge("search_and_summarize", "generate_quiz")
workflow.add_edge("generate_quiz", "grade_quiz_response")
workflow.add_edge("grade_quiz_response", END)

healthbot_app = workflow.compile()

# Streamlit UI Setup
st.set_page_config(page_title="MediTech HealthBot", page_icon="🩺", layout="centered")
st.title("🩺 MediTech HealthBot")
st.caption("AI-Powered Patient Education System")

# Initialize Session State
if "graph_state" not in st.session_state:
    st.session_state.graph_state = {
        "topic": "", "user_answer": "", "search_results": "",
        "summary": "", "quiz_question": "", "grade_feedback": ""
    }
if "ui_step" not in st.session_state:
    st.session_state.ui_step = "TOPIC_INPUT"

def reset_session():
    st.session_state.graph_state = {
        "topic": "", "user_answer": "", "search_results": "",
        "summary": "", "quiz_question": "", "grade_feedback": ""
    }
    st.session_state.ui_step = "TOPIC_INPUT"
    st.rerun()

# Topic Input Step
if st.session_state.ui_step == "TOPIC_INPUT":
    st.subheader("What would you like to learn about today?")
    topic_input = st.text_input("Enter a health topic or medical condition:")
    
    if st.button("Search & Learn", type="primary"):
        if not topic_input.strip():
            st.warning("Please enter a valid topic.")
        else:
            with st.spinner("Searching reputable medical databases..."):
                initial_input = {"topic": topic_input, "user_answer": "", "search_results": "", "summary": "", "quiz_question": "", "grade_feedback": ""}
                summary_state = search_and_summarize(initial_input)
                st.session_state.graph_state.update(initial_input)
                st.session_state.graph_state.update(summary_state)
                st.session_state.ui_step = "SHOW_SUMMARY"
                st.rerun()

# Show Summary Step
elif st.session_state.ui_step == "SHOW_SUMMARY":
    st.header(f"Learning Topic: {st.session_state.graph_state['topic'].title()}")
    summary_text = st.session_state.graph_state["summary"]
    
    if "I'm sorry, but I couldn't find reputable medical information" in summary_text:
        st.error(summary_text)
        if st.button("🔄 Try a Different Topic", type="primary"):
            reset_session()
    else:
        st.markdown("### 📖 Medical Summary")
        st.info(summary_text)
        st.write("---")
        if st.button("I'm Ready for a Quiz! 🚀", type="primary"):
            with st.spinner("Generating comprehension quiz question..."):
                quiz_state = create_quiz(st.session_state.graph_state)
                st.session_state.graph_state.update(quiz_state)
                st.session_state.ui_step = "TAKE_QUIZ"
                st.rerun()

# Take Quiz Step
elif st.session_state.ui_step == "TAKE_QUIZ":
    st.header("🧠 Comprehension Check")
    st.markdown("### ❓ Question:")
    st.warning(st.session_state.graph_state.get("quiz_question", "Loading question error..."))
    
    user_ans = st.text_area("Type your answer here:", key="patient_quiz_box")
    
    if st.button("Submit Answer", type="primary"):
        if not user_ans.strip():
            st.warning("Please input an answer before submitting.")
        else:
            with st.spinner("Evaluating response with source materials..."):
                st.session_state.graph_state["user_answer"] = user_ans
                grade_state = grade_quiz(st.session_state.graph_state)
                st.session_state.graph_state.update(grade_state)
                st.session_state.ui_step = "SHOW_RESULTS"
                st.rerun()

# Show Results Step
elif st.session_state.ui_step == "SHOW_RESULTS":
    st.header("📋 Evaluation Feedback")
    st.markdown(st.session_state.graph_state["grade_feedback"])
    st.write("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Learn Another Topic", use_container_width=True):
            reset_session()
    with col2:
        if st.button("❌ Exit Session", use_container_width=True):
            st.session_state.ui_step = "EXITED"
            st.rerun()

# Exited Step
elif st.session_state.ui_step == "EXITED":
    st.success("Thank you for using MediTech HealthBot. Your session has safely closed.")
    st.info("Refresh the webpage to open a brand new session.")