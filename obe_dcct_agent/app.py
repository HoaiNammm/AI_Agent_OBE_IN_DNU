"""
app.py - FastAPI application exposing the DCCT Agent pipeline as a REST API.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from graph import graph
from state import DCCTState

app = FastAPI(
    title="OBE DCCT Agent API",
    description="REST API for generating Đề Cương Chi Tiết (DCCT) following OBE standards.",
    version="0.1.0",
)


# ── Request / Response models ──────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    course_name: str
    course_code: str
    credits: int
    department: str = ""
    raw_input: str = ""


class GenerateResponse(BaseModel):
    output_path: str | None = None
    preview_text: str | None = None
    validation_passed: bool | None = None
    confidence_score: float | None = None
    errors: list[str] = []


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    """Health-check endpoint."""
    return {"status": "ok"}


@app.post("/generate", response_model=GenerateResponse)
def generate_dcct(request: GenerateRequest) -> GenerateResponse:
    """
    Run the full DCCT pipeline and return results.
    """
    initial_state: DCCTState = {
        "course_name": request.course_name,
        "course_code": request.course_code,
        "credits": request.credits,
        "department": request.department,
        "raw_input": request.raw_input,
        "messages": [],
    }

    try:
        final_state = graph.invoke(initial_state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    validation = final_state.get("validation_result") or {}
    return GenerateResponse(
        output_path=final_state.get("output_path"),
        preview_text=final_state.get("preview_text"),
        validation_passed=validation.get("passed"),
        confidence_score=validation.get("confidence_score"),
        errors=final_state.get("errors", []),
    )
