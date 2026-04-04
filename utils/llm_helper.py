"""
LLM Helper - Factory function tạo LLM instance theo cấu hình agent
Hỗ trợ Gemini (Google) và Claude (Anthropic)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger

logger = get_logger("utils.llm_helper")


def get_llm(agent_name: str):
    """
    Tạo LLM instance phù hợp cho agent.
    
    Ưu tiên: Claude nếu có ANTHROPIC_API_KEY, fallback về Gemini.
    
    Args:
        agent_name: Tên agent (vd: "supervisor", "understand")
    
    Returns:
        LangChain ChatModel instance
    """
    from config import GOOGLE_API_KEY, ANTHROPIC_API_KEY, get_agent_model, MODEL_PARAMS

    model_name = get_agent_model(agent_name)

    # Thử Claude trước (nếu model là Claude và có API key)
    if "claude" in model_name.lower() and ANTHROPIC_API_KEY:
        try:
            from langchain_anthropic import ChatAnthropic
            logger.info(f"[{agent_name}] Sử dụng Claude: {model_name}")
            return ChatAnthropic(
                model=model_name,
                api_key=ANTHROPIC_API_KEY,
                temperature=MODEL_PARAMS["temperature"],
                max_tokens=MODEL_PARAMS["max_tokens"],
            )
        except ImportError:
            logger.warning("langchain_anthropic chưa được cài đặt, fallback về Gemini")
        except Exception as e:
            logger.warning(f"Lỗi khởi tạo Claude: {e}, fallback về Gemini")

    # Fallback về Gemini
    if GOOGLE_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from config import GEMINI_MODEL

            gemini_model = GEMINI_MODEL if "claude" in model_name.lower() else model_name
            logger.info(f"[{agent_name}] Sử dụng Gemini: {gemini_model}")
            return ChatGoogleGenerativeAI(
                model=gemini_model,
                google_api_key=GOOGLE_API_KEY,
                temperature=MODEL_PARAMS["temperature"],
            )
        except Exception as e:
            logger.error(f"Lỗi khởi tạo Gemini: {e}")
            raise

    raise ValueError(
        "Cần ít nhất một API Key hợp lệ: GOOGLE_API_KEY hoặc ANTHROPIC_API_KEY"
    )


def call_llm_json(agent_name: str, system_prompt: str, user_prompt: str) -> str:
    """
    Gọi LLM và trả về response dạng string (raw).
    Parse JSON được thực hiện bởi caller.
    
    Args:
        agent_name: Tên agent để chọn LLM phù hợp
        system_prompt: System prompt
        user_prompt: User prompt
    
    Returns:
        Raw text response từ LLM
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = get_llm(agent_name)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    response = llm.invoke(messages)
    return response.content


async def call_llm_json_async(agent_name: str, system_prompt: str, user_prompt: str) -> str:
    """
    Async version của call_llm_json.
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = get_llm(agent_name)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    response = await llm.ainvoke(messages)
    return response.content


def extract_json_from_response(text: str) -> str:
    """
    Trích xuất JSON từ response LLM (loại bỏ markdown code blocks nếu có).
    """
    import re

    # Tìm JSON trong code block markdown
    pattern = r"```(?:json)?\s*([\s\S]*?)```"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()

    # Tìm JSON object trực tiếp
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    return text.strip()
