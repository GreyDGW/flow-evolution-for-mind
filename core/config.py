import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

def get_llm_config() -> dict:
    return {
        "api_key": os.getenv("LLM_API_KEY", ""),
        "base_url": os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1"),
        "model": os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-V3"),
        "timeout": int(os.getenv("LLM_TIMEOUT", "60"))
    }
