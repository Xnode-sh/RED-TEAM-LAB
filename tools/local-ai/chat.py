#!/usr/bin/env python3
"""Streaming terminal chat; no tools, execution, or history written to disk."""
import json
import readline
import sys
import urllib.request
from launch import ROOT, URL, ensure

def main():
    model_name = json.loads((ROOT/'active-model.json').read_text())['name']
    print(f"\033[1;31mRED TEAM LAB · {model_name}\033[0m")
    print("Загружаю модель…", flush=True)
    ensure()
    print("/new — новый диалог · /paste — много строк · /tokens N — длина ответа")
    print("/exit — выйти · Ctrl+C — прервать ответ")
    max_tokens = 512
    messages = [{"role": "system", "content": (ROOT/'system-prompt.txt').read_text().strip()}]
    while True:
        try:
            prompt = input("\n\033[1;36mТы › \033[0m").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if prompt in ('/exit', '/quit'):
            return
        if prompt == '/paste':
            print("Вставь код или задачу. Отдельная строка /end завершает ввод.")
            lines = []
            try:
                while True:
                    line = input()
                    if line == '/end':
                        break
                    lines.append(line)
            except (EOFError, KeyboardInterrupt):
                print("Ввод отменён.")
                continue
            prompt = '\n'.join(lines)
        if prompt.startswith('/tokens '):
            try:
                value = int(prompt.split()[1])
                if not 64 <= value <= 2048:
                    raise ValueError
                max_tokens = value
                print(f"Предел ответа: {max_tokens} токенов.")
            except (ValueError, IndexError):
                print("Использование: /tokens 64…2048")
            continue
        if prompt == '/new':
            messages = messages[:1]
            print("Диалог очищен.")
            continue
        if not prompt:
            continue
        if len(messages) > 13:
            messages = [messages[0]] + messages[-12:]
        messages.append({"role": "user", "content": prompt})
        data = json.dumps({"model": "rig-local", "messages": messages,
                           "stream": True, "max_tokens": max_tokens, "temperature": 0.2,
                           "top_p": 0.8, "top_k": 20, "min_p": 0,
                           "chat_template_kwargs": {"enable_thinking": False}}).encode()
        request = urllib.request.Request(URL+'/v1/chat/completions', data=data,
                                          headers={"Content-Type": "application/json"})
        answer = ''
        truncated = False
        print("\033[1;31mAI › \033[0m", end='', flush=True)
        try:
            with urllib.request.urlopen(request, timeout=240) as response:
                for line in response:
                    if not line.startswith(b'data: '):
                        continue
                    chunk = line[6:].strip()
                    if chunk == b'[DONE]':
                        break
                    choices = json.loads(chunk).get('choices', [])
                    if choices and choices[0].get('finish_reason') == 'length':
                        truncated = True
                    token = choices[0].get('delta', {}).get('content', '') if choices else ''
                    if token:
                        answer += token
                        # Prevent model output from injecting terminal control sequences.
                        print(''.join(c for c in token if c in '\n\t' or c.isprintable()), end='', flush=True)
        except KeyboardInterrupt:
            print("\n[Ответ прерван]")
        except (OSError, ValueError) as error:
            print("\nОшибка:", error)
        print()
        if truncated:
            print('[Достигнут предел ответа. /tokens 1024 — увеличить для следующего запроса]')
        if answer:
            messages.append({"role": "assistant", "content": answer})
        else:
            messages.pop()

if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError) as error:
        print("Ошибка запуска:", error, file=sys.stderr)
        input("Enter — закрыть вкладку")
        sys.exit(1)
