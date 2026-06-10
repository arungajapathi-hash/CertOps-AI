import asyncio
from typing import Dict

from backend.memory import SharedMemory
from backend.agents.learning_agent import LearningAgent
from backend.agents.study_plan_agent import StudyPlanAgent
from backend.agents.engagement_agent import EngagementAgent
from backend.agents.council.optimist import OptimistAgent
from backend.agents.council.skeptic import SkepticAgent
from backend.agents.council.advocate import AdvocateAgent
from backend.agents.council.historian import HistorianAgent
from backend.agents.council.risk_analyst import RiskAnalystAgent
from backend.agents.council.critic import CriticAgent
from backend.agents.assessment_agent import AssessmentAgent
from backend.agents.socratic_coach import SocraticCoach
from backend.agents.reflection_agent import ReflectionAgent
from backend.agents.manager_insights import ManagerInsightsAgent
from backend.reputation.engine import ReputationEngine


class Orchestrator:
    def __init__(self) -> None:
        self.memory = SharedMemory()
        # Agents are created lazily to avoid LLM client initialization during import
        self.learning_agent = None
        self.study_plan_agent = None
        self.engagement_agent = None
        
        # Council agents for readiness phase
        self.optimist = None
        self.skeptic = None
        self.advocate = None
        self.historian = None
        self.risk_analyst = None
        self.critic = None
        
        # Assessment, coaching and reflection agents
        self.assessment_agent = None
        self.socratic_coach = None
        self.reflection_agent = None
        
        # Manager insights
        self.manager_insights = ManagerInsightsAgent()
        self.reputation = ReputationEngine()

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

    async def run_readiness_phase(self, learner_id: str) -> Dict:
        """Run the Readiness Council — 5 agents debate in parallel, Critic decides."""
        mem = self.memory.to_dict()
        
        # Verify memory has learning phase data
        if not mem.get("learner_id") or mem["learner_id"] != learner_id:
            raise ValueError("Run learning phase first with the same learner_id")
        
        # Lazy instantiation of council agents
        if self.optimist is None:
            self.optimist = OptimistAgent()
        if self.skeptic is None:
            self.skeptic = SkepticAgent()
        if self.advocate is None:
            self.advocate = AdvocateAgent()
        if self.historian is None:
            self.historian = HistorianAgent()
        if self.risk_analyst is None:
            self.risk_analyst = RiskAnalystAgent()
        if self.critic is None:
            self.critic = CriticAgent()
        
        # Step 1: Run all 5 council agents IN PARALLEL
        self._log("Council agents (parallel execution)")
        results = await asyncio.gather(
            self.optimist.execute(mem.copy()),
            self.skeptic.execute(mem.copy()),
            self.advocate.execute(mem.copy()),
            self.historian.execute(mem.copy()),
            self.risk_analyst.execute(mem.copy()),
            return_exceptions=True
        )
        
        # Step 2: Merge council votes from all results
        for result in results:
            if isinstance(result, dict) and "council_votes" in result:
                mem["council_votes"].update(result["council_votes"])
        
        # Step 3: Run Critic sequentially (needs all votes)
        self._log("CriticAgent (synthesis)")
        mem = await self.critic.execute(mem)
        
        # Step 4: Update main memory
        self.memory.update(mem)
        
        return {
            "learner_id": learner_id,
            "council_votes": mem.get("council_votes", {}),
            "verdict": mem.get("readiness_verdict"),
            "confidence": mem.get("readiness_confidence"),
            "reasoning": mem.get("readiness_reasoning"),
            "critic_output": mem.get("critic_output", {}),
            "session_log": mem.get("session_log", []),
        }

    async def run_assessment_phase(self, learner_id: str) -> Dict:
        """Generate assessment questions for the learner."""
        mem = self.memory.to_dict()
        
        # Verify memory has learning phase data
        if not mem.get("learner_id") or mem["learner_id"] != learner_id:
            raise ValueError("Run learning phase first with the same learner_id")
        
        # Lazy instantiation
        if self.assessment_agent is None:
            self.assessment_agent = AssessmentAgent()
        
        self._log("AssessmentAgent (generate questions)")
        mem = await self.assessment_agent.execute(mem)
        
        # Update main memory
        self.memory.update(mem)
        
        return {
            "learner_id": learner_id,
            "certification": mem.get("certification"),
            "questions": mem.get("assessment_questions", []),
            "status": "questions_ready",
            "session_log": mem.get("session_log", []),
        }

    async def submit_assessment(self, learner_id: str, answers: Dict) -> Dict:
        """Submit answers and get results with optional Socratic coaching."""
        mem = self.memory.to_dict()
        
        # Verify learner matches
        if not mem.get("learner_id") or mem["learner_id"] != learner_id:
            raise ValueError("Learner ID mismatch")
        
        # Lazy instantiation
        if self.assessment_agent is None:
            self.assessment_agent = AssessmentAgent()
        if self.socratic_coach is None:
            self.socratic_coach = SocraticCoach()
        
        # Evaluate answers
        self._log("AssessmentAgent (evaluate answers)")
        mem["last_answers"] = answers
        mem = await self.assessment_agent.evaluate(mem, answers)
        
        # Trigger Socratic Coach on FAIL
        socratic_triggered = mem.get("assessment_outcome") == "FAIL"
        if socratic_triggered:
            self._log("SocraticCoach (diagnose misconceptions)")
            mem = await self.socratic_coach.execute(mem)
        
        # Update main memory
        self.memory.update(mem)
        
        return {
            "learner_id": learner_id,
            "score": mem.get("assessment_score"),
            "outcome": mem.get("assessment_outcome"),
            "topic_breakdown": mem.get("assessment_breakdown"),
            "socratic_triggered": socratic_triggered,
            "misconceptions": mem.get("misconceptions", []),
            "socratic_questions": mem.get("socratic_questions", []),
            "remediation": mem.get("remediation", {}),
            "session_log": mem.get("session_log", []),
        }

    async def run_reflection_phase(self, learner_id: str, actual_outcome: str) -> Dict:
        """Run reflection to compare prediction vs actual and update reputations."""
        mem = self.memory.to_dict()
        
        # Verify learner matches
        if not mem.get("learner_id") or mem["learner_id"] != learner_id:
            raise ValueError("Learner ID mismatch")
        
        # Lazy instantiation
        if self.reflection_agent is None:
            self.reflection_agent = ReflectionAgent()
        
        self._log("ReflectionAgent (self-learning analysis)")
        mem["assessment_outcome"] = actual_outcome
        mem = await self.reflection_agent.execute(mem)
        
        # Update main memory
        self.memory.update(mem)
        
        return {
            "learner_id": learner_id,
            "reflection": mem.get("reflection", {}),
            "updated_reputation": self.reputation.get_all_scores(),
            "session_log": mem.get("session_log", []),
        }

    def get_manager_insights(self) -> Dict:
        """Get team-level insights from manager analytics."""
        return self.manager_insights.get_insights()