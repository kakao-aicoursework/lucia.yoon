import os
import aiohttp
import logging
import openai
import json
from dto import ChatbotRequest

#시스템 메세지 추가, 데이터베이스 연결, 랭체인 기본 함수 연결 , 

# 환경 변수 처리
openai.api_key = os.getenv('')

# 로깅 설정
logger = logging.getLogger("Callback")
logging.basicConfig(level=logging.INFO)

# 시스템 메시지 상수
SYSTEM_MSG = "당신은 카카오 서비스를 알려주는 싱크입니다."

# 데이터 파일 처리 클래스
class DataProcessor:
    def __init__(self, file_name):
        self.file_name = file_name

    def read_file(self):
        with open(self.file_name, "r", encoding="utf-8") as file:
            return file.read()

    def process_data(self, content):
        ids = []
        documents = []
        lines = content.split('\n')
        current_id = None
        current_document = []

        for line in lines:
            if line.startswith('#'):
                if current_id is not None:
                    ids.append(current_id)
                    documents.append('\n'.join(current_document))
                    current_document = []
                current_id = line.strip()
            else:
                current_document.append(line.strip())

        if current_id is not None:
            ids.append(current_id)
            documents.append('\n'.join(current_document))

        return ids, documents

# OpenAI 챗봇 클래스
class OpenAIChatbot:
    def __init__(self, gpt_model="gpt-3.5-turbo"):
        self.gpt_model = gpt_model

    async def send_message(self, message_log, temperature=0.1):
        try:
            response = openai.ChatCompletion.create(
                model=self.gpt_model,
                messages=message_log, 
                temperature=temperature,
            )
            message_log.append(
            [
            {"role": "system", "content": SYSTEM_MSG},
            #{"role": "user", "content": request.userRequest.utterance},
        ]
        ) 
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return "처리 중 오류가 발생했습니다."

# 메인 함수
async def callback_handler(request: ChatbotRequest) -> dict:
    file_name = "/Users/kakao/vs_code/llm_lucia/kakaochattest_guide/project_data_카카오싱크.txt"
    data_processor = DataProcessor(file_name)
    content = data_processor.read_file()
    ids, documents = data_processor.process_data(content)

    # #

    # HTTP 요청 처리
    async with aiohttp.ClientSession() as session:
        url = request.userRequest.callbackUrl
        if url:
            try:
                async with session.post(url=url, json={"key": "value"}, ssl=False) as resp:
                    return await resp.json()
            except Exception as e:
                logger.error(f"HTTP request error: {e}")
                return {"error": "HTTP 요청 중 오류 발생"}

# 기타 필요한 함수 및 클래스 구현
