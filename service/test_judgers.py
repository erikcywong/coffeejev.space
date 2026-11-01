"""CoffeeJeV 判断器与参考 API 的单元测试。

运行方式（在工作区根目录执行，两种等价）：
    python -m unittest discover -s coffeejev/service -t .
    python coffeejev/service/test_judgers.py

覆盖：污染判断器单调性/成本阈值/三区间/OOD，驯化度硬闸门与人在环，
雾培选择的硬约束可行性、softmax 概率归一、无可行方案降级，以及 API 信封、
need_more_info、shadow 模式、审计哈希链。
"""

from __future__ import annotations

import json
import os
import sys
import threading
import unittest
import urllib.request

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:  # 兼容 discover 与直接运行两种方式
    sys.path.insert(0, _HERE)

import api  # noqa: E402
import judgers  # noqa: E402

ENVELOPE_KEYS = {
    "agent",
    "version",
    "stage",
    "jev_type",
    "decision",
    "confidence",
    "scores",
    "options",
    "human_review",
    "review_reasons",
    "reason",
    "sop_version",
    "evidence_refs",
    "latency_ms",
    "model_ids",
    "audit_id",
    "mode",
}

VALID_REQUEST = {
    "variety": "Caturra",
    "region": "云南保山",
    "stage": "aseptic_establishment",
    "sensors": {
        "ec": 1.4,
        "ph": 5.8,
        "vpd": 0.9,
        "temp": 24.0,
        "rh": 68.0,
        "do": 6.5,
        "droplet_um": 35.0,
        "water_temp": 20.0,
        "days_in_culture": 10.0,
    },
    "image_ref": "evidence/tray-042.jpg",
    "batch_history": {"contamination_rate": 0.08},
    "costs": {"fp": 1.0, "fn": 9.0},
    "objective": {"weights": {"survival": 0.5, "cost": 0.2, "quality": 0.3}},
    "mode": "live",
    "reading": {"vision_p": 0.35, "quality": 0.88},
}


# ---------------------------------------------------------------------------
# 通用数学工具
# ---------------------------------------------------------------------------


class HelperTests(unittest.TestCase):
    def test_clamp(self) -> None:
        self.assertEqual(judgers.clamp(-1.0, 0.0, 1.0), 0.0)
        self.assertEqual(judgers.clamp(2.0, 0.0, 1.0), 1.0)
        self.assertEqual(judgers.clamp(0.3, 0.0, 1.0), 0.3)

    def test_sigmoid_and_logit_roundtrip(self) -> None:
        for p in (0.001, 0.1, 0.5, 0.9, 0.999):
            self.assertAlmostEqual(judgers.sigmoid(judgers.logit(p)), p, places=6)
        self.assertEqual(judgers.sigmoid(0.0), 0.5)

    def test_logit_is_clamped(self) -> None:
        self.assertTrue(abs(judgers.logit(0.0)) < 20.0)
        self.assertTrue(abs(judgers.logit(1.0)) < 20.0)
        self.assertGreater(judgers.logit(0.9), judgers.logit(0.1))

    def test_population_stddev(self) -> None:
        self.assertEqual(judgers.population_stddev([]), 0.0)
        self.assertAlmostEqual(judgers.population_stddev([2.0, 2.0]), 0.0)
        # 总体标准差 (ddof=0)：样本 [1,3] 的总体标准差为 1
        self.assertAlmostEqual(judgers.population_stddev([1.0, 3.0]), 1.0)


# ---------------------------------------------------------------------------
# 判断器 A：污染判定
# ---------------------------------------------------------------------------


def _contamination_case(**overrides: object) -> dict[str, object]:
    case: dict[str, object] = {
        "vision_p": 0.20,
        "quality": 0.90,
        "temp": 24.0,
        "rh": 65.0,
        "days_in_culture": 14.0,
        "batch_hist_rate": 0.10,
        "cost_fp": 1.0,
        "cost_fn": 1.0,
    }
    case.update(overrides)
    return case


