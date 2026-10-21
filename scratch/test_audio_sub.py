import requests, base64, json

audio_data = open('D:/temp_scraper/test_ep3.mp3', 'rb').read()
b64_audio = base64.b64encode(audio_data).decode('utf-8')

url = 'http://localhost:20128/v1/chat/completions'
headers = {
    'Authorization': 'Bearer sk-6c5720214189ea51-otb97y-5446d478',
    'Content-Type': 'application/json'
}

prompt = """Transcribe the speech in this Chinese audio and translate it into Indonesian in WebVTT subtitle format.
Requirements:
1. Output ONLY valid WebVTT format starting with 'WEBVTT'.
2. Include ONLY the Indonesian translation text (do NOT include the Chinese text).
3. Ensure natural, fluent Indonesian translation matching drama conversation.
4. Output no markdown formatting (no ```vtt), just pure WebVTT text directly."""

payload = {
    'model': 'ag/gemini-3.8-flash-high',
    'stream': False,
    'messages': [
        {
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': prompt
                },
                {
                    'type': 'input_audio',
                    'input_audio': {
                        'data': b64_audio,
                        'format': 'mp3'
                    }
                }
            ]
        }
    ]
}

r = requests.post(url, headers=headers, json=payload, timeout=45)
res = r.json()
print("Status:", r.status_code)
print("Content:\n" + res['choices'][0]['message']['content'])
