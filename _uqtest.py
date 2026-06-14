import asyncio
from dotenv import load_dotenv; load_dotenv('.env')
from backend.agents.assessment_agent import AssessmentAgent

a = AssessmentAgent()


async def go():
    guide = a.knowledge.get_certification_guide('AZ-204')
    content = guide.get('content', '')
    bank = await a._build_bank(
        'AZ-204', content, 10, ['Develop Azure compute solutions'],
        [], citations=guide.get('citations', []), source=guide.get('source'),
    )
    stems = [q['question'] for q in bank]
    print('generated:', len(bank), '| unique:', len(set(stems)),
          '| grounded_in:', bank[0].get('grounded_in') if bank else None)
    for s in stems[:4]:
        print(' -', s[:70])


asyncio.run(go())
