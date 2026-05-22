import os
import time
import requests
from typing import Optional
from pathlib import Path
from abc import ABC, abstractmethod


def _load_env_file():
    core_dir = os.getenv("FLOW_EVOLUTION_DIR")
    if core_dir:
        env_path = Path(core_dir) / ".env"
        if env_path.exists():
            _parse_env_file(env_path)
            return
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        env_path = parent / ".env"
        if env_path.exists():
            _parse_env_file(env_path)
            return

def _parse_env_file(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                if key not in os.environ:
                    os.environ[key] = val.strip().strip('"').strip("'")

_load_env_file()


class BaseLLMClient(ABC):
    def __init__(self, api_key, model, timeout=60):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = 3
    
    @abstractmethod
    def _build_request(self, prompt, max_tokens):
        pass
    
    @abstractmethod
    def _parse_response(self, response_data):
        pass
    
    def chat(self, prompt, max_tokens=2000):
        url, headers, payload = self._build_request(prompt, max_tokens)
        last_error = None
        for attempt in range(self.max_retries):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
                resp.raise_for_status()
                return self._parse_response(resp.json())
            except requests.exceptions.Timeout as e:
                last_error = e
                wait = 2 ** attempt
                print(f"⏳ 超时({self.__class__.__name__}, {attempt+1}/{self.max_retries}), {wait}s后重试...")
                time.sleep(wait)
            except requests.exceptions.HTTPError as e:
                if 400 <= e.response.status_code < 500:
                    print(f"❌ 客户端错误({e.response.status_code}), 不重试")
                    return None
                last_error = e
                wait = 2 ** attempt
                print(f"⏳ 服务端错误({attempt+1}/{self.max_retries}), {wait}s后重试...")
                time.sleep(wait)
            except Exception as e:
                last_error = e
                break
        print(f"❌ {self.__class__.__name__} 失败({self.max_retries}次): {last_error}")
        return None


class OpenAICompatibleClient(BaseLLMClient):
    def __init__(self, api_key, base_url, model, timeout=60):
        super().__init__(api_key, model, timeout)
        self.base_url = base_url
    
    def _build_request(self, prompt, max_tokens):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.3
        }
        return self.base_url, headers, payload
    
    def _parse_response(self, data):
        return data["choices"][0]["message"]["content"]


class AnthropicClient(BaseLLMClient):
    def __init__(self, api_key, model="claude-3-5-sonnet-20241022", timeout=60):
        super().__init__(api_key, model, timeout)
        self.base_url = "https://api.anthropic.com/v1/messages"
    
    def _build_request(self, prompt, max_tokens):
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }
        return self.base_url, headers, payload
    
    def _parse_response(self, data):
        return data["content"][0]["text"]


class GeminiClient(BaseLLMClient):
    def __init__(self, api_key, model="gemini-1.5-flash", timeout=60):
        super().__init__(api_key, model, timeout)
    
    def _build_request(self, prompt, max_tokens):
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.3
            }
        }
        return url, headers, payload
    
    def _parse_response(self, data):
        return data["candidates"][0]["content"]["parts"][0]["text"]


class LLMClientFactory:
    BUILTIN = {
        "siliconflow": {
            "key_env": "SILICONFLOW_API_KEY",
            "url": "https://api.siliconflow.cn/v1/chat/completions",
            "model": "deepseek-ai/DeepSeek-V3",
            "cls": OpenAICompatibleClient,
        },
        "deepseek": {
            "key_env": "DEEPSEEK_API_KEY",
            "url": "https://api.deepseek.com/v1/chat/completions",
            "model": "deepseek-chat",
            "cls": OpenAICompatibleClient,
        },
        "openai": {
            "key_env": "OPENAI_API_KEY",
            "url": "https://api.openai.com/v1/chat/completions",
            "model": "gpt-4o-mini",
            "cls": OpenAICompatibleClient,
        },
        "openrouter": {
            "key_env": "OPENROUTER_API_KEY",
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "model": "anthropic/claude-3.5-sonnet",
            "cls": OpenAICompatibleClient,
        },
        "anthropic": {
            "key_env": "ANTHROPIC_API_KEY",
            "model": "claude-3-5-sonnet-20241022",
            "cls": AnthropicClient,
        },
        "gemini": {
            "key_env": "GEMINI_API_KEY",
            "model": "gemini-1.5-flash",
            "cls": GeminiClient,
        },
    }
    
    @classmethod
    def create(cls, platform=None, api_key=None, model=None):
        if platform and platform in cls.BUILTIN:
            cfg = cls.BUILTIN[platform]
            key = api_key or os.getenv(cfg["key_env"])
            if not key:
                raise ValueError(f"需要 {cfg['key_env']}")
            if cfg["cls"] == OpenAICompatibleClient:
                return OpenAICompatibleClient(key, cfg["url"], model or cfg["model"])
            return cfg["cls"](key, model or cfg["model"])
        
        for name in ["siliconflow", "deepseek", "openai", "openrouter", "anthropic", "gemini"]:
            cfg = cls.BUILTIN[name]
            key = os.getenv(cfg["key_env"])
            if key:
                if cfg["cls"] == OpenAICompatibleClient:
                    return OpenAICompatibleClient(key, cfg["url"], model or cfg["model"])
                return cfg["cls"](key, model or cfg["model"])
        
        custom_url = os.getenv("CUSTOM_BASE_URL")
        custom_key = os.getenv("CUSTOM_API_KEY")
        if custom_url and custom_key:
            return OpenAICompatibleClient(
                custom_key, custom_url,
                model or os.getenv("CUSTOM_MODEL", "gpt-4o-mini")
            )
        
        raise ValueError(
            "❌ 找不到 API Key。方案：\n"
            "1) export SILICONFLOW_API_KEY=sk-...\n"
            "2) cp .env.example .env 并编辑\n"
            "3) export CUSTOM_BASE_URL=... + CUSTOM_API_KEY=..."
        )


class DeepSeekLLMClient:
    def __init__(self, api_key=None, model=None, platform=None):
        self._client = LLMClientFactory.create(platform, api_key, model)
    
    def chat(self, prompt, max_tokens=2000):
        return self._client.chat(prompt, max_tokens)

SiliconFlowLLMClient = DeepSeekLLMClient
