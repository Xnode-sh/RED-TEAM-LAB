#!/usr/bin/env python3
"""Publish only the operator-authorized prepared post 005; avoid duplicate sends."""
import hashlib
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request
import uuid
root = Path(__file__).resolve().parent.parent/'content/telegram'
receipt = root/'005-receipt.json'
if receipt.exists():
    print('Already published:', json.loads(receipt.read_text())['url'])
    sys.exit(0)
config = json.loads((Path.home()/'.config/red-team-lab/telegram.json').read_text())
if str(config['channel_id']) != '-1004446642270':
    sys.exit('Unexpected destination; nothing sent.')
caption = (root/'005-local-lab-draft.md').read_text().split('## Текст\n\n',1)[1].strip()
if len(caption.encode('utf-16-le'))//2 > 1024:
    sys.exit('Caption is too long; nothing sent.')
photo = (root/'005-local-lab.png').read_bytes()
boundary = 'rig-'+uuid.uuid4().hex
parts = []
for key, value in {'chat_id':str(config['channel_id']), 'caption':caption}.items():
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="photo"; filename="005-local-lab.png"\r\nContent-Type: image/png\r\n\r\n'.encode()+photo+b'\r\n')
parts.append(f'--{boundary}--\r\n'.encode())
request = urllib.request.Request('https://api.telegram.org/bot'+config['bot_token']+'/sendPhoto',
    data=b''.join(parts), headers={'Content-Type':'multipart/form-data; boundary='+boundary})
try:
    with urllib.request.urlopen(request, timeout=45) as response:
        result=json.load(response)
except urllib.error.HTTPError as error:
    sys.exit('Telegram HTTP error '+str(error.code)+'; no automatic retry.')
except (OSError, ValueError):
    sys.exit('No confirmed response; check channel before retrying to avoid duplicates.')
if not result.get('ok'):
    sys.exit('Telegram rejected request; error code '+str(result.get('error_code')))
message=result['result']
if str(message['chat']['id']) != str(config['channel_id']) or not message.get('photo'):
    sys.exit('Unexpected confirmation; check channel before retrying.')
record={'message_id':message['message_id'], 'chat_id':message['chat']['id'],
        'date':message['date'], 'url':'https://t.me/red_team_lab/'+str(message['message_id']),
        'caption_sha256':hashlib.sha256(caption.encode()).hexdigest(),
        'image_sha256':hashlib.sha256(photo).hexdigest()}
receipt.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print('Published and confirmed:',record['url'])
