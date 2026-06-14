import asyncio
import json
import logging
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

logger = logging.getLogger("certops.orchestrator")


class Orchestrator:
    def __init__(self) -> None:
        # Per-learner memory isolation: each learner_id gets its own SharedMemory
        # so concurrent/sequential users never clobber each other's pipeline state.
        self._sessions: Dict[str, SharedMemory] = {}
        self.memory = SharedMemory()  # default/unbound memory
        # Cache of generated learning resources keyed by cert + topic set, so the
        # (slower) Foundry-grounded official lookup isn't repeated for the same
        # certification across runs in this server session.
        self._resource_cache: Dict[str, dict] = {}
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

    def _bind(self, learner_id: str) -> None:
        """Point self.memory at this learner's isolated SharedMemory.

        Called at the top of every public entrypoint so each learner's
        pipeline state (skill map, council votes, exam, results) stays
        separate. Idempotent — nested phase calls rebind to the same id.
        """
        if not learner_id:
            return
        mem = self._sessions.get(learner_id)
        if mem is None:
            mem = SharedMemory()
            mem.set("learner_id", learner_id)
            self._sessions[learner_id] = mem
        self.memory = mem

    def _log(self, agent_name: str) -> None:
        print(f"[ORCHESTRATOR] Calling {agent_name}")

    async def run_learning_phase(self, learner_id: str, role: str, certification: str, target_weeks: int) -> Dict:
        self._bind(learner_id)
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
        self._bind(learner_id)
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
        self._bind(learner_id)
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

        result = {
            "learner_id": learner_id,
            "certification": mem.get("certification"),
            "questions": mem.get("assessment_questions", []),
            "status": "questions_ready",
            "session_log": mem.get("session_log", []),
        }
        logger.debug(f"/assessment result: {len(result['questions'])} questions generated")
        return result

    async def submit_assessment(self, learner_id: str, answers: Dict) -> Dict:
        """Submit answers and get results with optional Socratic coaching."""
        self._bind(learner_id)
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
            logger.debug(f"Extracted weak_topics: {weak_topics}")

        # Trigger Socratic Coach on FAIL
        socratic_triggered = mem.get("assessment_outcome") == "FAIL"
        if socratic_triggered:
            self._log("SocraticCoach (diagnose misconceptions)")
            mem = await self.socratic_coach.execute(mem)

        # Update main memory
        self.memory.update(mem)

        result = {
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
        logger.debug(f"/submit result: score={result['score']}, outcome={result['outcome']}")
        return result

    async def run_reflection_phase(self, learner_id: str, actual_outcome: str) -> Dict:
        """Run reflection to compare prediction vs actual and update reputations."""
        self._bind(learner_id)
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

    async def run_coaching_phase(self, learner_id: str) -> dict:
        """Run Socratic coaching phase independently."""
        self._bind(learner_id)
        mem = self.memory.to_dict()
        if self.socratic_coach is None:
            self.socratic_coach = SocraticCoach()
        self._log("SocraticCoach (diagnose misconceptions)")
        mem = await self.socratic_coach.execute(mem)
        self.memory.update(mem)
        return {
            "misconceptions": mem.get("misconceptions", []),
            "socratic_questions": mem.get("socratic_questions", []),
            "remediation": mem.get("remediation", {})
        }

    def get_manager_insights(self) -> Dict:
        """Get team-level insights from manager analytics."""
        return self.manager_insights.get_insights()

    async def _fetch_learning_resources(self, memory: dict) -> dict:
        """Fetch learning resources for all relevant topics."""
        from backend.plugins.resource_finder import ResourceFinder
        finder = ResourceFinder()
        resources = {}

        # Preserve priority order: weak topics first, then the broader skill map.
        topics_to_fetch = []
        seen_topics = set()
        for raw_topic in memory.get("weak_topics", []) + memory.get("skill_map", []):
            topic = str(raw_topic).strip()
            topic_key = topic.lower()
            if topic and topic_key not in seen_topics:
                topics_to_fetch.append(topic)
                seen_topics.add(topic_key)
            if len(topics_to_fetch) >= 8:
                break

        cert = memory.get("certification", "")
        logger.debug(f"_fetch_learning_resources for {len(topics_to_fetch)} topics: {topics_to_fetch}")

        # Session cache: reuse if we've already built resources for this exact
        # certification + topic set (avoids repeating the Foundry official lookup).
        cache_key = cert + "|" + "|".join(sorted(t.lower() for t in topics_to_fetch))
        if cache_key in self._resource_cache:
            logger.debug(f"Reusing cached learning resources for {cache_key[:60]}")
            memory["learning_resources"] = self._resource_cache[cache_key]
            return memory

        # Base bundle: MVP / videos / practice are topic-specific search URLs.
        for topic in topics_to_fetch:
            resources[topic] = finder.find_resources(cert, topic)

        # Official resources: the MS Learn Catalog API returns the same generic
        # modules for every topic, so ground them in Foundry IQ instead — one
        # call for all topics gives real, topic-specific learn.microsoft.com links.
        try:
            foundry_official = await asyncio.to_thread(
                self._foundry_official_resources, cert, topics_to_fetch
            )
            for topic, items in foundry_official.items():
                if items and topic in resources:
                    resources[topic]["official"] = items
        except Exception as e:
            logger.debug(f"Foundry resource grounding failed, keeping deterministic: {e}")

        self._resource_cache[cache_key] = resources
        memory["learning_resources"] = resources
        return memory

    def _foundry_official_resources(self, cert: str, topics: list) -> dict:
        """Ask Foundry IQ for official MS Learn resources per topic (one call).

        Returns {topic: [{title, url, ...}]}. Only accepts real
        learn.microsoft.com URLs so nothing hallucinated reaches the UI.
        """
        from backend.plugins.knowledge_router import get_knowledge_plugin
        plugin = get_knowledge_plugin()
        query = getattr(plugin, "query", None)
        if not callable(query):
            return {}

        topic_list = "\n".join(f"- {t}" for t in topics)
        prompt = (
            f"For the {cert} certification, recommend 2-3 official Microsoft Learn "
            f"modules or documentation pages for EACH topic below. Use only real "
            f"learn.microsoft.com URLs grounded in the knowledge base.\n\n"
            f"Topics:\n{topic_list}\n\n"
            f"Return ONLY JSON mapping each topic to a list:\n"
            f'{{"<topic name>": [{{"title": "...", "url": "https://learn.microsoft.com/..."}}]}}'
        )
        raw = query(prompt, isolation_suffix="resources") or ""
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        try:
            data = json.loads(clean.strip())
        except Exception:
            return {}
        if not isinstance(data, dict):
            return {}

        out = {}
        lower_map = {k.lower(): v for k, v in data.items()}
        for topic in topics:
            items = data.get(topic) or lower_map.get(topic.lower()) or []
            bundle = []
            for it in (items if isinstance(items, list) else [])[:3]:
                if not isinstance(it, dict):
                    continue
                url = str(it.get("url", "")).strip()
                title = str(it.get("title", "")).strip()
                if title and url.startswith("http") and "learn.microsoft.com" in url:
                    bundle.append({
                        "title": title,
                        "url": url,
                        "type": "MS Learn (Foundry IQ)",
                        "source": "Microsoft Learn · Foundry IQ",
                        "free": True,
                        "verified": True,
                    })
            if bundle:
                out[topic] = bundle
        return out

    async def run_full_pipeline(
        self,
        learner_id: str,
        role: str,
        certification: str,
        target_weeks: int,
        progress_callback: Optional[Callable] = None,
        interactive_assessment: bool = True  # NEW: if True, pauses before assessment
    ) -> dict:
        """
        Runs the complete CertOps AI pipeline automatically.
        If interactive_assessment=True, pauses after Phase 2
        for user to take the real quiz.
        Each phase result feeds into the next.
        Adapts plan if discrepancies found.
        Returns consolidated report or partial report awaiting assessment.
        """
        self._bind(learner_id)

        report = {
            "learner_id": learner_id,
            "certification": certification,
            "phases": {},
            "adaptations": [],
            "final_verdict": "",
            "consolidated_plan": {}
        }
        current_mem = self.memory.to_dict()
        can_reuse_context = (
            current_mem.get("learner_id") == learner_id
            and current_mem.get("certification") == certification
        )

        # PHASE 1: Learning
        # Update pipeline state
        self.memory.update({"pipeline_state": "running_learning"})
        if progress_callback:
            await progress_callback("phase_start", "Learning Phase", 1, 6)

        if can_reuse_context and current_mem.get("skill_map"):
            mem = current_mem
        else:
            mem = await self.run_learning_phase(
                learner_id, role, certification, target_weeks
            )
        report["phases"]["learning"] = {
            "status": "complete",
            "skill_map": mem.get("skill_map", []),
            "study_plan": mem.get("study_plan", {}),
            "weak_topics": mem.get("weak_topics", [])
        }

        # Fetch learning resources for the active topic set.
        mem = self.memory.to_dict()
        expected_topics = []
        seen_topics = set()
        for raw_topic in mem.get("weak_topics", []) + mem.get("skill_map", []):
            topic = str(raw_topic).strip()
            topic_key = topic.lower()
            if topic and topic_key not in seen_topics:
                expected_topics.append(topic)
                seen_topics.add(topic_key)
            if len(expected_topics) >= 8:
                break
        current_topics = list(mem.get("learning_resources", {}).keys())
        if current_topics != expected_topics:
            mem = await self._fetch_learning_resources(mem)
            self.memory.update(mem)
            logger.debug(f"Resources fetched for: {list(mem.get('learning_resources', {}).keys())}")

        if progress_callback:
            await progress_callback("phase_done", "Learning Phase", 1, 6)

        # PHASE 2: Readiness Council
        # Update pipeline state
        self.memory.update({"pipeline_state": "running_council"})
        if progress_callback:
            await progress_callback("phase_start", "Readiness Council", 2, 6)

        mem = self.memory.to_dict()
        if can_reuse_context and mem.get("readiness_verdict"):
            council_result = {
                "council_votes": mem.get("council_votes", {}),
                "verdict": mem.get("readiness_verdict", ""),
                "confidence": mem.get("readiness_confidence", 0),
                "reasoning": mem.get("readiness_reasoning", ""),
            }
        else:
            council_result = await self.run_readiness_phase(learner_id)
        report["phases"]["council"] = {
            "status": "complete",
            "votes": council_result.get("council_votes", {}),
            "verdict": council_result.get("verdict", ""),
            "confidence": council_result.get("confidence", 0),
            "reasoning": council_result.get("reasoning", "")
        }

        # ADAPTATION 1: Check council discrepancies
        logger.debug(f"Council votes keys: {list(council_result.get('council_votes', {}).keys())}")
        logger.debug(f"Verdicts: {[v.get('verdict') for v in council_result.get('council_votes', {}).values()]}")

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
        if interactive_assessment:
            # LAZY GENERATION — pause here WITHOUT generating questions. They are
            # generated on demand when the learner clicks "Start Mock Exam", so
            # this analysis stays fast (learning + council only).
            report["phases"]["assessment"] = {
                "status": "deferred",
                "question_count": 0,
                "questions": [],
            }
            report["status"] = "awaiting_assessment"
            report["pipeline_paused_at"] = "assessment"
            self.memory.update({"pipeline_state": "awaiting_assessment"})
            if progress_callback:
                await progress_callback("phase_done", "Readiness Council", 2, 6)
            return report

        # --- Auto mode (interactive_assessment=False): generate questions now ---
        self.memory.update({"pipeline_state": "exam_in_progress"})
        if progress_callback:
            await progress_callback("phase_start", "Assessment", 3, 6)

        assessment_result = await self.run_assessment_phase(learner_id)
        report["phases"]["assessment"] = {
            "status": "questions_ready",
            "question_count": len(assessment_result.get("questions", [])),
            "questions": assessment_result.get("questions", [])
        }
        if progress_callback:
            await progress_callback("phase_done", "Assessment", 3, 6)

        # Auto-evaluate with simulated answers
        # Update pipeline state to processing while evaluating
        self.memory.update({"pipeline_state": "processing_results"})
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
            "total_adaptations": len(report["adaptations"]),
            "learning_resources": mem.get("learning_resources", {})
        }
        report["session_log"] = mem.get("session_log", [])
        report["status"] = "pipeline_complete"
        self.memory.update({"pipeline_state": "complete"})

        return report

    async def continue_pipeline_after_assessment(
        self,
        learner_id: str,
        answers: dict,
        progress_callback: Optional[Callable] = None
    ) -> dict:
        """
        Called after user completes interactive quiz.
        Runs Phase 3 evaluation + Phase 4 (Coaching) + Phase 5 (Reflection).
        Returns consolidated report.
        """
        logger.debug(f"/pipeline/continue called with {len(answers)} answers")

        self._bind(learner_id)
        mem = self.memory.to_dict()
        report = {
            "learner_id": learner_id,
            "phases": {},
            "adaptations": mem.get("adaptations", []),
            "final_verdict": "",
            "consolidated_plan": {}
        }

        # PHASE 3: Evaluate real answers
        if progress_callback:
            await progress_callback("phase_start", "Assessment Evaluation", 3, 5)

        # Update pipeline state to processing while evaluation runs
        self.memory.update({"pipeline_state": "processing_results"})

        submit_result = await self.submit_assessment(learner_id, answers)
        outcome = submit_result.get("outcome", "FAIL")
        score = submit_result.get("score", 0)

        logger.debug(f"/pipeline/continue evaluation: score={score}, outcome={outcome}")

        report["phases"]["assessment"] = {
            "status": "complete",
            "score": score,
            "outcome": outcome,
            "breakdown": submit_result.get("topic_breakdown", {})
        }

        if progress_callback:
            await progress_callback("phase_done", "Assessment Evaluation", 3, 5)

        # ADAPTATION: If FAIL → update plan
        if outcome == "FAIL":
            if progress_callback:
                await progress_callback(
                    "adaptation",
                    f"Assessment failed ({score:.1f}%) — updating study plan",
                    4, 5
                )

            mem = self.memory.to_dict()
            fail_adaptation = {
                "reason": f"Assessment score {score:.1f}% below threshold",
                "action": "Reinforced weak topics in study plan",
                "weak_topics": mem.get("weak_topics", []),
                "additional_hours": 5
            }
            mem = await self._adapt_learning_plan(mem, [fail_adaptation])
            self.memory.update(mem)
            report["adaptations"].append(fail_adaptation)

        # PHASE 4: Coaching
        if progress_callback:
            await progress_callback("phase_start", "Coaching", 4, 5)

        if outcome == "FAIL":
            coaching_result = await self.run_coaching_phase(learner_id)
            report["phases"]["coaching"] = {
                "status": "complete",
                "triggered": True,
                "misconceptions": coaching_result.get("misconceptions", []),
                "socratic_questions": coaching_result.get("socratic_questions", []),
                "remediation": coaching_result.get("remediation", {})
            }
        else:
            report["phases"]["coaching"] = {
                "status": "skipped",
                "triggered": False
            }

        if progress_callback:
            await progress_callback("phase_done", "Coaching", 4, 5)

        # PHASE 5: Reflection
        if progress_callback:
            await progress_callback("phase_start", "Reflection", 5, 5)

        reflection_result = await self.run_reflection_phase(learner_id, outcome)
        report["phases"]["reflection"] = {
            "status": "complete",
            "analysis": reflection_result.get("reflection", {}).get("analysis", ""),
            "updated_reputation": reflection_result.get("updated_reputation", [])
        }

        if progress_callback:
            await progress_callback("phase_done", "Reflection", 5, 5)

        # Build final consolidated report
        mem = self.memory.to_dict()
        report["final_verdict"] = mem.get("readiness_verdict", "")
        report["final_confidence"] = mem.get("readiness_confidence", 0)
        report["consolidated_plan"] = {
            "skill_map": mem.get("skill_map", []),
            "study_plan": mem.get("study_plan", {}),
            "weak_topics": mem.get("weak_topics", []),
            "total_adaptations": len(report["adaptations"]),
            "learning_resources": mem.get("learning_resources", {})
        }
        report["session_log"] = mem.get("session_log", [])
        report["status"] = "pipeline_complete"
        self.memory.update({"pipeline_state": "complete"})

        logger.debug(f"Pipeline continue complete. Status: {report['status']}")
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

        logger.debug(f"_check_council_discrepancies votes: {votes}")

        # Count verdicts - handle both nested formats
        verdicts = []
        for agent_name, vote_data in votes.items():
            verdict = vote_data.get("verdict") if isinstance(vote_data, dict) else None
            if verdict:
                verdicts.append(verdict)

        logger.debug(f"Extracted verdicts: {verdicts}")

        ready_count = sum(1 for v in verdicts if v == "READY")
        not_ready_count = sum(1 for v in verdicts if v == "NOT_READY")
        delay_count = sum(1 for v in verdicts if v == "DELAY")

        unique_verdicts = set(verdicts)
        logger.debug(f"Unique verdicts: {unique_verdicts}")

        has_split = (
            ("READY" in unique_verdicts and "NOT_READY" in unique_verdicts) or
            ("DELAY" in unique_verdicts and len(unique_verdicts) > 1)
        )

        if has_split and len(votes) > 1:
            logger.debug(f"Council split detected, generating adaptation")
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
        """Uses LLM to adapt the study plan based on findings."""
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
            # The prompt asks the LLM to flag modified weeks with "adapted": true;
            # it sometimes drops that flag at the plan ROOT instead of inside a
            # week. Keep only dict-valued week entries so a stray scalar can't
            # crash the renderer downstream.
            if isinstance(adapted_plan, dict):
                adapted_plan = {
                    week: entry for week, entry in adapted_plan.items()
                    if isinstance(entry, dict)
                }
            if adapted_plan:
                memory["study_plan"] = adapted_plan
                memory["plan_adapted"] = True
                memory["adaptations"] = adaptations
            else:
                memory["plan_adapted"] = False
        except Exception:
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

    async def run_adaptive_loop(
        self,
        learner_id: str,
        max_iterations: int = 3
    ) -> dict:
        """
        Runs assessment → diagnoses failure →
        regenerates path → repeat until ready or max attempts.

        Each iteration:
        1. Run assessment
        2. Get score and outcome
        3. If PASS → stop
        4. If FAIL → run Socratic coach, adapt learning plan, retry
        """
        self._bind(learner_id)

        iteration = 0
        history = []
        mem = self.memory.to_dict()

        while iteration < max_iterations:
            iteration += 1
            mem = self.memory.to_dict()

            print(
                f"[AdaptiveLoop] Iteration {iteration}/{max_iterations}"
            )

            # Run assessment
            assessment_result = await self.run_assessment_phase(learner_id)

            # Get answers — simulate based on current score
            questions = assessment_result.get("questions", [])
            practice_score = mem.get("practice_score_avg", 65)

            # Each iteration increases score slightly (learning effect)
            adjusted_score = min(
                practice_score + ((iteration - 1) * 8),
                95
            )

            simulated_answers = self._simulate_answers(
                questions,
                adjusted_score
            )

            result = await self.submit_assessment(
                learner_id, simulated_answers
            )

            score = result.get("score", 0)
            outcome = result.get("outcome", "FAIL")

            iteration_record = {
                "iteration": iteration,
                "score": score,
                "outcome": outcome,
                "weak_topics": mem.get("weak_topics", []),
                "changes_made": []
            }

            if outcome == "PASS":
                iteration_record["changes_made"].append(
                    "Assessment passed — no further adaptation needed"
                )
                history.append(iteration_record)
                break

            # FAIL: diagnose and adapt
            if self.socratic_coach is None:
                self.socratic_coach = SocraticCoach()

            mem = await self.socratic_coach.execute(
                self.memory.to_dict()
            )
            self.memory.update(mem)

            weak_topics = mem.get("weak_topics", [])

            if weak_topics:
                adaptation = await self._adapt_for_weak_topics(
                    mem, weak_topics, iteration
                )
                self.memory.update(adaptation)

                iteration_record["changes_made"].extend([
                    f"Focused study plan on: {', '.join(weak_topics[:3])}",
                    f"Added {2 * iteration} extra practice hours",
                    f"Reprioritised week structure"
                ])

            history.append(iteration_record)

        self.memory.update({"adaptive_history": history})

        return {
            "iterations": len(history),
            "final_outcome": history[-1]["outcome"] if history else "FAIL",
            "final_score": history[-1]["score"] if history else 0,
            "history": history,
            "study_plan": self.memory.to_dict().get(
                "study_plan", {}
            ),
            "weak_topics": self.memory.to_dict().get(
                "weak_topics", []
            )
        }

    async def _adapt_for_weak_topics(
        self,
        memory: dict,
        weak_topics: list,
        iteration: int
    ) -> dict:
        """Regenerates study plan focused on weak topics."""

        system_prompt = """
You are a learning plan optimizer.
A learner has failed their assessment.
Adapt their study plan to address specific weak areas.
Make the changes significant and targeted.
Return only valid JSON matching the original plan structure.
"""

        current_plan = json.dumps(
            memory.get("study_plan", {}),
            indent=2
        )[:2000]

        user_prompt = f"""
Iteration: {iteration} (previous attempts failed)
Weak topics that need fixing: {weak_topics}

Current study plan:
{current_plan}

Adapt this plan by:
1. Adding {iteration} extra hours per weak topic
2. Moving weak topics earlier in the schedule
3. Adding specific practice exercises for each weak topic
4. Including review checkpoints before the exam

For each week add an "adaptation_note" field explaining
what changed and why.

Return the complete adapted study plan JSON.
"""

        response = self._call_llm_sync(
            system_prompt, user_prompt
        )

        try:
            clean = response.strip()
            if "```" in clean:
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            clean = clean.strip()

            adapted = json.loads(clean)
            memory["study_plan"] = adapted
            memory["plan_adapted"] = True
            memory["adaptation_iteration"] = iteration

        except Exception as e:
            print(f"[AdaptiveLoop] JSON parse error: {e}")
            plan = memory.get("study_plan", {})
            for week in plan:
                if isinstance(plan[week], dict):
                    plan[week]["adaptation_note"] = (
                        f"Adapted in iteration {iteration}: "
                        f"Extra focus on {', '.join(weak_topics[:2])}"
                    )
            memory["study_plan"] = plan

        return memory
