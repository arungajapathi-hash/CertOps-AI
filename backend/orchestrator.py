import asyncio
import json
import random
from typing import Dict, Callable, Optional

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
        
        # Extract weak topics from assessment breakdown
        topic_breakdown = mem.get("assessment_breakdown", {})
        if topic_breakdown:
            # Find topics below 60%
            weak_topics = [
                topic for topic, data in topic_breakdown.items()
                if data.get("score", 100) < 60
            ]
            
            # If no topics below 60, get lowest 2 topics
            if not weak_topics:
                sorted_topics = sorted(
                    topic_breakdown.items(),
                    key=lambda x: x[1].get("score", 0)
                )
                weak_topics = [t[0] for t in sorted_topics[:2]]
            
            mem["weak_topics"] = weak_topics
            print(f"[Debug] Extracted weak_topics: {weak_topics}")
        
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

    async def run_full_pipeline(
        self,
        learner_id: str,
        role: str,
        certification: str,
        target_weeks: int,
        progress_callback: Optional[Callable] = None
    ) -> dict:
        """
        Runs the complete CertOps AI pipeline automatically.
        Each phase result feeds into the next.
        Adapts plan if discrepancies found.
        Returns consolidated report.
        """
        
        report = {
            "learner_id": learner_id,
            "certification": certification,
            "phases": {},
            "adaptations": [],
            "final_verdict": "",
            "consolidated_plan": {}
        }

        # PHASE 1: Learning
        if progress_callback:
            await progress_callback("phase_start", "Learning Phase", 1, 6)
        
        mem = await self.run_learning_phase(
            learner_id, role, certification, target_weeks
        )
        report["phases"]["learning"] = {
            "status": "complete",
            "skill_map": mem.get("skill_map", []),
            "study_plan": mem.get("study_plan", {}),
            "weak_topics": mem.get("weak_topics", [])
        }

        if progress_callback:
            await progress_callback("phase_done", "Learning Phase", 1, 6)

        # PHASE 2: Readiness Council
        if progress_callback:
            await progress_callback("phase_start", "Readiness Council", 2, 6)
        
        council_result = await self.run_readiness_phase(learner_id)
        report["phases"]["council"] = {
            "status": "complete",
            "votes": council_result.get("council_votes", {}),
            "verdict": council_result.get("verdict", ""),
            "confidence": council_result.get("confidence", 0)
        }

        # ADAPTATION 1: Check council discrepancies
        # Debug logging
        council_votes = council_result.get('council_votes', {})
        print(f"[Debug] Council votes keys: {list(council_votes.keys())}")
        print(f"[Debug] Verdicts: {[v.get('verdict') for v in council_votes.values()]}")
        
        adaptations = self._check_council_discrepancies(
            council_result, self.memory.to_dict()
        )
        
        if adaptations:
            if progress_callback:
                await progress_callback(
                    "adaptation", 
                    f"Adapting plan: {adaptations[0]['reason']}", 
                    2, 6
                )
            
            # Apply adaptations to study plan
            mem = await self._adapt_learning_plan(
                self.memory.to_dict(), adaptations
            )
            self.memory.update(mem)
            report["adaptations"].extend(adaptations)
            
            report["phases"]["learning"]["study_plan"] = \
                mem.get("study_plan", {})
            report["phases"]["learning"]["adapted"] = True

        if progress_callback:
            await progress_callback("phase_done", "Readiness Council", 2, 6)

        # PHASE 3: Assessment
        if progress_callback:
            await progress_callback("phase_start", "Assessment", 3, 6)
        
        assessment_result = await self.run_assessment_phase(learner_id)
        report["phases"]["assessment"] = {
            "status": "questions_ready",
            "question_count": len(
                assessment_result.get("questions", [])
            )
        }

        if progress_callback:
            await progress_callback("phase_done", "Assessment", 3, 6)

        # PHASE 4: Auto-evaluate with simulated answers
        # For pipeline demo: use practice_score to simulate
        practice_score = self.memory.to_dict().get(
            "practice_score_avg", 65
        )
        simulated_answers = self._simulate_answers(
            assessment_result.get("questions", []),
            practice_score
        )
        
        submit_result = await self.submit_assessment(
            learner_id, simulated_answers
        )
        
        outcome = submit_result.get("outcome", "FAIL")
        score = submit_result.get("score", 0)
        
        report["phases"]["assessment"]["status"] = "complete"
        report["phases"]["assessment"]["score"] = score
        report["phases"]["assessment"]["outcome"] = outcome
        report["phases"]["assessment"]["breakdown"] = \
            submit_result.get("topic_breakdown", {})

        # ADAPTATION 2: If FAIL → update study plan
        if outcome == "FAIL":
            if progress_callback:
                await progress_callback(
                    "adaptation",
                    f"Assessment failed ({score:.1f}%) — updating study plan",
                    4, 6
                )
            
            mem = self.memory.to_dict()
            fail_adaptation = {
                "reason": f"Assessment score {score:.1f}% below threshold",
                "action": "Reinforced weak topics in study plan",
                "weak_topics": mem.get("weak_topics", []),
                "additional_hours": 5
            }
            
            mem = await self._adapt_learning_plan(
                mem, [fail_adaptation]
            )
            self.memory.update(mem)
            report["adaptations"].append(fail_adaptation)

        # PHASE 5: Coaching if failed
        if progress_callback:
            await progress_callback("phase_start", "Coaching", 5, 6)
        
        if outcome == "FAIL":
            coaching_result = await self.submit_assessment(
                learner_id, simulated_answers
            )
            report["phases"]["coaching"] = {
                "status": "complete",
                "triggered": True,
                "misconceptions": self.memory.to_dict().get(
                    "misconceptions", []
                ),
                "socratic_questions": self.memory.to_dict().get(
                    "socratic_questions", []
                ),
                "remediation": self.memory.to_dict().get(
                    "remediation", {}
                )
            }
        else:
            report["phases"]["coaching"] = {
                "status": "skipped",
                "triggered": False,
                "reason": "Assessment passed — coaching not needed"
            }

        if progress_callback:
            await progress_callback("phase_done", "Coaching", 5, 6)

        # PHASE 6: Reflection
        if progress_callback:
            await progress_callback("phase_start", "Reflection", 6, 6)
        
        reflection_result = await self.run_reflection_phase(
            learner_id, outcome
        )
        report["phases"]["reflection"] = {
            "status": "complete",
            "analysis": reflection_result.get(
                "reflection", {}
            ).get("analysis", ""),
            "updated_reputation": reflection_result.get(
                "updated_reputation", []
            )
        }

        if progress_callback:
            await progress_callback("phase_done", "Reflection", 6, 6)

        # Build consolidated report
        mem = self.memory.to_dict()
        report["final_verdict"] = mem.get("readiness_verdict", "")
        report["final_confidence"] = mem.get("readiness_confidence", 0)
        report["consolidated_plan"] = {
            "skill_map": mem.get("skill_map", []),
            "study_plan": mem.get("study_plan", {}),
            "weak_topics": mem.get("weak_topics", []),
            "recommended_materials": mem.get(
                "recommended_materials", []
            ),
            "work_signals": mem.get("work_signals", {}),
            "total_adaptations": len(report["adaptations"])
        }
        report["session_log"] = mem.get("session_log", [])
        report["status"] = "pipeline_complete"

        return report

    def _check_council_discrepancies(
        self, council_result: dict, memory: dict
    ) -> list:
        """
        Check if council agents disagree significantly.
        Returns list of adaptations needed.
        """
        votes = council_result.get("council_votes", {})
        adaptations = []

        if not votes:
            return adaptations

        # Debug: print votes structure
        print(f"[Debug] _check_council_discrepancies votes: {votes}")
        
        # Count verdicts - handle both nested formats
        verdicts = []
        for agent_name, vote_data in votes.items():
            # Handle both formats: {verdict: X} or nested structure
            verdict = vote_data.get("verdict") if isinstance(vote_data, dict) else None
            if verdict:
                verdicts.append(verdict)
        
        print(f"[Debug] Extracted verdicts: {verdicts}")
        
        ready_count = sum(1 for v in verdicts if v == "READY")
        not_ready_count = sum(1 for v in verdicts if v == "NOT_READY")
        delay_count = sum(1 for v in verdicts if v == "DELAY")

        # Discrepancy 1: Split council - Always adapt if any mix of verdicts
        # Always trigger on split (READY + NOT_READY or DELAY + others)
        unique_verdicts = set(verdicts)
        print(f"[Debug] Unique verdicts: {unique_verdicts}")
        
        has_split = (
            ("READY" in unique_verdicts and "NOT_READY" in unique_verdicts) or
            ("DELAY" in unique_verdicts and len(unique_verdicts) > 1)
        )
        
        if has_split and len(votes) > 1:
            print(f"[Debug] Council split detected, generating adaptation")
            # Find what skeptic/risk flagged
            skeptic = votes.get("skeptic", {})
            risk = votes.get("risk_analyst", {})
            
            weak_signals = []
            for v in [skeptic, risk]:
                if isinstance(v, dict):
                    weak_signals.extend(v.get("evidence", []))
            
            adaptations.append({
                "type": "council_split",
                "reason": "Council split between different verdicts",
                "action": "Added focused review sessions for disputed areas",
                "signals": weak_signals[:3],
                "plan_change": "add_review_sessions"
            })

        # Discrepancy 2: Advocate flagged workload
        advocate = votes.get("advocate", {})
        if advocate.get("verdict") in ["NOT_READY", "DELAY"]:
            work = memory.get("work_signals", {})
            meeting_hours = work.get("meeting_hours_per_week", 0)
            
            if meeting_hours > 18:
                adaptations.append({
                    "type": "workload_risk",
                    "reason": f"High meeting load ({meeting_hours}h/week)",
                    "action": "Extended timeline by 1 week, reduced daily hours",
                    "plan_change": "extend_timeline"
                })

        # Discrepancy 3: Historian found bad pattern
        historian = votes.get("historian", {})
        if historian.get("verdict") == "NOT_READY":
            adaptations.append({
                "type": "historical_risk",
                "reason": "Similar learners historically struggled",
                "action": "Added extra practice sessions from Historian's pattern",
                "plan_change": "add_practice_sessions"
            })

        return adaptations

    async def _adapt_learning_plan(
        self, memory: dict, adaptations: list
    ) -> dict:
        """
        Uses LLM to adapt the study plan based on findings.
        """
        if not adaptations:
            return memory

        system_prompt = """You are a learning plan optimizer.
Based on discrepancies found by the readiness council,
adapt the existing study plan to address weaknesses.
Return only valid JSON with the updated study plan."""

        adaptation_summary = "\n".join([
            f"- {a['reason']}: {a['action']}"
            for a in adaptations
        ])

        current_plan = json.dumps(
            memory.get("study_plan", {}), indent=2
        )
        weak_topics = memory.get("weak_topics", [])

        user_prompt = f"""
Current study plan:
{current_plan[:1500]}

Weak topics identified: {weak_topics}

Council findings requiring plan adaptation:
{adaptation_summary}

Adapt the study plan to address these issues.
Add review sessions for weak areas.
Do not reduce total coverage.

Return JSON with same structure as input plan 
but with adaptations applied.
Add an "adapted": true field to modified weeks.
"""

        response = self._call_llm_sync(system_prompt, user_prompt)
        
        try:
            clean = response.strip().strip("```json").strip("```")
            adapted_plan = json.loads(clean)
            memory["study_plan"] = adapted_plan
            memory["plan_adapted"] = True
            memory["adaptations"] = adaptations
        except:
            # Keep original plan if parsing fails
            memory["plan_adapted"] = False

        return memory

    def _simulate_answers(
        self, questions: list, practice_score: float
    ) -> dict:
        """
        Simulate exam answers based on practice score.
        Used for automated pipeline demo.
        Higher practice score = more correct answers.
        """
        answers = {}
        correct_rate = practice_score / 100
        
        for q in questions:
            qid = str(q["id"])
            correct = q.get("correct_answer", "A")
            options = list(q.get("options", {}).keys())
            
            if random.random() < correct_rate:
                answers[qid] = correct
            else:
                wrong = [o for o in options if o != correct]
                answers[qid] = random.choice(wrong) if wrong else correct
        
        return answers

    def _call_llm_sync(
        self, system_prompt: str, user_prompt: str
    ) -> str:
        """Synchronous LLM call for adapter methods"""
        from backend.agents.base_agent import BaseAgent
        agent = BaseAgent("PipelineAdapter")
        return agent._call_llm(system_prompt, user_prompt)
