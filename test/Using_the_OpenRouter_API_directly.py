import requests
import json
import os

response = requests.post(
  url="https://openrouter.ai/api/v1/chat/completions",
  headers={
    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
    "Content-Type": "application/json",
  },
  data=json.dumps({
    "model": "openai/gpt-4o",
    "messages": [
      {
        "role": "user",
        "content": "What is the meaning of life?"
      }
    ]
  })
)

print("-=== json output ===-")
print(response.json())

print("-=== answer output ===-")
data = response.json()
answer = data['choices'][0]['message']['content']
print(answer)