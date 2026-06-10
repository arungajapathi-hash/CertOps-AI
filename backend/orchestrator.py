import asyncio
from typing import Dict

from backend.memory import SharedMemory
from backend.agents.learning_agent import LearningAgent
from backend.agents.study_plan_agent import StudyPlanAgent
from backend.agents.engagement_agent import EngagementAgent


class Orchestrator:
    def __init__(self) -> None:
        self.memory = SharedMemory()
        # Agents are created lazily to avoid LLM client initialization during import
        self.learning_agent = None
        self.study_plan_agent = None
        self.engagement_agent = None

    def _log(self, agent_name: str) -> None:
        print(f"[ORCHESTRATOR] Calling {agent_name}")

    async def run_learning_phase(self, learner_id: str, role: str, certification: str, target_weeks: int) -> Dict:
        # Reset and seed memory
        self.memory.reset()
        self.memory.update({
            "learner_id": learner_id,
            "role": role,
            "certification": certification,
            "target_weeks": target_weeks,
        })
        mem = self.memory.to_dict()

        # Lazy instantiation of agents
        if self.learning_agent is None:
            self.learning_agent = LearningAgent()
        if self.study_plan_agent is None:
            self.study_plan_agent = StudyPlanAgent()
        if self.engagement_agent is None:
            self.engagement_agent = EngagementAgent()

        # Run Learning Agent
        self._log("LearningAgent")
        mem = await self.learning_agent.execute(mem)

        # Run Study Plan Agent
        self._log("StudyPlanAgent")
        mem = await self.study_plan_agent.execute(mem)

        # Run Engagement Agent
        self._log("EngagementAgent")
        mem = await self.engagement_agent.execute(mem)

        # Persist back to shared memory
        self.memory.update(mem)

        return {
            "learner_id": learner_id,
            "certification": certification,
            "skill_map": mem.get("skill_map"),
            "study_plan": mem.get("study_plan"),
            "work_signals": mem.get("work_signals"),
            "recommended_materials": mem.get("recommended_materials"),
            "session_log": mem.get("session_log"),
            "status": "learning_phase_complete",
        }