class ContaminationTests(unittest.TestCase):
    def test_p_contaminated_monotone_in_vision_p(self) -> None:
        probabilities = [
            judgers.judge_contamination(_contamination_case(vision_p=v)).scores[
                "p_contaminated"
            ]
            for v in (0.01, 0.05, 0.10, 0.20, 0.40, 0.70, 0.90, 0.99)
        ]
        for lower, higher in zip(probabilities, probabilities[1:]):
            self.assertGreater(higher, lower)

    def test_higher_cost_fn_lowers_tau_cost(self) -> None:
        results = [
            judgers.judge_contamination(_contamination_case(cost_fn=fn))
            for fn in (1.0, 4.0, 9.0, 20.0)
        ]
        tau_cost = [result.scores["tau_cost"] for result in results]
        for lower, higher in zip(tau_cost, tau_cost[1:]):
            self.assertGreater(lower, higher)
        # tau_cost 落在 [0.02, 0.5]
        for value in tau_cost:
            self.assertGreaterEqual(value, 0.02)
            self.assertLessEqual(value, 0.5)

    def test_operational_floor_raises_tau_hi_but_not_tau_cost(self) -> None:
        # 纯成本解 1/(1+9)=0.1 < 默认运营下限 0.15 -> 生效阈值被抬高
        floored = judgers.judge_contamination(_contamination_case(cost_fn=9.0))
        self.assertAlmostEqual(floored.scores["tau_cost"], 0.1, places=4)
        self.assertAlmostEqual(floored.scores["tau_hi"], 0.15, places=4)

        # 成本解高于下限时，生效阈值 = 成本解
        cost_driven = judgers.judge_contamination(
            _contamination_case(cost_fn=1.0, tau_min=0.05)
        )
        self.assertAlmostEqual(cost_driven.scores["tau_cost"], 0.5, places=4)
        self.assertAlmostEqual(cost_driven.scores["tau_hi"], 0.5, places=4)

    def test_floor_moves_decision_down_one_zone(self) -> None:
        # p_cal 约 26%：运营下限 5% 时进隔离区，抬到 30% 后退回复核区
        isolate = judgers.judge_contamination(p_raw=0.2, quality=0.99, tau_min=0.05)
        review = judgers.judge_contamination(p_raw=0.2, quality=0.99, tau_min=0.30)
        self.assertEqual(isolate.decision, "isolate_and_sample")
        self.assertEqual(review.decision, "review_microscopy")
        self.assertAlmostEqual(isolate.scores["tau_hi"], 0.1, places=4)   # 成本解生效
        self.assertAlmostEqual(review.scores["tau_hi"], 0.30, places=4)   # 下限生效
        self.assertEqual(
            isolate.scores["p_contaminated"], review.scores["p_contaminated"]
        )
        # 运营下限不改变成本解
        self.assertAlmostEqual(
            isolate.scores["tau_cost"], review.scores["tau_cost"], places=6
        )
        self.assertLessEqual(len(isolate.reason), judgers.REASON_MAX_LEN)
        self.assertIn("校准后污染概率", isolate.reason)
        self.assertIn("隔离", isolate.reason)
        # 理由需同时提到生效阈值与成本解
        self.assertIn("10.0%", isolate.reason)
        self.assertIn("10.0%", review.reason)  # 成本解 10% 也出现在复核理由中

    def test_three_zones_reachable(self) -> None:
        isolate = judgers.judge_contamination(
            _contamination_case(
                vision_p=0.95, quality=0.9, temp=26.0, rh=72.0,
                days_in_culture=20.0, batch_hist_rate=0.3,
            )
        )
        review = judgers.judge_contamination(
            _contamination_case(vision_p=0.20, quality=1.0)
        )
        keep = judgers.judge_contamination(
            _contamination_case(
                vision_p=0.005, quality=0.9, temp=22.0, rh=60.0,
                days_in_culture=7.0,
            )
        )
        self.assertEqual(isolate.decision, "isolate_and_sample")
        self.assertEqual(review.decision, "review_microscopy")
        self.assertEqual(keep.decision, "continue")
        self.assertEqual(
            {isolate.decision, review.decision, keep.decision},
            {"isolate_and_sample", "review_microscopy", "continue"},
        )
        # 隔离为不可逆动作，必须人在环
        self.assertTrue(isolate.human_review)

    def test_ood_when_quality_low_or_no_history(self) -> None:
        bad_quality = judgers.judge_contamination(_contamination_case(quality=0.50))
        self.assertTrue(bad_quality.human_review)
        self.assertTrue(any("OOD" in reason for reason in bad_quality.review_reasons))

        no_history = judgers.judge_contamination(
            _contamination_case(batch_hist_rate=0.0, quality=0.9)
        )
        self.assertTrue(any("OOD" in reason for reason in no_history.review_reasons))

        normal = judgers.judge_contamination(
            _contamination_case(vision_p=0.2, quality=1.0, batch_hist_rate=0.1)
        )
        self.assertFalse(any("OOD" in reason for reason in normal.review_reasons))

    def test_reason_states_probability_and_zone(self) -> None:
        result = judgers.judge_contamination(_contamination_case(vision_p=0.1))
        self.assertLessEqual(len(result.reason), judgers.REASON_MAX_LEN)
        self.assertIn("校准后污染概率", result.reason)
        self.assertIn(f"{result.scores['p_contaminated']:.0%}", result.reason)
        self.assertIn("继续培养", result.reason)
        # 新契约：scores 同时给出成本解与生效阈值
        self.assertEqual(
            set(result.scores),
            {"p_contaminated", "tau_cost", "tau_hi", "tau_lo", "image_quality"},
        )


