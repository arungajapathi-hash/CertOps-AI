import json


class SharedMemory:
    def __init__(self) -> None:
        self._memory = {}
        self.reset()

    def get(self, key):
        return self._memory.get(key)

    def set(self, key, value):
        self._memory[key] = value

    def update(self, data: dict):
        if not isinstance(data, dict):
            raise ValueError("update() requires a dictionary")
        self._memory.update(data)

    def reset(self):
        self._memory = {
            "learner_id": "",
            "role": "",
            "certification": "",
            "target_weeks": 0,
            "skill_map": [],
            "recommended_materials": [],
            "study_plan": {},
            "work_signals": {},
            "practice_score_avg": 0,
            "hours_studied": 0,
            "weak_topics": [],
            "council_votes": {},
            "readiness_verdict": "",
            "readiness_confidence": 0,
            "readiness_reasoning": "",
            "assessment_score": 0,
            "assessment_breakdown": {},
            "assessment_outcome": "",
            "misconceptions": [],
            "socratic_questions": [],
            "reflection": {},
            "session_log": [],
        }

    def to_dict(self):
        return dict(self._memory)

    def snapshot(self):
        return json.dumps(self._memory, indent=2)
