import os
import json
import pickle
import openai
import numpy as np
import tkinter as tk
import pandas as pd
from tkinter import scrolledtext
import tkinter.filedialog as filedialog
from sklearn.feature_extraction.text import TfidfVectorizer


# OpenAI API Key 설정
openai.api_key = ""

# File open
file_name = "/Users/kakao/vs_code/llm_lucia/project_step1/project_data_카카오톡채널.txt"

with open(file_name, "r", encoding="utf-8") as file:
    content = file.read()
    

# 데이터 인덱스
ids = []
# 벡터로 변환 저장할 텍스트 데이터로 ChromaDB에 Embedding 데이터가 없으면 자동으로 벡터로 변환해서 저장
documents = []
# 줄 단위로 분할
lines = content.split('\n')
current_id = None
current_document = []

# 데이터 처리
for line in lines:
    # '#'으로 시작하면 id로 처리
    if line.startswith('#'):
        # 기존에 쌓인 내용을 처리하고 초기화
        if current_id is not None:
            ids.append(current_id)
            documents.append('\n'.join(current_document))
            current_document = []
        current_id = line.strip()
    # '#'이 아니면 document에 추가
    else:
        current_document.append(line.strip())
        
# 마지막 데이터 처리
if current_id is not None:
    ids.append(current_id)
    documents.append('\n'.join(current_document))

# 결과 확인
for i in range(len(ids)):
    print(f"ID: {ids[i]}\nDocument:\n{documents[i]}\n{'='*50}\n")
    

# vectorDB
import chromadb

client = chromadb.PersistentClient()

collection = client.get_or_create_collection(
    name="kakao_chatbot",
    #metadata={"hnsw:space": "cosine"}# l2 is the default, metadata:유사도를 무엇으로 만드는지 설정하는 것, l2가 디폴트
)

# DB 저장
collection.add(
    documents=documents,
    ids=ids
)

# DB 쿼리
collection.query(
    query_texts=["기능 소개"],
    n_results=5,
)

import tkinter as tk
from tkinter import scrolledtext
import openai
import json


def save_to_collection(data):
    try:
        # 여기에서 collection을 사용하여 데이터 저장
        collection.insert_one(data)
        print("Data saved to the collection successfully.")
    except Exception as e:
        print(f"Error saving data to the collection: {e}")

def send_message(message_log, gpt_model="gpt-3.5-turbo", temperature=0.1):
    try:
        response = openai.ChatCompletion.create(
            model=gpt_model,
            messages=message_log,
            temperature=temperature,
        )

        response_message = response["choices"][0]["message"]

        if response_message.get("function_call"):
            available_functions = {
                "save_to_collection": save_to_collection,
            }
            function_name = response_message["function_call"]["name"]

            if function_name == "save_to_collection":
                data_to_save = response_message["function_call"]["arguments"]
                save_to_collection(data_to_save)

            message_log.append(response_message)
            message_log.append(
                {
                    "role": "function",
                    "name": function_name,
                    "content": "Function executed successfully.",
                }
            )

            response = openai.ChatCompletion.create(
                model=gpt_model,
                messages=message_log,
                temperature=temperature,
            )

        return response.choices[0].message.content
    except Exception as e:
        print(f"Error: {e}")

def main():
    def show_popup_message(window, message):
        popup = tk.Toplevel(window)
        popup.title("")

        # 팝업 창의 내용
        label = tk.Label(popup, text=message, font=("맑은 고딕", 12))
        label.pack(expand=True, fill=tk.BOTH)

        # 팝업 창의 크기 조절하기
        window.update_idletasks()
        popup_width = label.winfo_reqwidth() + 20
        popup_height = label.winfo_reqheight() + 20
        popup.geometry(f"{popup_width}x{popup_height}")

        # 팝업 창의 중앙에 위치하기
        window_x = window.winfo_x()
        window_y = window.winfo_y()
        window_width = window.winfo_width()
        window_height = window.winfo_height()

        popup_x = window_x + window_width // 2 - popup_width // 2
        popup_y = window_y + window_height // 2 - popup_height // 2
        popup.geometry(f"+{popup_x}+{popup_y}")

        popup.transient(window)
        popup.attributes('-topmost', True)

        popup.update()
        return popup
    
    def on_send():
        user_input = user_entry.get()
        user_entry.delete(0, tk.END)

        if user_input.lower() == "quit":
            window.destroy()
            return

        message_log.append({"role": "user", "content": user_input})
        conversation.config(state=tk.NORMAL)
        conversation.insert(tk.END, f"You: {user_input}\n", "user")
        thinking_popup = show_popup_message(window, "처리중...")
        window.update_idletasks()
        response = send_message(message_log)
        thinking_popup.destroy()

        message_log.append({"role": "assistant", "content": response})

        conversation.insert(tk.END, f"ai assistant: {response}\n", "assistant")
        conversation.config(state=tk.DISABLED)
        conversation.see(tk.END)

    window = tk.Tk()
    window.title("GPT AI")

    font = ("맑은 고딕", 10)

    conversation = scrolledtext.ScrolledText(window, wrap=tk.WORD, bg='#f0f0f0', font=font)
    conversation.tag_configure("user", background="#c9daf8")
    conversation.tag_configure("assistant", background="#e4e4e4")
    conversation.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    input_frame = tk.Frame(window)
    input_frame.pack(fill=tk.X, padx=10, pady=10)

    user_entry = tk.Entry(input_frame)
    user_entry.pack(fill=tk.X, side=tk.LEFT, expand=True)

    send_button = tk.Button(input_frame, text="Send", command=on_send)
    send_button.pack(side=tk.RIGHT)

    window.bind('<Return>', lambda event: on_send())

    system_message = '''
        "저는 카카오 서비스 챗봇입니다."
    '''
    message_log = [{"role": "system", "content": system_message}]
    conversation.insert(tk.END, f"ai assistant: {system_message}\n", "assistant")

    window.mainloop()

if __name__ == "__main__":
    collection = client.get_or_create_collection(
        name="kakao_chatbot",
        #metadata={"hnsw:space": "cosine"}# l2 is the default, metadata:유사도를 무엇으로 만드는지 설정하는 것, l2가 디폴트
    )
    main()