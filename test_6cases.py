"""
Test 6 error cases — runs without UI/LLM calls.
"""
import sys, io, asyncio, inspect
sys.path.insert(0, ".")

results = []

def chk(label, ok, note=""):
    status = "PASS" if ok else "FAIL"
    results.append((label, status, note))
    suffix = f" -- {note[:90]}" if note else ""
    print(f"  [{status}] {label}{suffix}")


# ─── Case 1: Upload .jpg ────────────────────────────────────────────────────
print("=== Case 1: Upload .jpg ===")
from utils.dcct_parser import extract_text_from_bytes

jpg_bytes = bytes([0xFF, 0xD8, 0xFF, 0xE0])  # JPEG header
try:
    txt = extract_text_from_bytes(jpg_bytes, "photo.jpg")
    chk("No crash", True)
    chk("Returns empty string for unsupported ext", txt == "")
except Exception as e:
    chk("No crash", False, str(e))

# ─── Case 2: Upload .docx corrupt ───────────────────────────────────────────
print("\n=== Case 2: .docx corrupt ===")
corrupt = b"PK\x03\x04this is not a valid docx file at all"
try:
    extract_text_from_bytes(corrupt, "broken.docx")
    chk("Raises ValueError for corrupt docx", False, "No exception raised")
except ValueError as e:
    chk("Raises ValueError for corrupt docx", True)
    chk("Error message is non-empty", len(str(e)) > 10)
except Exception as e:
    chk("Raises ValueError for corrupt docx", False, f"Wrong type: {type(e).__name__}")

# ─── Case 3: Ma HP trong ────────────────────────────────────────────────────
print("\n=== Case 3: Ma HP trong (empty course code) ===")

def _validate_form(course_code, course_name, summary):
    missing = []
    if not course_code or not course_code.strip():
        missing.append("Ma hoc phan")
    if not course_name or not course_name.strip():
        missing.append("Ten hoc phan")
    if not summary or not summary.strip():
        missing.append("Mo ta")
    return missing

chk("Empty code caught", "Ma hoc phan" in _validate_form("", "AI", "desc..."))
chk("Whitespace-only caught", "Ma hoc phan" in _validate_form("   ", "AI", "desc..."))
chk("Valid form passes", len(_validate_form("CSC4007", "AI", "desc...")) == 0)

# ─── Case 4: Ma HP khong co trong KB ────────────────────────────────────────
print("\n=== Case 4: Ma HP khong co trong KB ===")
from kb.plo_pi_loader import get_course_irma

result_unknown = get_course_irma("XXXYYY999", "KHMT")
chk("get_course_irma returns {} for unknown HP", result_unknown == {})

# Simulate mapping.py warning logic
_warnings = []
_code = "XXXYYY999"
if not get_course_irma(_code, "KHMT"):
    _warnings.append(f"HP '{_code}' chua co trong ma tran PI ngành KHMT. IRMA sinh tu dong.")
chk("Warning generated in mapping logic", len(_warnings) > 0)

# Check if frontend reads 'warnings' key from result
# frontend/app.py line 865: errors = result.get("errors", [])
# Bug: warnings not shown
import ast, tokenize
with open("frontend/app.py", encoding="utf-8") as f:
    app_src = f.read()
warnings_shown = (
    "result.get(\"warnings\"" in app_src
    or "result.get('warnings'" in app_src
)
chk("Frontend displays warnings from result state", warnings_shown,
    "BUG: app.py only reads 'errors', warnings are invisible" if not warnings_shown else "")

# ─── Case 5: DCCT cu khong co CLO ───────────────────────────────────────────
print("\n=== Case 5: DCCT cu khong co CLO ===")

async def _test_mapping_empty():
    from agents.mapping import mapping_node
    state = {
        "clo_list": [],
        "extracted_info": {"course_code": "CSC4007", "course_name": "NLP"},
        "course_code": "CSC4007",
        "course_name": "NLP",
        "program": "KHMT",
        "warnings": [],
        "errors": [],
        "irma_matrix": None,
    }
    return await mapping_node(state)

out5 = asyncio.run(_test_mapping_empty())
chk("mapping_node: no crash with empty clo_list", True)
chk("mapping_node: returns mapping_done", out5.get("current_step") == "mapping_done")
chk("mapping_node: adds warning about missing CLO",
    any("CLO" in w for w in out5.get("warnings", [])))

from agents.teaching_plan import teaching_plan_node
tp_src = inspect.getsource(teaching_plan_node)
has_tp_guard = "if not clo_list" in tp_src
chk("teaching_plan_node: guard for empty clo_list", has_tp_guard,
    "MISSING guard -- LLM still called with empty input" if not has_tp_guard else "")

from agents.assessment import assessment_node
as_src = inspect.getsource(assessment_node)
has_as_guard = "if not clo_list" in as_src
chk("assessment_node: guard for empty clo_list", has_as_guard,
    "MISSING guard" if not has_as_guard else "")

# Validator does check len(clo_list) < 3
from agents.validator import _basic_validation
basic_issues = _basic_validation([], [], [], [], None)
chk("validator: flags empty clo_list as issue",
    any("CLO" in i or "ít" in i for i in basic_issues), str(basic_issues[:1]))

# ─── Case 6: LLM timeout / rate limit ───────────────────────────────────────
print("\n=== Case 6: LLM timeout / rate limit ===")
from utils.llm_helper import call_llm_json_async
src6 = inspect.getsource(call_llm_json_async)
has_timeout = "wait_for" in src6 or "asyncio.timeout" in src6 or "TimeoutError" in src6
chk("call_llm_json_async: has timeout wrapper", has_timeout,
    "MISSING -- app hangs on slow API" if not has_timeout else "")

# Check that agent-level except catches SDK errors
from agents.understand import understand_node
u_src = inspect.getsource(understand_node)
chk("understand_node: catches Exception from LLM", "except Exception" in u_src)

# Friendly rate-limit message is in llm_helper (architecture: helper maps errors, agents forward them)
src6_helper = inspect.getsource(call_llm_json_async)
has_friendly = "429" in src6_helper and "rate limit" in src6_helper.lower() and "TimeoutError" in src6_helper
chk("llm_helper: friendly rate-limit + timeout messages", has_friendly,
    "MISSING friendly messages" if not has_friendly else "")

# Summary
print("\n" + "=" * 55)
fails = [r for r in results if r[1] == "FAIL"]
print(f"Total: {len(results)} | PASS: {len(results)-len(fails)} | FAIL: {len(fails)}")
if fails:
    print("\nFailed checks needing fixes:")
    for label, _, note in fails:
        print(f"  - {label}")
        if note:
            print(f"    {note}")
