import os
import streamlit as st
from typing import Dict, TypedDict
from dotenv import load_dotenv
from langchain_cohere import ChatCohere
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END

# --- 1. ENVIRONMENT & API SETUP ---
load_dotenv('config.env')
if not os.getenv('COHERE_API_KEY') or not os.getenv('TAVILY_API_KEY'):
    st.error("API Keys missing! Please check your config.env file.")
    st.stop()

# Initialize Models and Tools
llm = ChatCohere(model="command-r-plus-08-2024", temperature=0)
search_tool = TavilySearchResults(max_results=3)

# --- 2. LANGGRAPH STATE SCHEMA ---
class HealthBotState(TypedDict):
    topic: str
    user_answer: str
    search_results: str
    summary: str
    quiz_question: str
    grade_feedback: str

# --- 3. GRAPH NODES ---
def search_and_summarize(state: HealthBotState) -> Dict:
    topic = state["topic"]
    query = f"{topic} medical condition symptoms treatment causes reputable sources"
    raw_results = search_tool.invoke({"query": query})
    
    summary_prompt = f"""
    You are a medical assistant explaining concepts to a patient. 
    Using ONLY the following search results, provide a 3-4 paragraph patient-friendly explanation of the topic. 
    Do not use any external knowledge. If the context does not contain enough information, state that.
    
    Search Results: {raw_results}
    """
    summary_response = llm.invoke(summary_prompt)
    return {"search_results": str(raw_results), "summary": summary_response.content}

def generate_quiz(state: HealthBotState) -> Dict:
    # Ensure we have the summary from the state before generating the quiz
    summary_text = state.get("summary", "")
    quiz_prompt = f"""
    Based ONLY on the summary provided below, create a single, clear quiz question to test the patient's comprehension. 
    Do not include the answer in your response, just the question.
    
    Summary: {summary_text}
    """
    quiz_response = llm.invoke(quiz_prompt)
    return {"quiz_question": quiz_response.content}

def grade_quiz_response(state: HealthBotState) -> Dict:
    grade_prompt = f"""
    You are a medical educator. Grade the patient's answer to the quiz question based ONLY on the summary provided.
    
    Summary: {state['summary']}
    Quiz Question: {state['quiz_question']}
    Patient's Answer: {state['user_answer']}
    
    Provide a letter grade (e.g., A, B, C, D, F) and a justification for the grade. 
    Your justification MUST include direct quotes/citations from the Summary to reinforce learning.
    """
    grade_response = llm.invoke(grade_prompt)
    return {"grade_feedback": grade_response.content}

# --- 4. BUILD A LINEAR, ROBUST GRAPH ---
workflow = StateGraph(HealthBotState)
workflow.add_node("search_and_summarize", search_and_summarize)
workflow.add_node("generate_quiz", generate_quiz)
workflow.add_node("grade_quiz_response", grade_quiz_response)

# Linear flow ensures sequential state safety
workflow.set_entry_point("search_and_summarize")
workflow.add_edge("search_and_summarize", "generate_quiz")
workflow.add_edge("generate_quiz", "grade_quiz_response")
workflow.add_edge("grade_quiz_response", END)

healthbot_app = workflow.compile()

# --- 5. STREAMLIT UI MANAGEMENT ---
st.set_page_config(page_title="MediTech HealthBot", page_icon="🩺", layout="centered")
st.title("🩺 MediTech HealthBot")
st.caption("AI-Powered Patient Education System")

# Initialize state management dictionaries
if "graph_state" not in st.session_state:
    st.session_state.graph_state = {
        "topic": "", "user_answer": "", "search_results": "",
        "summary": "", "quiz_question": "", "grade_feedback": ""
    }
if "ui_step" not in st.session_state:
    st.session_state.ui_step = "TOPIC_INPUT"

