import sys
import json
sys.path.insert(0, 'c:/GitHub/telegram-news-aggregator/src')
from agent.mcp_client import MCPClient
mcp = MCPClient()
dialogs = mcp.get_dialogs()
print('Chats disponibles:')
if isinstance(dialogs, dict) and 'content' in dialogs:
    for item in dialogs['content']:
        if item.get('type') == 'text' and 'text' in item:
            try:
                data = json.loads(item['text'])
                if 'dialogs' in data:
                    for d in data['dialogs']:
                        dialog_id = d.get('name', d.get('title', 'unknown'))
                        title = d.get('title', 'unknown')
                        dialog_type = d.get('type', 'unknown')
                        print(f'  ID: {dialog_id}, Name: {title}, Type: {dialog_type}')
            except json.JSONDecodeError as e:
                print(f'Error parseando JSON: {e}')
else:
    print(f'Formato inesperado: {dialogs}')