from typing import Dict
from config import llm, search_tool

def collect_topic(state: Dict) -> Dict:
    # Requirement: Ask the patient what health topic they'd like to learn about
    print("\n--- Welcome to MediTech HealthBot ---")
    topic = input("What health topic or medical condition would you like to learn about today? \n> ")
    return {"topic": topic}

def search_medical_info(state: Dict) -> Dict:
    # Requirement: Search Tavily focusing on reputable medical sources
    topic = state["topic"]
    print(f"\n[Searching for reputable medical information on '{topic}'...]")
    # Appending context to guide Tavily towards medical sources
    query = f"{topic} medical condition symptoms treatment causes reputable sources"
    search_results = search_tool.invoke({"query": query})
    return {"search_results": str(search_results)}

def generate_summary(state: Dict) -> Dict:
    # Requirement: Summarize search results in 3-4 patient-friendly paragraphs using NO other knowledge
    prompt = f"""
    You are a medical assistant explaining concepts to a patient. 
    Using ONLY the following search results, provide a 3-4 paragraph patient-friendly explanation of the topic. 
    Do not use any external knowledge. If the context does not contain enough information, state that.
    
    Search Results: {state['search_results']}
    """
    response = llm.invoke(prompt)
    summary = response.content
    print("\n--- Summary ---")
    print(summary)
    print("---------------")
    return {"summary": summary}

def prompt_readiness(state: Dict) -> Dict:
    # Requirement: Prompt patient to indicate when they're ready for a comprehension check
    ready = ""
    while ready.lower() not in ['y', 'yes']:
        ready = input("\nAre you ready for a quick comprehension check? (y/yes) \n> ")
    return {"is_ready_for_quiz": True}

def create_quiz(state: Dict) -> Dict:
    # Requirement: Generate a single relevant quiz question based on the provided information alone
    prompt = f"""
    Based ONLY on the summary provided below, create a single, clear quiz question to test the patient's comprehension. 
    Do not include the answer in your response, just the question.
    
    Summary: {state['summary']}
    """
    response = llm.invoke(prompt)
    return {"quiz_question": response.content}

def administer_quiz(state: Dict) -> Dict:
    # Requirement: Present question and collect answer
    print("\n--- Comprehension Check ---")
    print(state["quiz_question"])
    user_answer = input("\nYour answer: \n> ")
    return {"user_answer": user_answer}

def grade_quiz(state: Dict) -> Dict:
    # Requirement: Evaluate response, provide a grade (A, B, C, etc.), and explanation with citations from the summary
    prompt = f"""
    You are a medical educator. Grade the patient's answer to the quiz question based ONLY on the summary provided.
    
    Summary: {state['summary']}
    Quiz Question: {state['quiz_question']}
    Patient's Answer: {state['user_answer']}
    
    Provide a letter grade (e.g., A, B, C, D, F) and a justification for the grade. 
    Your justification MUST include direct quotes/citations from the Summary to reinforce learning.
    """
    response = llm.invoke(prompt)
    feedback = response.content
    print("\n--- Quiz Results ---")
    print(feedback)
    print("--------------------")
    return {"grade_feedback": feedback}

def check_continuation(state: Dict) -> Dict:
    # Requirement: Ask if patient wants a new topic or to exit. Reset state if new topic to maintain privacy.
    choice = input("\nWould you like to learn about another health topic? (y/n) \n> ")
    if choice.lower() in ['y', 'yes']:
        # Return a completely cleared state dict to reset for the next run
        return {
            "topic": "",
            "user_answer": "",
            "search_results": "",
            "summary": "",
            "quiz_question": "",
            "grade_feedback": "",
            "is_ready_for_quiz": False,
            "continue_session": True
        }
    else:
        print("\nThank you for using MediTech HealthBot. Goodbye!")
        return {"continue_session": False}

def route_continuation(state: Dict):
    if state.get("continue_session"):
        return "collect_topic"
    from langgraph.graph import END
    return END
