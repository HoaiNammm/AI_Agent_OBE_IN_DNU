# main.py
import asyncio
from config import validate_config
from state import DCCTState
from graph import get_graph
from rag.index_builder import initialize_rag

async def run_agent(course_code: str, course_name: str, summary: str):
    if not validate_config():
        return None

    await initialize_rag()

    initial_state: DCCTState = {
        "user_input": f"{course_code} - {course_name}\n{summary}",
        "course_code": course_code,
        "course_name": course_name,
        "credits": "3",
        "summary": summary,
        "outline": None,
        "extracted_info": {},
        "clo_list": [],
        "mapping_matrix": [],
        "teaching_plan": [],
        "assessment_plan": [],
        "rubrics": {},
        "messages": [],
        "current_step": "understand",
        "confidence_score": 0.0,
        "critic_feedback": [],
        "retry_counts": {},
        "preview_data": None,
        "needs_human_input": False,
        "human_feedback": None,
        "final_dcct_data": None,
        "export_ready": False,
        "errors": [],
        "warnings": [],
    }

    graph = get_graph()

    try:
        result = await graph.ainvoke(initial_state)
        print(f"✅ Hoàn thành. Confidence: {result.get('confidence_score', 0):.1f}%")
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(run_agent("CSC4012", "Trí tuệ nhân tạo ứng dụng", "Học phần giới thiệu ứng dụng AI thực tế."))