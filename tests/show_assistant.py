import json

with open('tests/data/d7387af7-18c7-4825-937b-c7c209a5b080.jsonl', 'r') as f:
    for i, line in enumerate(f, 1):
        data = json.loads(line)
        if data.get('type') == 'message':
            msg = data.get('message', {})
            if msg.get('role') == 'assistant':
                print("=== assistant 消息结构 ===")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
                break
