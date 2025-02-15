import requests
import json

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2ZDRlZjI1LWI3ZmEtNGJiMi1hOGNmLTljMTc4NjJmMzA2NyJ9.4ZJiW_cJgETFboUCsnBKcq8i-zHm6peoigl16rkdi_Q"

headers = { 'Authorization': f'Bearer {TOKEN}', 'Accept': 'application/json' }
params = { 'model': 'qwen:0.5b', 'messages': [{'role': 'user', 'content': 'add punctuation: 沒有的話我們看第三個就是健康'}]}
  
response = requests.post("http://192.168.1.31:3000/api/chat/completions", headers=headers, json=params)

with open("message_output.json", "w") as f:
    json.dump(response.json(), f, indent=4)


print(response.json()['choices'][0]['message']['content'])