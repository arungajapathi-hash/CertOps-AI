"""AssessmentAgent - Generates mock exam questions and evaluates answers."""
import json
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

        # Step 1: Get certification guide
        try:
            guide = self.knowledge.get_certification_guide(certification)
            content = guide.get("content", "") if isinstance(guide, dict) else str(guide)
        except Exception as e:
            self._log(f"Error fetching guide: {e}")
            content = f"General {certification} exam content"

        # Step 2: Generate questions via LLM
        system_prompt = (
            "You are a senior Microsoft certification item writer. "
            "Generate realistic certification-style practice questions grounded in the provided exam content. "
            "Use scenario-based stems that test applied judgement, trade-offs, constraints, and best next actions. "
            "Avoid placeholder wording such as 'sample question', 'option A', or obvious answers. "
            "Each question must have exactly four plausible options, one correct answer, a concise explanation, "
            "and a source citation. Return only valid JSON with double-quoted keys and strings."
        )

        domain_instructions = ""
        if exam_domains:
            domain_lines = []
            for domain in exam_domains:
                name = domain.get("domain", "General")
                weight = domain.get("weight_percent", 0)
                count = max(1, round(question_count * weight / 100))
                key_topics = domain.get("key_topics", [])
                topic_line = f"- {name}: approx. {count} questions ({weight}% weight)"
                if key_topics:
                    topic_line += f" covering {', '.join(key_topics[:3])}"
                domain_lines.append(topic_line)
            domain_instructions = "Domain allocation:\n" + "\n".join(domain_lines) + "\n\n"

        user_prompt = (
            f"Generate {question_count} certification-style practice questions for {certification}.\n\n"
            f"Certification content:\n{content[:2000]}\n\n"
            f"{domain_instructions}"
            f"Focus these weak topics heavily (60% of questions):\n{weak_topics}\n\n"
            f"Also cover these skills (40% of questions):\n{skill_map[:5] if skill_map else ['General certification topics']}\n\n"
            f"Question quality requirements:\n"
            f"- Use realistic workplace scenarios and constraints.\n"
            f"- Include command/configuration/architecture choices where relevant.\n"
            f"- Make distractors plausible but clearly wrong for a specific reason.\n"
            f"- Do not mention that these are sample questions.\n"
            f"- Do not use generic option text.\n\n"
            f"Return JSON:\n"
            f"{{\n"
            f"  \"questions\": [\n"
            f"    {{\n"
            f"      \"id\": 1,\n"
            f"      \"topic\": \"domain or topic name\",\n"
            f"      \"question\": \"scenario question text\",\n"
            f"      \"options\": {{\n"
            f"        \"A\": \"plausible option text\",\n"
            f"        \"B\": \"plausible option text\",\n"
            f"        \"C\": \"plausible option text\",\n"
            f"        \"D\": \"plausible option text\"\n"
            f"      }},\n"
            f"      \"correct_answer\": \"A\",\n"
            f"      \"explanation\": \"why this option is correct and why the closest distractor is not\",\n"
            f"      \"source\": \"exam guide section citation\"\n"
            f"    }}\n"
            f"  ]\n"
            f"}}"
        )

        response = self._call_llm(system_prompt, user_prompt, temperature=0.7)

        # Step 3: Parse questions
        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            clean = clean.strip()

            result = json.loads(clean)
            questions = self._normalize_questions(
                result.get("questions", []),
                certification,
                weak_topics,
                skill_map,
                question_count,
                exam_domains,
            )

            if len(questions) < question_count:
                questions = self._generate_fallback_questions(
                    certification,
                    weak_topics,
                    skill_map,
                    question_count,
                    exam_domains,
                    existing_questions=questions
                )

            memory["assessment_questions"] = questions
            self._append_log(memory, f"AssessmentAgent: Generated {len(questions)} questions for {certification}")

        except json.JSONDecodeError as e:
            self._log(f"JSON parse error: {e}")
            questions = self._generate_fallback_questions(
                certification,
                weak_topics,
                skill_map,
                question_count,
                exam_domains,
            )
            memory["assessment_questions"] = questions
            self._append_log(memory, f"AssessmentAgent: Using fallback questions ({len(questions)})")

        return memory

    def _normalize_questions(
        self,
        questions: List[Dict[str, Any]],
        certification: str,
        weak_topics: List[str],
        skill_map: List[str],
        question_count: int,
        exam_domains: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Keep generated items exam-like and replace weak/placeholder items."""
        valid_questions = []
        for i, question in enumerate(questions[:question_count], start=1):
            if not isinstance(question, dict) or self._looks_placeholder(question):
                continue

            options = question.get("options", {})
            if not isinstance(options, dict) or set(options.keys()) != {"A", "B", "C", "D"}:
                continue

            correct = str(question.get("correct_answer", "")).upper()
            if correct not in options:
                continue

            question["id"] = i
            question["correct_answer"] = correct
            question["topic"] = question.get("topic") or self._topic_for_index(
                i - 1,
                certification,
                weak_topics,
                skill_map,
                exam_domains,
            )
            question["source"] = question.get("source") or f"{certification} exam skills outline"
            valid_questions.append(question)

        if len(valid_questions) < question_count:
            fallback = self._generate_fallback_questions(
                certification,
                weak_topics,
                skill_map,
                question_count,
                exam_domains,
                existing_questions=valid_questions,
            )
            used = {q.get("question") for q in valid_questions}
            for question in fallback:
                if question.get("question") not in used:
                    question["id"] = len(valid_questions) + 1
                    valid_questions.append(question)
                if len(valid_questions) == question_count:
                    break

        return valid_questions

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

