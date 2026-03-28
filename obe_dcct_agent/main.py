"""
main.py - CLI entry point for the OBE DCCT Agent pipeline.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from config import LOG_LEVEL, LOG_DIR
from graph import graph
from state import DCCTState

# ── Logging setup ──────────────────────────────────────────────────────────────
import os

os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(LOG_DIR, "agent.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OBE DCCT Agent - Generate detailed course outline (Đề Cương Chi Tiết)"
    )
    parser.add_argument("--course-name", required=True, help="Course name")
    parser.add_argument("--course-code", required=True, help="Course code")
    parser.add_argument("--credits", type=int, required=True, help="Number of credits")
    parser.add_argument("--department", default="", help="Department name")
    parser.add_argument(
        "--input", dest="raw_input", default="", help="Optional free-text input"
    )
    parser.add_argument(
        "--output-json", action="store_true", help="Print final state as JSON"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    initial_state: DCCTState = {
        "course_name": args.course_name,
        "course_code": args.course_code,
        "credits": args.credits,
        "department": args.department,
        "raw_input": args.raw_input,
        "messages": [],
    }

    logger.info("Starting DCCT pipeline for course: %s (%s)", args.course_name, args.course_code)

    final_state = graph.invoke(initial_state)

    if args.output_json:
        # Serialize state (excluding messages for brevity)
        printable = {k: v for k, v in final_state.items() if k != "messages"}
        print(json.dumps(printable, indent=2, default=str))
    else:
        output_path = final_state.get("output_path")
        if output_path:
            logger.info("DCCT document generated: %s", output_path)
            print(f"\n✅ DCCT generated successfully: {output_path}")
        else:
            logger.warning("Pipeline finished but no output file was produced.")
            print("\n⚠️  Pipeline finished but no output file was produced.")

        validation = final_state.get("validation_result")
        if validation:
            status = "✅ PASSED" if validation.get("passed") else "❌ FAILED"
            score = validation.get("confidence_score", 0)
            print(f"   Validation: {status}  |  Confidence: {score:.0%}")

        errors = final_state.get("errors", [])
        if errors:
            print("\n⚠️  Errors encountered:")
            for err in errors:
                print(f"   - {err}")


if __name__ == "__main__":
    main()