# ---------------------------------------------------------------------------
# 判断器 B：驯化 readiness
# ---------------------------------------------------------------------------


def _readiness_case(**overrides: object) -> dict[str, object]:
    case: dict[str, object] = {
        "roots": 8.0,
        "browning": 30.0,
        "shoot_cm": 4.0,
        "leaf_color": 80.0,
        "stomata_wax": 80.0,
        "water_loss_pct": 10.0,
        "contamination_p": 0.10,
    }
    case.update(overrides)
    return case


class ReadinessTests(unittest.TestCase):
    def test_roots_gate_caps_score(self) -> None:
        result = judgers.judge_readiness(
            _readiness_case(
                roots=1.0, browning=10.0, shoot_cm=1.0,
                leaf_color=95.0, stomata_wax=95.0, water_loss_pct=3.0,
            )
        )
        self.assertLessEqual(result.scores["readiness"], 55)
        self.assertIn("根系", result.reason)

    def test_browning_gate_caps_score(self) -> None:
        result = judgers.judge_readiness(_readiness_case(browning=90.0))
        self.assertLessEqual(result.scores["readiness"], 60)
        self.assertIn("褐化", result.reason)

    def test_contamination_gate_caps_score(self) -> None:
        result = judgers.judge_readiness(_readiness_case(contamination_p=0.8))
        self.assertLessEqual(result.scores["readiness"], 40)
        self.assertIn("污染", result.reason)

    def test_readiness_always_within_bounds(self) -> None:
        for roots in (0.0, 1.0, 3.0, 8.0, 12.0, 20.0):
            for browning in (0.0, 40.0, 60.0, 61.0, 100.0):
                for leaf in (0.0, 50.0, 100.0):
                    result = judgers.judge_readiness(
                        _readiness_case(
                            roots=roots,
                            browning=browning,
                            leaf_color=leaf,
                            shoot_cm=leaf / 100.0 * 8.0,
                            stomata_wax=100.0 - leaf,
                            water_loss_pct=30.0 - leaf / 100.0 * 30.0,
                        )
                    )
                    readiness = result.scores["readiness"]
                    self.assertIsInstance(readiness, int)
                    self.assertGreaterEqual(readiness, 0)
                    self.assertLessEqual(readiness, 100)

    def test_transplant_ready_forces_human_review(self) -> None:
        result = judgers.judge_readiness(
            _readiness_case(
                roots=20.0, browning=5.0, shoot_cm=8.0,
                leaf_color=95.0, stomata_wax=95.0,
                water_loss_pct=3.0, contamination_p=0.05,
            )
        )
        self.assertGreaterEqual(result.scores["readiness"], 80)
        self.assertEqual(result.decision, "transplant_ready")
        self.assertTrue(result.human_review)
        self.assertTrue(any("移栽" in reason for reason in result.review_reasons))
        self.assertIn("移栽", result.reason)

    def test_completeness_lowers_confidence(self) -> None:
        full = judgers.judge_readiness(_readiness_case())
        empty = judgers.judge_readiness(_readiness_case(), supplied=set())
        self.assertGreater(full.confidence, empty.confidence)
        self.assertLessEqual(empty.confidence, full.confidence)
        self.assertGreaterEqual(empty.confidence, 0.35)
        self.assertLessEqual(full.confidence, 0.97)