# UI STEP 1: Topic Selection
if st.session_state.ui_step == "TOPIC_INPUT":
    st.subheader("What would you like to learn about today?")
    topic_input = st.text_input("Enter a health topic or medical condition:")
    
    if st.button("Search & Learn", type="primary"):
        if topic_input.strip() == "":
            st.warning("Please enter a valid topic.")
        else:
            with st.spinner("Searching reputable medical databases..."):
                # Run the first step node directly to populate the summary layout
                initial_input = {"topic": topic_input, "user_answer": "", "search_results": "", "summary": "", "quiz_question": "", "grade_feedback": ""}
                summary_state = search_and_summarize(initial_input)
                st.session_state.graph_state.update(initial_input)
                st.session_state.graph_state.update(summary_state)
                st.session_state.ui_step = "SHOW_SUMMARY"
                st.rerun()

# UI STEP 2: Display Summary / Handle Guardrail Rejection
elif st.session_state.ui_step == "SHOW_SUMMARY":
    st.header(f"Learning Topic: {st.session_state.graph_state['topic'].title()}")
    
    summary_text = st.session_state.graph_state["summary"]
    
    # Check if the guardrail prompt triggered a rejection
    if "I'm sorry, but I couldn't find reputable medical information" in summary_text:
        st.error(summary_text)
        if st.button("🔄 Try a Different Topic", type="primary"):
            st.session_state.graph_state = {
                "topic": "", "user_answer": "", "search_results": "",
                "summary": "", "quiz_question": "", "grade_feedback": ""
            }
            st.session_state.ui_step = "TOPIC_INPUT"
            st.rerun()
    else:
        # Normal Flow if it's a real medical topic
        st.markdown("### 📖 Medical Summary")
        st.info(summary_text)
        
        st.write("---")
        if st.button("I'm Ready for a Quiz! 🚀", type="primary"):
            with st.spinner("Generating comprehension quiz question..."):
                quiz_state = generate_quiz(st.session_state.graph_state)
                st.session_state.graph_state.update(quiz_state)
                st.session_state.ui_step = "TAKE_QUIZ"
                st.rerun()

# UI STEP 3: Quiz Assessment (FIXED VISIBILITY)
elif st.session_state.ui_step == "TAKE_QUIZ":
    st.header("🧠 Comprehension Check")
    
    # UI FIX: Added a distinct layout container to guarantee clear question display
    st.markdown("### ❓ Question:")
    st.warning(st.session_state.graph_state.get("quiz_question", "Loading question error..."))
    
    user_ans = st.text_area("Type your answer here:", key="patient_quiz_box")
    
    if st.button("Submit Answer", type="primary"):
        if user_ans.strip() == "":
            st.warning("Please input an answer before submitting.")
        else:
            with st.spinner("Evaluating response with source materials..."):
                st.session_state.graph_state["user_answer"] = user_ans
                # Run grading evaluation directly using accumulated state values
                grade_state = grade_quiz_response(st.session_state.graph_state)
                st.session_state.graph_state.update(grade_state)
                st.session_state.ui_step = "SHOW_RESULTS"
                st.rerun()

# UI STEP 4: Results & Reset Logic
elif st.session_state.ui_step == "SHOW_RESULTS":
    st.header("📋 Evaluation Feedback")
    st.markdown(st.session_state.graph_state["grade_feedback"])
    
    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Learn Another Topic", use_container_width=True):
            st.session_state.graph_state = {
                "topic": "", "user_answer": "", "search_results": "",
                "summary": "", "quiz_question": "", "grade_feedback": ""
            }
            st.session_state.ui_step = "TOPIC_INPUT"
            st.rerun()
    with col2:
        if st.button("❌ Exit Session", use_container_width=True):
            st.session_state.ui_step = "EXITED"
            st.rerun()

elif st.session_state.ui_step == "EXITED":
    st.success("Thank you for using MediTech HealthBot. Your session has safely closed.")
    st.info("Refresh the webpage to open a brand new session.")