PIPELINE_STATES = {
    "idle": {
        "label": "Ready to start",
        "next_action": "Fill the form and click Run Analysis"
    },
    "running_learning": {
        "label": "Building your learning plan",
        "next_action": "Please wait..."
    },
    "running_council": {
        "label": "Council debating your readiness",
        "next_action": "Please wait..."
    },
    "awaiting_assessment": {
        "label": "Ready for your mock exam",
        "next_action": "Take the interactive exam below"
    },
    "exam_in_progress": {
        "label": "Exam in progress",
        "next_action": "Answer all questions to continue"
    },
    "processing_results": {
        "label": "Evaluating your performance",
        "next_action": "Please wait..."
    },
    "complete": {
        "label": "Analysis complete",
        "next_action": "Review your results below"
    }
}
