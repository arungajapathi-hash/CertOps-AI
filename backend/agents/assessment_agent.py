"""AssessmentAgent - Generates mock exam questions and evaluates answers."""
import json
import random
from typing import Dict, List, Any

from backend.agents.base_agent import BaseAgent
from backend.plugins.knowledge_router import get_knowledge_plugin
from backend import database

EXAM_PROFILES = {
    "AZ-900": {"count": 40, "duration": 45},
    "AZ-204": {"count": 50, "duration": 60},
    "AZ-400": {"count": 60, "duration": 90},
}


class AssessmentAgent(BaseAgent):
    def __init__(self):
        super().__init__("AssessmentAgent")
        self.knowledge = get_knowledge_plugin()

    async def execute(self, memory: Dict) -> Dict:
        """Generate assessment questions based on certification and weak topics."""
        self._log("Generating assessment questions...")

        certification = memory.get("certification", "Unknown")
        weak_topics = memory.get("weak_topics", [])
        skill_map = memory.get("skill_map", [])
        exam_domains = memory.get("exam_domains", []) or []

        profile = EXAM_PROFILES.get(certification, {"count": 40, "duration": 45})
        question_count = profile["count"]
        timer_minutes = profile["duration"]
        memory["assessment_question_count"] = question_count
        memory["assessment_timer_minutes"] = timer_minutes

        # Build a fresh, Foundry-IQ-grounded question set on every exam — no
        # disk cache, so a retake always gets newly generated questions.
        try:
            guide = self.knowledge.get_certification_guide(certification)
            content = guide.get("content", "") if isinstance(guide, dict) else str(guide)
        except Exception as e:
            self._log(f"Error fetching guide: {e}")
            content = f"General {certification} exam content"

        citations = guide.get("citations", []) if isinstance(guide, dict) else []
        source = guide.get("source", "Foundry IQ") if isinstance(guide, dict) else "Foundry IQ"
        generated = await self._build_bank(
            certification, content, question_count, skill_map, exam_domains,
            citations=citations, source=source,
        )

        if generated:
            sampled = self._sample_from_bank(generated, question_count, weak_topics, exam_domains)
            if len(sampled) < question_count:
                sampled = self._generate_fallback_questions(
                    certification, weak_topics, skill_map, question_count,
                    exam_domains, existing_questions=sampled,
                )
            memory["assessment_questions"] = sampled[:question_count]
            memory["assessment_source"] = "foundry_generated"
            self._append_log(
                memory,
                f"AssessmentAgent: Built {len(generated)} Foundry-grounded questions for {certification}",
            )
        else:
            # Generation failed entirely — fall back to templates so the exam
            # still runs (rare; only when the LLM is unreachable).
            memory["assessment_questions"] = self._generate_fallback_questions(
                certification, weak_topics, skill_map, question_count, exam_domains,
            )
            memory["assessment_source"] = "template_fallback"
            self._append_log(memory, f"AssessmentAgent: Using template fallback for {certification}")

        return memory

    async def _build_bank(
        self,
        certification: str,
        content: str,
        question_count: int,
        skill_map: List[str],
        exam_domains: List[Dict[str, Any]],
        citations: List[str] = None,
        source: str = "Foundry IQ",
    ) -> List[Dict[str, Any]]:
        """Generate a fresh question set in small batches (not persisted).

        Each domain's batch is grounded on Foundry IQ retrieval (per-topic
        search), so questions cite the same knowledge base used elsewhere in
        the app. Batching keeps each LLM response small enough that it never
        truncates (the root cause of the old repeating-question bug).
        """
        citations = citations or []
        target = int(question_count * 1.3) + 4
        domain_names = [d.get("domain") for d in exam_domains if d.get("domain")]
        if not domain_names:
            domain_names = (skill_map[:5] if skill_map else [f"{certification} core skills"])

        bank: List[Dict[str, Any]] = []
        seen = set()
        batch_size = 8
        di = 0
        stalls = 0
        while len(bank) < target and stalls < 3:
            domain = domain_names[di % len(domain_names)]
            di += 1
            before = len(bank)
            # Pull Foundry IQ context specific to this domain when available,
            # otherwise fall back to the overall guide content.
            domain_context = content
            search = getattr(self.knowledge, "search_topics", None)
            if callable(search):
                try:
                    retrieved = search(certification, domain)
                    if retrieved and len(str(retrieved)) > 80:
                        domain_context = str(retrieved)
                except Exception:
                    domain_context = content
            batch = await self._gen_question_batch(
                certification, domain, batch_size, domain_context,
                [q["question"] for q in bank],
                citations=citations, source=source,
            )
            for q in batch:
                stem = q.get("question", "").strip().lower()
                if stem and stem not in seen:
                    seen.add(stem)
                    bank.append(q)
                    if len(bank) >= target:
                        break
            stalls = stalls + 1 if len(bank) == before else 0

        if bank:
            for i, q in enumerate(bank, start=1):
                q["id"] = i
        return bank

    async def _gen_question_batch(
        self, certification: str, domain: str, n: int, content: str, avoid: List[str],
        citations: List[str] = None, source: str = "Foundry IQ",
    ) -> List[Dict[str, Any]]:
        """Generate a small batch of validated questions for one domain,
        grounded on the supplied Foundry IQ context."""
        citations = citations or []
        default_source = citations[0] if citations else source
        system = (
            "You are a senior certification item writer. Produce realistic, "
            "scenario-based multiple-choice questions grounded ONLY in the "
            "provided exam content. Return ONLY valid JSON."
        )
        avoid_txt = ""
        if avoid:
            avoid_txt = "\nDo NOT repeat or paraphrase these existing stems:\n" + "; ".join(avoid[-12:]) + "\n"
        user = (
            f"Write {n} distinct {certification} exam questions for the domain '{domain}'.\n"
            f"Exam content:\n{content[:1500]}\n{avoid_txt}\n"
            "Each item needs a scenario stem, exactly four plausible options (A-D), "
            "one correct answer, a one-sentence explanation, and a short source label.\n"
            'Return JSON: {"questions":[{"topic":"' + domain + '","question":"...",'
            '"options":{"A":"...","B":"...","C":"...","D":"..."},'
            '"correct_answer":"A","explanation":"...","source":"..."}]}'
        )
        raw = await self._call_llm_async(system, user, temperature=0.8, max_tokens=2200)
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        try:
            items = json.loads(clean.strip()).get("questions", [])
        except Exception:
            return []
        out = []
        for q in items:
            if not isinstance(q, dict) or self._looks_placeholder(q):
                continue
            opts = q.get("options", {})
            if not isinstance(opts, dict) or set(opts.keys()) != {"A", "B", "C", "D"}:
                continue
            if str(q.get("correct_answer", "")).upper() not in opts:
                continue
            q["correct_answer"] = str(q["correct_answer"]).upper()
            q["topic"] = q.get("topic") or domain
            q["source"] = q.get("source") or default_source
            q["grounded_in"] = source
            out.append(q)
        return out

    def _looks_placeholder(self, question: Dict[str, Any]) -> bool:
        text = " ".join([
            str(question.get("question", "")),
            " ".join(str(v) for v in question.get("options", {}).values())
            if isinstance(question.get("options"), dict) else "",
        ]).lower()
        placeholder_terms = [
            "sample question",
            "option a",
            "option b",
            "option c",
            "option d",
            "question text",
            "topic name",
        ]
        return any(term in text for term in placeholder_terms)

    def _topic_for_index(
        self,
        index: int,
        certification: str,
        weak_topics: List[str],
        skill_map: List[str],
        exam_domains: List[Dict[str, Any]] = None,
    ) -> str:
        exam_domains = exam_domains or []
        domain_names = [d.get("domain") for d in exam_domains if d.get("domain")]
        if domain_names:
            return domain_names[index % len(domain_names)]
        topics = [t for t in (weak_topics + skill_map) if t]
        return topics[index % len(topics)] if topics else f"{certification} readiness"

    def _sample_from_bank(
        self,
        bank: List[Dict[str, Any]],
        count: int,
        weak_topics: List[str],
        exam_domains: List[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Sample `count` unique questions, biased toward weak topics (~60%).

        Returns freshly numbered, validated question dicts. Never repeats an
        item within a single exam.
        """
        valid = []
        for q in bank:
            options = q.get("options", {})
            if not isinstance(options, dict) or set(options.keys()) != {"A", "B", "C", "D"}:
                continue
            if str(q.get("correct_answer", "")).upper() not in options:
                continue
            valid.append(q)
        if not valid:
            return []

        weak_lower = {str(t).lower() for t in (weak_topics or []) if t}
        weak_q, other_q = [], []
        for q in valid:
            topic = str(q.get("topic", "")).lower()
            (weak_q if weak_lower and any(w in topic for w in weak_lower) else other_q).append(q)

        random.shuffle(weak_q)
        random.shuffle(other_q)

        target_weak = min(len(weak_q), int(round(count * 0.6)))
        chosen = weak_q[:target_weak] + other_q + weak_q[target_weak:]
        chosen = chosen[:count]
        random.shuffle(chosen)

        result = []
        for i, q in enumerate(chosen, start=1):
            nq = dict(q)
            nq["id"] = i
            nq["correct_answer"] = str(q.get("correct_answer", "A")).upper()
            nq["topic"] = q.get("topic") or "General"
            nq["source"] = q.get("source") or f"Curated {self.name} bank"
            result.append(nq)
        return result

    async def evaluate(self, memory: Dict, answers: Dict) -> Dict:
        """Evaluate submitted answers and calculate scores."""
        self._log("Evaluating assessment answers...")

        questions = memory.get("assessment_questions", [])
        if not questions:
            self._log("No questions found in memory")
            memory["assessment_score"] = 0
            memory["assessment_outcome"] = "FAIL"
            return memory

        # Step 1: Score answers
        correct = 0
        topic_scores = {}
        wrong_questions = []

        for q in questions:
            q_id = str(q.get("id", ""))
            correct_answer = q.get("correct_answer", "")
            user_answer = answers.get(q_id, "").upper()
            is_correct = user_answer == correct_answer.upper()

            if is_correct:
                correct += 1
            else:
                wrong_questions.append(q)

            topic = q.get("topic", "General")
            if topic not in topic_scores:
                topic_scores[topic] = {"correct": 0, "total": 0}
            topic_scores[topic]["total"] += 1
            if is_correct:
                topic_scores[topic]["correct"] += 1

        # Step 2: Calculate scores
        overall_score = (correct / len(questions)) * 100 if questions else 0

        topic_breakdown = {}
        for topic, scores in topic_scores.items():
            topic_breakdown[topic] = {
                "score": (scores["correct"] / scores["total"]) * 100 if scores["total"] > 0 else 0,
                "correct": scores["correct"],
                "total": scores["total"]
            }

        outcome = "PASS" if overall_score >= 70 else "FAIL"

        # Step 3: Identify new weak topics from wrong answers
        new_weak = [
            t for t, s in topic_breakdown.items()
            if s["score"] < 60
        ]
        memory["weak_topics"] = list(set(
            memory.get("weak_topics", []) + new_weak
        ))

        # Step 4: Update memory
        memory["assessment_score"] = overall_score
        memory["assessment_breakdown"] = topic_breakdown
        memory["assessment_outcome"] = outcome
        memory["wrong_questions"] = wrong_questions
        memory["last_answers"] = answers

        # Step 5: Save to SQLite
        try:
            conn = database.get_connection()
            cursor = conn.cursor()

            learner_id = memory.get("learner_id", "unknown")
            certification = memory.get("certification", "unknown")

            cursor.execute("""
                INSERT INTO assessment_results (learner_id, certification, score, topic_breakdown, outcome)
                VALUES (?, ?, ?, ?, ?)
            """, (
                learner_id,
                certification,
                overall_score,
                json.dumps(topic_breakdown),
                outcome
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            self._log(f"Error saving assessment result: {e}")

        self._append_log(
            memory,
            f"AssessmentAgent: Score {overall_score:.1f}% — {outcome}"
        )

        return memory

    def _generate_fallback_questions(
        self,
        certification: str,
        weak_topics: List[str],
        skill_map: List[str] = None,
        question_count: int = 10,
        exam_domains: List[Dict[str, Any]] = None,
        existing_questions: List[Dict[str, Any]] = None,
    ) -> List[Dict]:
        """Generate exam-like fallback questions when LLM output is unavailable."""
        questions = existing_questions[:] if existing_questions else []
        skill_map = skill_map or []
        exam_domains = exam_domains or []
        domain_names = [d.get("domain") for d in exam_domains if d.get("domain")]
        topics = [t for t in (weak_topics + skill_map) if t] or [
            "identity and access",
            "monitoring and diagnostics",
            "security and compliance",
            "deployment and operations",
            "data protection and reliability",
        ]

        templates = [
            {
                "question": (
                    "A team is preparing a production workload for {certification}. During review, "
                    "you find that {topic} is the weakest area and the release date cannot move. "
                    "What should you do first to reduce certification and implementation risk?"
                ),
                "options": {
                    "A": "Map the weak area to the official skills outline, run targeted labs, and verify the result with scenario questions.",
                    "B": "Skip the weak area and focus only on topics where the learner already scores highly.",
                    "C": "Memorize service names without practicing configuration or troubleshooting decisions.",
                    "D": "Delay all study activity until the final week so the material is fresh."
                },
                "correct_answer": "A",
                "explanation": "Targeted practice against the official objective is the fastest way to close a known readiness gap; the other options avoid applied validation."
            },
            {
                "question": (
                    "You need to choose the best study activity for a learner who understands the definition of {topic} "
                    "but misses questions that include constraints, failures, or trade-offs. Which activity is most appropriate?"
                ),
                "options": {
                    "A": "Read a glossary of related terms for twenty minutes.",
                    "B": "Work through scenario labs and explain why each distractor would fail in the given constraints.",
                    "C": "Watch unrelated overview videos without checking comprehension.",
                    "D": "Remove {topic} from the plan because conceptual knowledge is already present."
                },
                "correct_answer": "B",
                "explanation": "Certification exams usually test applied judgement, so scenario labs plus distractor analysis close the gap better than passive review."
            },
            {
                "question": (
                    "A practice test shows repeated misses in {topic}. The learner has limited time before the {certification} exam. "
                    "Which planning change best aligns with real exam preparation?"
                ),
                "options": {
                    "A": "Add focused review blocks, hands-on practice, and a checkpoint score for the affected objective.",
                    "B": "Keep the original plan unchanged because the average score is the only metric that matters.",
                    "C": "Replace all remaining study time with broad product announcements.",
                    "D": "Only review questions that were answered correctly to build confidence."
                },
                "correct_answer": "A",
                "explanation": "A weak objective should change the plan with focused practice and measurable checkpoints, not broad or confidence-only review."
            },
            {
                "question": (
                    "During a readiness review for {certification}, two answer choices both appear valid for {topic}. "
                    "What is the best way to decide between them on the exam?"
                ),
                "options": {
                    "A": "Select the newest service even if it does not meet the scenario constraints.",
                    "B": "Choose the option that satisfies every stated requirement with the least unnecessary scope.",
                    "C": "Choose the longest answer because it usually contains more detail.",
                    "D": "Ignore cost, security, and operational constraints unless they are in the question title."
                },
                "correct_answer": "B",
                "explanation": "Microsoft exam items reward the answer that fits all explicit constraints; attractive options often fail one requirement."
            },
            {
                "question": (
                    "A learner can explain {topic}, but their answers change when wording includes 'minimum effort', "
                    "'least privilege', or 'highest availability'. What should the coaching feedback emphasize?"
                ),
                "options": {
                    "A": "Identify qualifier words first, then eliminate options that violate the key constraint.",
                    "B": "Ignore qualifiers because they are usually decorative text.",
                    "C": "Pick the option that uses the most familiar Azure service name.",
                    "D": "Answer from personal preference rather than the scenario requirements."
                },
                "correct_answer": "A",
                "explanation": "Qualifiers often define the correct trade-off; spotting them prevents plausible but over-scoped choices."
            },
        ]

        while len(questions) < question_count:
            i = len(questions)
            topic = domain_names[i % len(domain_names)] if domain_names else topics[i % len(topics)]
            template = templates[i % len(templates)]
            options = {
                key: value.format(topic=topic, certification=certification)
                for key, value in template["options"].items()
            }
            questions.append({
                "id": len(questions) + 1,
                "topic": topic,
                "question": template["question"].format(topic=topic, certification=certification),
                "options": options,
                "correct_answer": template["correct_answer"],
                "explanation": template["explanation"],
                "source": f"{certification} exam skills outline - {topic}"
            })

        return questions