# ---------------------------------------------------------------------------
# 判断器 C：雾培方案选择
# ---------------------------------------------------------------------------


def _fog_case(**overrides: object) -> dict[str, object]:
    case: dict[str, object] = {
        "ec": 1.4,
        "ph": 5.8,
        "vpd": 0.9,
        "temp": 24.0,
        "do_mg_l": 6.5,
        "droplet_um": 35.0,
        "water_temp": 20.0,
        "weights": {"survival": 0.5, "cost": 0.2, "quality": 0.3},
    }
    case.update(overrides)
    return case


class FogChoiceTests(unittest.TestCase):
    def test_option_shape(self) -> None:
        result = judgers.judge_fog_choice(_fog_case())
        self.assertEqual(len(result.options), 6)
        expected = {
            "action", "label", "feasible", "violations",
            "utility", "p", "components",
        }
        for option in result.options:
            self.assertEqual(set(option), expected)
            self.assertEqual(
                set(option["components"]), {"survival", "cost", "quality"}
            )

    def test_low_ph_marks_options_infeasible(self) -> None:
        result = judgers.judge_fog_choice(_fog_case(ph=4.5))
        by_action = {option["action"]: option for option in result.options}

        baseline = by_action["sop_baseline"]
        self.assertFalse(baseline["feasible"])
        self.assertIn("ph_range", baseline["violations"])

        fix = by_action["adjust_ph"]
        self.assertTrue(fix["feasible"])
        self.assertEqual(result.decision, "adjust_ph")
        self.assertAlmostEqual(
            judgers.judge_fog_choice(_fog_case(ph=4.5)).scores["post_ph"], 5.54,
            places=2,
        )

    def test_no_feasible_option_stops_and_reviews(self) -> None:
        result = judgers.judge_fog_choice(_fog_case(do_mg_l=3.5))
        self.assertTrue(all(not option["feasible"] for option in result.options))
        self.assertEqual(result.decision, "stop_and_review")
        self.assertTrue(result.human_review)
        self.assertEqual(result.confidence, 0.0)
        self.assertTrue(all(option["p"] == 0.0 for option in result.options))
        # 提升溶氧后也达不到 5.0 mg/L
        raise_do = next(o for o in result.options if o["action"] == "raise_do")
        self.assertIn("do_min", raise_do["violations"])

    def test_probabilities_sum_to_one(self) -> None:
        result = judgers.judge_fog_choice(_fog_case())
        feasible = [option for option in result.options if option["feasible"]]
        self.assertTrue(feasible)
        self.assertAlmostEqual(sum(option["p"] for option in feasible), 1.0, delta=1e-6)
        self.assertAlmostEqual(
            sum(option["p"] for option in result.options), 1.0, delta=1e-6
        )

    def test_recommended_option_satisfies_hard_constraints(self) -> None:
        result = judgers.judge_fog_choice(_fog_case())
        chosen = next(
            option for option in result.options
            if option["action"] == result.decision
        )
        self.assertTrue(chosen["feasible"])
        self.assertEqual(chosen["violations"], [])
        self.assertGreaterEqual(result.scores["post_ec"], 0.8)
        self.assertLessEqual(result.scores["post_ec"], 2.0)
        self.assertGreaterEqual(result.scores["post_ph"], 5.3)
        self.assertLessEqual(result.scores["post_ph"], 6.4)
        # 置信度是边际置信 σ(ΔU/τ)，不是 softmax 最大值（后者在六个近似打平时只有 ~0.2）
        self.assertGreater(result.confidence, 0.5)
        self.assertLessEqual(result.confidence, 0.99)
        self.assertIsNotNone(result.scores["margin"])
        self.assertGreaterEqual(result.scores["margin"], 0.0)

    def test_water_temp_is_zone_gate_not_option_constraint(self) -> None:
        """液温超限是「整套系统」的前置状态：转人工，但不该把 6 个候选全判违规。"""
        result = judgers.judge_fog_choice(_fog_case(water_temp=25.0))
        self.assertEqual(result.decision, "stop_and_review")
        self.assertTrue(result.human_review)
        self.assertEqual(result.confidence, 0.0)
        self.assertTrue(result.scores["zone_gates"])
        self.assertIn("营养液", result.scores["zone_gates"][0])
        for option in result.options:
            self.assertNotIn("water_temp_max", option["violations"])
        self.assertTrue(any(option["feasible"] for option in result.options))
        self.assertTrue(any("前置条件" in reason for reason in result.review_reasons))


    def test_in_band_state_keeps_sop(self) -> None:
        """所有参数都在目标值时，唯一正确答案是「什么都不做」——不许产生动作偏好。"""
        result = judgers.judge_fog_choice(_fog_case())
        self.assertEqual(result.decision, "sop_baseline")
        self.assertFalse(result.human_review)
        self.assertGreaterEqual(result.confidence, 0.70)

    def test_single_feasible_costly_action_requires_review(self) -> None:
        """约束只剩「冲洗储液」这一个高成本动作时，不能替人决定这笔钱。"""
        result = judgers.judge_fog_choice(_fog_case(ec=2.4, do_mg_l=4.6))
        feasible = [option["action"] for option in result.options if option["feasible"]]
        self.assertEqual(feasible, ["flush_reservoir"])
        self.assertEqual(result.decision, "flush_reservoir")
        self.assertTrue(result.human_review)
        self.assertTrue(any("成本" in reason for reason in result.review_reasons))


