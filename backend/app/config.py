import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 这里加上了 ": str" 让 PyCharm 认识，防止报红线
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-chat")