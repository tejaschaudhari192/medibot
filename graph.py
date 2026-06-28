from langgraph.graph import StateGraph
from state import HealthBotState
from nodes import (
    collect_topic,
    search_medical_info,
    generate_summary,
    prompt_readiness,
    create_quiz,
    administer_quiz,
    grade_quiz,
    check_continuation,
    route_continuation
)

# Build the graph
workflow = StateGraph(HealthBotState)

# Add all nodes
workflow.add_node("collect_topic", collect_topic)
workflow.add_node("search_medical_info", search_medical_info)
workflow.add_node("generate_summary", generate_summary)
workflow.add_node("prompt_readiness", prompt_readiness)
workflow.add_node("create_quiz", create_quiz)
workflow.add_node("administer_quiz", administer_quiz)
workflow.add_node("grade_quiz", grade_quiz)
workflow.add_node("check_continuation", check_continuation)

# Define sequential edges
workflow.add_edge("collect_topic", "search_medical_info")
workflow.add_edge("search_medical_info", "generate_summary")
workflow.add_edge("generate_summary", "prompt_readiness")
workflow.add_edge("prompt_readiness", "create_quiz")
workflow.add_edge("create_quiz", "administer_quiz")
workflow.add_edge("administer_quiz", "grade_quiz")
workflow.add_edge("grade_quiz", "check_continuation")

# Define conditional edge for resetting or ending
workflow.add_conditional_edges(
    "check_continuation",
    route_continuation
)

# Set the entry point and compile
workflow.set_entry_point("collect_topic")
healthbot_app = workflow.compile()

# Execution trigger
if __name__ == "__main__":
    # Initialize with an empty state
    initial_state = {
        "topic": "",
        "user_answer": "",
        "search_results": "",
        "summary": "",
        "quiz_question": "",
        "grade_feedback": "",
        "is_ready_for_quiz": False,
        "continue_session": False
    }
    # Stream the graph execution
    healthbot_app.invoke(initial_state, config={"recursion_limit": 50})