# ---------------------------------------------------------------------------
# 判断器 A 的复核契约
# ---------------------------------------------------------------------------


class ContaminationReviewContractTests(unittest.TestCase):
    def test_review_microscopy_always_requests_human(self) -> None:
        """决策是「叫人来镜检」却把 human_review 设成 False，等于没有人被叫。"""
        result = judgers.judge_contamination(
            _contamination_case(vision_p=0.20, quality=1.0)
        )
        self.assertEqual(result.decision, "review_microscopy")
        self.assertTrue(result.human_review)
        self.assertTrue(result.review_reasons)

    def test_continue_can_skip_review(self) -> None:
        result = judgers.judge_contamination(
            _contamination_case(
                vision_p=0.005, quality=0.9, temp=22.0, rh=60.0, days_in_culture=7.0
            )
        )
        self.assertEqual(result.decision, "continue")
        self.assertFalse(result.human_review)


# ---------------------------------------------------------------------------
# readiness 的比值带
# ---------------------------------------------------------------------------


class RatioBandTests(unittest.TestCase):
    def test_etiolated_shoot_loses_ratio_points(self) -> None:
        """株高/根数比 1.6（徒长）不该拿满分；0.64（矮壮）才在目标带内。"""
        stout = judgers.judge_readiness(_readiness_case(roots=5.0, shoot_cm=3.2))
        etiolated = judgers.judge_readiness(_readiness_case(roots=5.0, shoot_cm=8.0))
        self.assertEqual(judgers._ratio_score(3.2, 5.0), 100.0)
        self.assertLess(judgers._ratio_score(8.0, 5.0), 20.0)
        self.assertLess(etiolated.scores["readiness"], stout.scores["readiness"])
        self.assertEqual(judgers._ratio_score(3.0, 0.0), 0.0)


# ---------------------------------------------------------------------------
# 请求校验：必填字段按判断器区分
# ---------------------------------------------------------------------------


