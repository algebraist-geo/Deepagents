from langchain_deepseek import ChatDeepSeek
import os
from dotenv import load_dotenv
load_dotenv()
llm=ChatDeepSeek(
            model="deepseek-v4-pro",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            api_key=os.environ.get('deepseek_api'),
)
