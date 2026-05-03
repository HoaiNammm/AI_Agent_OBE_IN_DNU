"""
LLM Helper - Factory function tạo LLM instance theo cấu hình agent
Hỗ trợ Groq (primary), Gemini (Google) và Claude (Anthropic)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger

logger = get_logger("utils.llm_helper")


def get_llm(agent_name: str):
    """
    Tạo LLM instance phù hợp cho agent.
    
    Ưu tiên: Groq → Gemini → Claude.
    
    Args:
        agent_name: Tên agent (vd: "supervisor", "understand")
    
    Returns:
        LangChain ChatModel instance
    """
    from config import GROQ_API_KEY, GROQ_MODEL, GOOGLE_API_KEY, ANTHROPIC_API_KEY, MODEL_PARAMS

    # Groq là primary
    if GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq
            logger.info(f"[{agent_name}] Sử dụng Groq: {GROQ_MODEL}")
            return ChatGroq(
                model=GROQ_MODEL,
                api_key=GROQ_API_KEY,
                temperature=MODEL_PARAMS["temperature"],
            )
        except ImportError:
            logger.warning("langchain_groq chưa được cài đặt, fallback về Gemini")
        except Exception as e:
            logger.warning(f"Lỗi khởi tạo Groq: {e}, fallback về Gemini")

    # Fallback về Gemini
    if GOOGLE_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from config import GEMINI_MODEL
            logger.info(f"[{agent_name}] Sử dụng Gemini: {GEMINI_MODEL}")
            return ChatGoogleGenerativeAI(
                model=GEMINI_MODEL,
                google_api_key=GOOGLE_API_KEY,
                temperature=MODEL_PARAMS["temperature"],
            )
        except Exception as e:
            logger.warning(f"Lỗi khởi tạo Gemini: {e}, fallback về Claude")

    # Fallback về Claude
    if ANTHROPIC_API_KEY:
        try:
            from langchain_anthropic import ChatAnthropic
            from config import CLAUDE_MODEL
            logger.info(f"[{agent_name}] Sử dụng Claude: {CLAUDE_MODEL}")
            return ChatAnthropic(
                model=CLAUDE_MODEL,
                api_key=ANTHROPIC_API_KEY,
                temperature=MODEL_PARAMS["temperature"],
                max_tokens=MODEL_PARAMS["max_tokens"],
            )
        except Exception as e:
            logger.error(f"Lỗi khởi tạo Claude: {e}")

    raise ValueError(
        "Cần ít nhất một API Key hợp lệ: GROQ_API_KEY, GOOGLE_API_KEY hoặc ANTHROPIC_API_KEY"
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


async def call_llm_json_async(agent_name: str, system_prompt: str, user_prompt: str,
                              timeout: int = 120) -> str:
    """
    Async version của call_llm_json với timeout và friendly error mapping.

    Raises:
        TimeoutError: nếu LLM không trả lời trong `timeout` giây.
        RuntimeError: bọc các lỗi API (rate-limit, network, ...) thành thông báo thân thiện.
    """
    import asyncio
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = get_llm(agent_name)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    try:
        response = await asyncio.wait_for(llm.ainvoke(messages), timeout=timeout)
        return response.content
    except asyncio.TimeoutError:
        logger.error(f"[{agent_name}] LLM timeout sau {timeout}s")
        raise TimeoutError(
            f"AI không phản hồi sau {timeout} giây. "
            "Vui lòng thử lại sau hoặc kiểm tra kết nối mạng."
        )
    except Exception as e:
        err_str = str(e).lower()
        if "429" in str(e) or "rate limit" in err_str or "rate_limit" in err_str:
            logger.warning(f"[{agent_name}] Rate limit: {e}")
            raise RuntimeError(
                "API đã đạt giới hạn yêu cầu (rate limit). "
                "Vui lòng đợi vài giây rồi thử lại."
            )
        if "401" in str(e) or "unauthorized" in err_str or "api key" in err_str:
            logger.error(f"[{agent_name}] Auth error: {e}")
            raise RuntimeError(
                "API Key không hợp lệ hoặc đã hết hạn. "
                "Vui lòng kiểm tra lại cấu hình GROQ_API_KEY / GOOGLE_API_KEY."
            )
        if "503" in str(e) or "service unavailable" in err_str or "overloaded" in err_str:
            logger.warning(f"[{agent_name}] Service unavailable: {e}")
            raise RuntimeError(
                "Dịch vụ AI tạm thời không khả dụng (503). "
                "Vui lòng thử lại sau ít phút."
            )
        logger.error(f"[{agent_name}] LLM error: {e}")
        raise


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