class ValidationScopeTests(unittest.TestCase):
    def test_aseptic_stage_does_not_require_ec_ph(self) -> None:
        """组培瓶里没有 EC/pH 探头：无菌检查不应被「缺 sensors.ec」拦下。"""
        result = api.decide({
            "variety": "Arabica-Geisha",
            "region": "YN-01",
            "stage": "aseptic_establishment",
            "sensors": {"temp": 25.5, "rh": 74, "days_in_culture": 12},
            "reading": {"vision_p": 0.2, "quality": 1.0},
        })
        self.assertNotEqual(result["decision"], "need_more_info")

    def test_fog_stage_still_requires_full_sensor_set(self) -> None:
        result = api.decide({
            "variety": "Arabica-Caturra",
            "region": "YN-01",
            "stage": "aeroponics_nutrition",
            "sensors": {"ec": 1.4, "ph": 5.8},
        })
        self.assertEqual(result["decision"], "need_more_info")
        self.assertIn("sensors.vpd", result["missing"])

    def test_readiness_requires_some_evidence(self) -> None:
        result = api.decide({
            "variety": "Arabica-Caturra",
            "region": "YN-01",
            "stage": "acclimation",
            "sensors": {"temp": 24},
        })
        self.assertEqual(result["decision"], "need_more_info")



# ---------------------------------------------------------------------------
# HTTP API
# ---------------------------------------------------------------------------


