from typing import TypedDict

class HealthBotState(TypedDict):
    # Patient inputs
    topic: str                 # The health topic entered by the patient
    user_answer: str           # The patient's answer to the quiz
    
    # LLM & Tool outputs
    search_results: str        # Raw context retrieved from Tavily
    summary: str               # The 3-4 paragraph patient-friendly summary
    quiz_question: str         # The single generated quiz question
    grade_feedback: str        # The final grade and citation-backed justification
    
    # Workflow control
    is_ready_for_quiz: bool    # Tracks if the patient indicated they are ready
    continue_session: bool     # Tracks if the patient wants to learn a new topic
