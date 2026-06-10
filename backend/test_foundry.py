from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    base_url="https://certops-ai-resource.services.ai.azure.com/openai/v1/",
    api_key=os.getenv("AZURE_OPENAI_API_KEY")
)

response = client.chat.completions.create(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    messages=[
        {
            "role": "user",
            "content": "Say hello from CertOps AI"
        }
    ]
)

print(response.choices[0].message.content)