class ApiTests(unittest.TestCase):
    server: "api.ThreadingHTTPServer"
    thread: threading.Thread
    port: int

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = api.make_server("127.0.0.1", 0)  # 0 -> 系统分配临时端口
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    # -- 工具 -------------------------------------------------------------
    def _request(self, path: str, payload: object | None = None) -> tuple[int, dict]:
        data = (
            None if payload is None
            else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        )
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=data,
            method="POST" if data is not None else "GET",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    # -- 用例 -------------------------------------------------------------
    def test_decide_valid_envelope(self) -> None:
        status, body = self._request("/coffee-jev/decide", VALID_REQUEST)
        self.assertEqual(status, 200)
        self.assertTrue(ENVELOPE_KEYS.issubset(set(body)))
        self.assertEqual(body["agent"], "CoffeeJeV")
        self.assertEqual(body["version"], "1.0.0")
        self.assertEqual(body["sop_version"], "coffee-tc-aero-v1.0")
        self.assertEqual(body["stage"], "aseptic_establishment")
        self.assertEqual(body["jev_type"], "noul")
        self.assertEqual(body["mode"], "live")
        self.assertIn(
            body["decision"], {"isolate_and_sample", "review_microscopy", "continue"}
        )
        self.assertTrue(0.0 <= body["confidence"] <= 1.0)
        self.assertIsInstance(body["human_review"], bool)
        self.assertGreater(body["latency_ms"], 0.0)
        self.assertTrue(body["audit_id"])
        self.assertEqual(body["evidence_refs"], ["evidence/tray-042.jpg"])
        # 两段式阈值：成本解与实际生效阈值都要给出
        self.assertIn("tau_cost", body["scores"])
        self.assertIn("tau_hi", body["scores"])
        self.assertNotIn("missing", body)
        self.assertNotIn("would_decide", body)

    def test_decide_readiness_stage(self) -> None:
        request = dict(VALID_REQUEST)
        request["stage"] = "acclimation"
        request["reading"] = {
            "roots": 12.0,
            "browning": 15.0,
            "shoot_cm": 6.0,
            "leaf_color": 90.0,
            "stomata_wax": 88.0,
            "water_loss_pct": 6.0,
            "contamination_p": 0.05,
        }
        _, body = self._request("/coffee-jev/decide", request)
        self.assertEqual(body["jev_type"], "score")
        self.assertEqual(
            body["decision"],
            {"transplant_ready", "delay_adjust", "continue_acclimation"}.intersection(
                {body["decision"]}
            ).pop(),
        )
        self.assertIn("readiness", body["scores"])
        self.assertNotIn("defaulted", body)

    def test_decide_fog_stage(self) -> None:
        request = dict(VALID_REQUEST)
        request["stage"] = "aeroponics_nutrition"
        _, body = self._request("/coffee-jev/decide", request)
        self.assertEqual(body["jev_type"], "choice")
        self.assertEqual(len(body["options"]), 6)
        self.assertIn("utility", body["scores"])
        self.assertIn("post_ec", body["scores"])

    def test_missing_fields_need_more_info(self) -> None:
        request = dict(VALID_REQUEST)
        request.pop("variety")
        status, body = self._request("/coffee-jev/decide", request)
        self.assertEqual(status, 200)
        self.assertEqual(body["decision"], "need_more_info")
        self.assertTrue(body["human_review"])
        self.assertIn("variety", body["missing"])

        request = json.loads(json.dumps(VALID_REQUEST))
        request["sensors"].pop("temp")
        _, body = self._request("/coffee-jev/decide", request)
        self.assertIn("sensors.temp", body["missing"])

    def test_unknown_stage_need_more_info(self) -> None:
        request = dict(VALID_REQUEST)
        request["stage"] = "not_a_real_stage"
        _, body = self._request("/coffee-jev/decide", request)
        self.assertEqual(body["decision"], "need_more_info")
        self.assertIn("stage", body["missing"])

    def test_shadow_mode(self) -> None:
        request = dict(VALID_REQUEST)
        request["mode"] = "shadow"
        _, body = self._request("/coffee-jev/decide", request)
        self.assertEqual(body["mode"], "shadow")
        self.assertEqual(body["would_decide"], body["decision"])
        self.assertIs(body["executed"], False)

    def test_defaulted_fields_reported(self) -> None:
        request = json.loads(json.dumps(VALID_REQUEST))
        request.pop("reading")
        request.pop("batch_history")
        request.pop("costs")
        _, body = self._request("/coffee-jev/decide", request)
        self.assertIn("defaulted", body)
        self.assertIn("reading.vision_p", body["defaulted"])
        self.assertIn("batch_history.contamination_rate", body["defaulted"])
        self.assertIn("costs.fn", body["defaulted"])

    def test_tau_min_from_request(self) -> None:
        # costs.tau_min 抬高运营下限：p_cal≈26% 退回镜检复核区
        request = json.loads(json.dumps(VALID_REQUEST))
        request["reading"] = {"vision_p": 0.2, "quality": 0.99}
        request["costs"] = {"fp": 1.0, "fn": 9.0, "tau_min": 0.30}
        _, body = self._request("/coffee-jev/decide", request)
        self.assertEqual(body["decision"], "review_microscopy")
        self.assertAlmostEqual(body["scores"]["tau_cost"], 0.10, places=4)
        self.assertAlmostEqual(body["scores"]["tau_hi"], 0.30, places=4)

        # params.tau_min 同样生效（缺省 costs 时用默认 C_FP=1 / C_FN=9）
        fallback = json.loads(json.dumps(request))
        fallback.pop("costs")
        fallback["params"] = {"tau_min": 0.30}
        _, body = self._request("/coffee-jev/decide", fallback)
        self.assertEqual(body["decision"], "review_microscopy")
        self.assertAlmostEqual(body["scores"]["tau_cost"], 0.10, places=4)
        self.assertAlmostEqual(body["scores"]["tau_hi"], 0.30, places=4)

    def test_health(self) -> None:
        status, body = self._request("/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ok")
        self.assertEqual(
            body["judgers"], ["contamination", "readiness", "fog_choice"]
        )
        self.assertEqual(body["sop_version"], "coffee-tc-aero-v1.0")

    def test_audit_chain_valid(self) -> None:
        self._request("/coffee-jev/decide", VALID_REQUEST)
        status, body = self._request("/coffee-jev/audit")
        self.assertEqual(status, 200)
        self.assertIs(body["chain_valid"], True)
        self.assertGreaterEqual(len(body["entries"]), 1)
        self.assertLessEqual(len(body["entries"]), 50)
        for entry in body["entries"]:
            self.assertTrue({"seq", "ts", "audit_id", "prev", "hash"}.issubset(entry))
            self.assertEqual(len(entry["hash"]), 64)
        sequences = [entry["seq"] for entry in body["entries"]]
        self.assertEqual(sequences, sorted(sequences))


if __name__ == "__main__":
    unittest.main(verbosity=2)
