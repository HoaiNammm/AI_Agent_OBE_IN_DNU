"""
Tests cho OBE utilities
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.obe_utils import (
    get_bloom_level,
    get_bloom_verbs_for_level,
    suggest_irma_for_bloom,
    calculate_sessions,
    get_all_pi_codes,
    get_pi_description,
    get_plo_for_pi,
    PLO_DATA,
    PI_DATA,
    BLOOM_VERBS,
)


class TestBloomTaxonomy:
    def test_bloom_level_from_english_verb(self):
        level, name = get_bloom_level("explain")
        assert level == 2
        assert "Hiểu" in name or "Understand" in name

    def test_bloom_level_from_vietnamese_verb(self):
        level, name = get_bloom_level("thiết kế")
        assert level == 6

    def test_bloom_level_apply(self):
        level, _ = get_bloom_level("apply")
        assert level == 3

    def test_bloom_level_analyze(self):
        level, _ = get_bloom_level("phân tích")
        assert level == 4

    def test_bloom_level_evaluate(self):
        level, _ = get_bloom_level("evaluate")
        assert level == 5

    def test_bloom_level_remember(self):
        level, _ = get_bloom_level("define")
        assert level == 1

    def test_bloom_level_default_for_unknown(self):
        level, _ = get_bloom_level("unknown_verb_xyz")
        assert level == 2  # default: Understand

    def test_get_bloom_verbs_for_level(self):
        verbs = get_bloom_verbs_for_level(3)
        assert isinstance(verbs, list)
        assert len(verbs) > 0
        assert "apply" in verbs or "áp dụng" in verbs

    def test_all_levels_have_verbs(self):
        for level in range(1, 7):
            verbs = get_bloom_verbs_for_level(level)
            assert len(verbs) > 0, f"Level {level} không có verb nào"


class TestIRMA:
    def test_suggest_irma_bloom_1_2(self):
        assert suggest_irma_for_bloom(1) == "I"
        assert suggest_irma_for_bloom(2) == "I"

    def test_suggest_irma_bloom_3(self):
        assert suggest_irma_for_bloom(3) == "R"

    def test_suggest_irma_bloom_4(self):
        assert suggest_irma_for_bloom(4) == "M"

    def test_suggest_irma_bloom_5_6(self):
        assert suggest_irma_for_bloom(5) == "A"
        assert suggest_irma_for_bloom(6) == "A"


class TestSessionCalculation:
    def test_3_credits(self):
        result = calculate_sessions("3")
        assert result["credits"] == 3
        assert result["total_periods"] == 45
        assert result["theory_periods"] + result["lab_periods"] == 45

    def test_2_credits(self):
        result = calculate_sessions("2")
        assert result["credits"] == 2
        assert result["total_periods"] == 30

    def test_custom_ratio(self):
        result = calculate_sessions("3", theory_ratio=1.0)
        assert result["lab_periods"] == 0
        assert result["theory_periods"] == 45

    def test_invalid_credits(self):
        result = calculate_sessions("invalid")
        assert result["credits"] == 3  # default


class TestPLOData:
    def test_plo_data_not_empty(self):
        assert len(PLO_DATA) >= 5

    def test_plo_codes_format(self):
        for code in PLO_DATA.keys():
            assert code.startswith("PLO"), f"{code} không đúng format PLO"

    def test_plo_descriptions_not_empty(self):
        for code, desc in PLO_DATA.items():
            assert len(desc) > 10, f"{code} description quá ngắn"


class TestPIData:
    def test_pi_data_not_empty(self):
        assert len(PI_DATA) >= 5

    def test_pi_codes_format(self):
        for plo_code, pis in PI_DATA.items():
            for pi_code in pis.keys():
                assert pi_code.startswith("PI"), f"{pi_code} không đúng format PI"
                # Check PI code links to PLO (e.g., PI1.1 → PLO1)
                plo_num = plo_code.replace("PLO", "")
                assert pi_code.startswith(f"PI{plo_num}."), \
                    f"{pi_code} không thuộc {plo_code}"

    def test_get_all_pi_codes(self):
        codes = get_all_pi_codes()
        assert len(codes) >= 10

    def test_get_pi_description(self):
        desc = get_pi_description("PI1.1")
        assert len(desc) > 0

    def test_get_plo_for_pi(self):
        plo = get_plo_for_pi("PI1.1")
        assert plo == "PLO1"

        plo = get_plo_for_pi("PI3.2")
        assert plo == "PLO3"

    def test_get_plo_for_unknown_pi(self):
        plo = get_plo_for_pi("PI99.99")
        assert plo == ""

    def test_all_plos_have_pis(self):
        for plo_code in PLO_DATA.keys():
            assert plo_code in PI_DATA, f"{plo_code} không có PI"
            assert len(PI_DATA[plo_code]) >= 1, f"{plo_code} không có PI nào"
