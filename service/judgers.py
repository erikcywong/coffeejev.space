"""CoffeeJeV 判断器参考实现（纯标准库，Python 3.11+）。

三个判断器与前端 ``coffeejev/index.html`` 内的 JS 引擎一一对应：

- ``judge_contamination`` -> jev_type ``"noul"``   组培污染判定（三区间 + OOD）
- ``judge_readiness``     -> jev_type ``"score"``  驯化度打分（硬闸门 + 置信度）
- ``judge_fog_choice``    -> jev_type ``"choice"`` 雾培参数方案选择（效用 + 硬约束）

输入/输出契约见 ``README.md``。所有阈值与权重都是**设计目标数值**，
用于演示成本推导阈值、校准与人在环策略，不是实测结果。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

# ---------------------------------------------------------------------------
# 通用数学工具（与前端 JS 引擎中的同名函数保持一致）
# ---------------------------------------------------------------------------

_LOGIT_EPS = 1e-4          # logit 的输入裁剪边界
REASON_MAX_LEN = 80        # 中文决策理由的最大字符数


def clamp(value: float, low: float, high: float) -> float:
    """把 ``value`` 限制在闭区间 ``[low, high]``。"""
    if value < low:
        return low
    if value > high:
        return high
    return value


def sigmoid(x: float) -> float:
    """数值稳定的 logistic 函数，避免 exp 溢出。"""
    if x >= 0.0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def logit(p: float) -> float:
    """log(p / (1-p))，先把 p 裁剪到 [1e-4, 1-1e-4]。"""
    q = clamp(float(p), _LOGIT_EPS, 1.0 - _LOGIT_EPS)
    return math.log(q / (1.0 - q))


def population_stddev(values: Sequence[float]) -> float:
    """总体标准差（ddof=0）；空序列返回 0。"""
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def _num(source: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    """从映射中读取数值；缺失/None/不可转换时回落到 ``default``。"""
    value = source.get(key)
    if value is None:
        return float(default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _merge_payload(
    payload: Mapping[str, Any] | None, overrides: Mapping[str, Any]
) -> dict[str, Any]:
    """支持两种调用风格：传 dict，或直接传字段关键字（关键字优先）。"""
    merged: dict[str, Any] = dict(payload) if isinstance(payload, Mapping) else {}
    merged.update(overrides)
    return merged


def _round(value: float, digits: int = 4) -> float:
    """四舍五入并消除 -0.0。"""
    rounded = round(float(value), digits)
    return 0.0 if rounded == 0 else rounded


def _clip_reason(text: str) -> str:
    """压缩空白并把中文理由裁剪到 80 字符以内。"""
    text = " ".join(str(text).split())
    if len(text) <= REASON_MAX_LEN:
        return text
    return text[: REASON_MAX_LEN - 1] + "…"


# ---------------------------------------------------------------------------
# 统一输出结构
# ---------------------------------------------------------------------------


@dataclass
class JudgerResult:
    """三个判断器共用的返回值，由 api.py 组装成响应信封。"""

    jev_type: str
    decision: str
    confidence: float
    scores: dict[str, Any] = field(default_factory=dict)
    options: list[dict[str, Any]] = field(default_factory=list)
    human_review: bool = False
    review_reasons: list[str] = field(default_factory=list)
    reason: str = ""


# ---------------------------------------------------------------------------
# 判断器 A：污染判定（jev_type = "noul"）
# ---------------------------------------------------------------------------

_CONTAMINATION_T = 1.35  # 温度缩放（temperature scaling，演示值）
_CONTAMINATION_TAU_MIN = 0.15  # 运营下限：纯成本解在 C_FP<<C_FN 时会低到不可用
_HIGH_CONFIDENCE = 0.70


def judge_contamination(
    payload: Mapping[str, Any] | None = None, **overrides: Any
) -> JudgerResult:
    """污染判定：视觉概率 + 批次先验 + 环境偏移 -> 校准概率 -> 三区间决策。

    生效阈值采用**两段式**：先由成本比算出 ``tau_cost``，再与运营下限
    ``tau_min``（默认 0.15）取大，避免 C_FP/C_FN 悬殊时把几乎每一盘都隔离。

    三区间：
    - ``p_cal >= tau_hi`` -> ``isolate_and_sample``（隔离并采样，不可逆）
    - ``p_cal >= tau_lo`` -> ``review_microscopy``（镜检复核）
    - 否则              -> ``continue``（继续培养）

    入参既可以是 dict（``judge_contamination({"vision_p": 0.3})``），也可以是
    关键字（``judge_contamination(p_raw=0.3, quality=0.99, tau_min=0.05)``）。
    """
    payload = _merge_payload(payload, overrides)
    # 视觉原始分兼容两种键名：vision_p（API 契约）/ p_raw（前端引擎）
    vision_p = _num(payload, "vision_p", _num(payload, "p_raw", 0.2))
    quality = clamp(_num(payload, "quality", 0.9), 0.0, 1.0)
    temp = _num(payload, "temp", 24.0)
    rh = _num(payload, "rh", 65.0)
    days = _num(payload, "days_in_culture", 14.0)
    hist_rate = _num(payload, "batch_hist_rate", 0.02)
    cost_fp = max(0.0, _num(payload, "cost_fp", 1.0))
    cost_fn = max(0.0, _num(payload, "cost_fn", 9.0))
    tau_min = _num(payload, "tau_min", _CONTAMINATION_TAU_MIN)

    # 批次历史先验（裁剪到 [1e-3, 0.5]，避免先验抢掉全部证据）
    prior = clamp(hist_rate, 1e-3, 0.5)
    # 图像质量决定视觉证据与批次先验的融合比例
    blend = (
        quality * logit(vision_p)
        + (1.0 - quality) * logit(prior)
        + 0.35 * (temp - 24.0) / 3.0
        + 0.25 * (rh - 65.0) / 15.0
        + 0.12 * (days - 14.0) / 7.0
    )
    p_cal = sigmoid(blend / _CONTAMINATION_T)

    # 成本推导阈值：隔离干净盘的代价 vs 漏检真实污染的代价（纯成本解）
    denominator = cost_fp + cost_fn
    cost_ratio = cost_fp / denominator if denominator > 0 else 0.02
    tau_cost = clamp(cost_ratio, 0.02, 0.5)
    # 运营下限兜底：成本比极小时也不让阈值低到不可操作
    tau_hi = clamp(max(tau_cost, tau_min), 0.02, 0.5)
    tau_lo = max(0.06, 0.45 * tau_hi)

    if p_cal >= tau_hi:
        decision = "isolate_and_sample"
    elif p_cal >= tau_lo:
        decision = "review_microscopy"
    else:
        decision = "continue"

    confidence = max(p_cal, 1.0 - p_cal)
    ood = quality < 0.55 or hist_rate == 0.0
    # 只有 continue 才可能免复核：review_microscopy 的语义就是「叫人来镜检」，
    # 漏掉它会让边界区样本返回 human_review=False，复核队列根本收不到。
    human_review = (
        decision != "continue" or confidence < _HIGH_CONFIDENCE or ood
    )

    review_reasons: list[str] = []
    if confidence < _HIGH_CONFIDENCE:
        review_reasons.append(f"置信度 {confidence:.3f} 低于 {_HIGH_CONFIDENCE:.2f}")
    if ood:
        review_reasons.append("图像质量不足或缺少批次历史基线（OOD）")
    if decision == "review_microscopy":
        review_reasons.append("污染概率落在复核区，安排镜检取证")
    if decision == "isolate_and_sample":
        review_reasons.append("隔离采样不可逆，需人工复核")

    if decision == "isolate_and_sample":
        reason = (
            f"校准后污染概率 {p_cal:.0%}，已超生效阈值 {tau_hi:.1%}"
            f"（成本解 {tau_cost:.1%} 被运营下限 {tau_min:.1%} 抬高），建议整盘隔离送检。"
        )
    elif decision == "review_microscopy":
        reason = (
            f"校准后污染概率 {p_cal:.0%} 处于复核区"
            f"（成本解 {tau_cost:.1%}，生效阈值 {tau_hi:.1%}），建议镜检复核。"
        )
    else:
        reason = (
            f"校准后污染概率 {p_cal:.0%} 低于复核阈值 {tau_lo:.1%}"
            f"（成本解 {tau_cost:.1%}，生效阈值 {tau_hi:.1%}），继续培养。"
        )

    scores = {
        "p_contaminated": _round(p_cal),
        "tau_cost": _round(tau_cost),
        "tau_hi": _round(tau_hi),
        "tau_lo": _round(tau_lo),
        "image_quality": _round(quality),
    }
    return JudgerResult(
        jev_type="noul",
        decision=decision,
        confidence=_round(confidence),
        scores=scores,
        options=[],
        human_review=human_review,
        review_reasons=review_reasons,
        reason=_clip_reason(reason),
    )


# ---------------------------------------------------------------------------
# 判断器 B：驯化 readiness（jev_type = "score"）
# ---------------------------------------------------------------------------

# 六项证据输入 -> 六个子分数，顺序与权重一一对应
EVIDENCE_KEYS: tuple[str, ...] = (
    "roots",
    "browning",
    "shoot_cm",
    "leaf_color",
    "stomata_wax",
    "water_loss_pct",
)
_READINESS_WEIGHTS: tuple[float, ...] = (0.22, 0.20, 0.10, 0.12, 0.18, 0.18)

_BAND_LABELS = {
    "transplant_ready": "可移栽",
    "delay_adjust": "延迟调整",
    "continue_acclimation": "继续驯化",
}


def _ratio_score(shoot_cm: float, roots: float) -> float:
    """株高/根数比打分：0.35–0.65 满分，偏离按带宽线性扣分。"""
    if roots <= 0.0:
        return 0.0
    ratio = shoot_cm / roots
    if 0.35 <= ratio <= 0.65:
        return 100.0
    distance = 0.35 - ratio if ratio < 0.35 else ratio - 0.65
    return clamp(100.0 - distance / 0.35 * 100.0, 0.0, 100.0)


def judge_readiness(
    payload: Mapping[str, Any] | None = None,
    supplied: Iterable[str] | None = None,
    **overrides: Any,
) -> JudgerResult:
    """驯化度打分：加权子分数 + 三道硬闸门封顶 + 置信度/人在环。

    ``supplied`` 为真实提供的证据字段集合（缺省时按 payload 中非 None 的键推断）；
    未提供的证据按 0 参与计算，并通过 ``completeness`` 拉低置信度。
    """
    payload = _merge_payload(payload, overrides)
    if supplied is None:
        supplied_keys = {key for key in EVIDENCE_KEYS if payload.get(key) is not None}
    else:
        supplied_keys = {key for key in supplied if key in EVIDENCE_KEYS}

    roots = max(0.0, _num(payload, "roots", 0.0))
    browning = max(0.0, _num(payload, "browning", 0.0))
    shoot_cm = max(0.0, _num(payload, "shoot_cm", 0.0))
    leaf_color = _num(payload, "leaf_color", 0.0)
    stomata_wax = _num(payload, "stomata_wax", 0.0)
    water_loss_pct = max(0.0, _num(payload, "water_loss_pct", 0.0))
    contamination_p = clamp(_num(payload, "contamination_p", 0.0), 0.0, 1.0)

    # 六个子分数（0..100），越界输入做防御性裁剪
    s_roots = clamp(min(100.0, roots / 12.0 * 100.0), 0.0, 100.0)
    s_brown = clamp(100.0 - browning, 0.0, 100.0)
    # 株高/根数比是「矮壮苗」指标：目标带 0.35–0.65，偏离两侧都扣分。
    # 旧写法 ratio/0.6*100 让徒长苗（ratio 1.2）拿满分，根数 0 时也给 100。
    s_ratio = _ratio_score(shoot_cm, roots)
    s_leaf = clamp(leaf_color, 0.0, 100.0)
    s_wax = clamp(stomata_wax, 0.0, 100.0)
    s_water = clamp(100.0 - water_loss_pct / 25.0 * 100.0, 0.0, 100.0)
    subscores = [s_roots, s_brown, s_ratio, s_leaf, s_wax, s_water]

    raw = sum(weight * value for weight, value in zip(_READINESS_WEIGHTS, subscores))

    # 硬闸门：违反时把分数封顶，并记录最强的封顶项用于解释
    gates: list[tuple[float, str]] = []
    if roots < 3:
        gates.append((55.0, "根系数量不足（roots<3）"))
    if browning > 60:
        gates.append((60.0, "褐化程度过高（browning>60）"))
    if contamination_p >= 0.5:
        gates.append((40.0, "污染风险过高（contamination_p≥0.5）"))
    capped = min([raw] + [cap for cap, _ in gates])
    readiness = int(round(clamp(capped, 0.0, 100.0)))

    if readiness >= 80:
        band = "transplant_ready"
    elif readiness >= 60:
        band = "delay_adjust"
    else:
        band = "continue_acclimation"

    completeness = len(supplied_keys) / len(EVIDENCE_KEYS)
    spread = population_stddev(subscores)
    confidence = clamp(
        0.62 + 0.30 * completeness - 0.35 * (spread / 50.0), 0.35, 0.97
    )

    human_review = confidence < _HIGH_CONFIDENCE or band == "transplant_ready"

    review_reasons: list[str] = []
    if confidence < _HIGH_CONFIDENCE:
        review_reasons.append(
            f"置信度 {confidence:.3f} 低于 {_HIGH_CONFIDENCE:.2f}"
            f"（证据完整度 {completeness:.0%}）"
        )
    if band == "transplant_ready":
        review_reasons.append("移栽不可逆，需人工确认")

    if gates:
        _, gate_label = min(gates)  # 封顶最严（cap 最小）的闸门最能解释结果
        reason = f"驯化度 {readiness}，判定「{_BAND_LABELS[band]}」；受限闸门：{gate_label}。"
    else:
        reason = f"驯化度 {readiness}，判定「{_BAND_LABELS[band]}」；无硬闸门触发。"

    scores = {
        "readiness": readiness,
        "contamination_risk": int(round(contamination_p * 100.0)),
        "root_health": int(round(s_roots * 0.6 + s_brown * 0.4)),
    }
    return JudgerResult(
        jev_type="score",
        decision=band,
        confidence=_round(confidence),
        scores=scores,
        options=[],
        human_review=human_review,
        review_reasons=review_reasons,
        reason=_clip_reason(reason),
    )


# ---------------------------------------------------------------------------
# 判断器 C：雾培方案选择（jev_type = "choice"）
# ---------------------------------------------------------------------------

# 维度顺序：[ec, ph, vpd, temp, do, droplet]
FOG_TARGETS: tuple[float, ...] = (1.4, 5.8, 0.9, 24.0, 6.5, 35.0)
FOG_SPANS: tuple[float, ...] = (0.8, 0.9, 0.5, 6.0, 3.0, 25.0)
FOG_RISK_WEIGHTS: tuple[float, ...] = (0.16, 0.18, 0.09, 0.24, 0.28, 0.05)
FOG_SOFTMAX_BETA = 6.0   # 仅用于展示排序概率，不用于置信度
CONF_TAU = 0.01          # 置信度尺度：σ(ΔU/τ)，ΔU 为最优与次优效用差
COSTLY_ONLY_THRESHOLD = 0.20  # 唯一可行且边际成本高于此值 → 必须人确认

# (action, 中文标签, 增量向量, cost_index, quality_penalty)
# adjust_ph 的 pH 增量依赖当前 pH，在函数内动态计算（占位 0.0）。
_FOG_OPTIONS: tuple[tuple[str, str, tuple[float, ...], float, float], ...] = (
    ("sop_baseline", "SOP 基线", (0.0, 0.0, 0.0, 0.0, 0.0, 0.0), 0.00, 0.05),
    ("lower_ec", "降低 EC", (-0.25, 0.0, 0.0, 0.0, 0.0, 0.0), 0.06, 0.12),
    ("raise_do", "提升溶氧", (0.0, 0.0, 0.0, -0.5, 1.2, 0.0), 0.18, 0.02),
    ("adjust_ph", "校正 pH", (0.0, 0.0, 0.0, 0.0, 0.0, 0.0), 0.10, 0.04),
    ("dry_back", "回干预处理", (0.1, 0.0, 0.25, 0.5, 0.0, 0.0), 0.04, 0.08),
    ("flush_reservoir", "冲洗储液", (-0.45, 0.0, 0.0, 0.0, 0.5, 0.0), 0.30, 0.18),
)

FOG_CONSTRAINT_LABELS = {
    "ec_range": "EC 需在 [0.8, 2.0]",
    "ph_range": "pH 需在 [5.3, 6.4]",
    "do_min": "溶氧需 ≥ 5.0 mg/L",
    "temp_max": "液温需 ≤ 26 ℃",
    "water_temp_max": "水温需 ≤ 24 ℃",
}


def _normalised_weights(raw: Any) -> tuple[float, float, float]:
    """把 {survival, cost, quality} 归一化到和为 1，负值按 0 处理。"""
    defaults = (0.5, 0.2, 0.3)
    if not isinstance(raw, Mapping):
        return defaults
    values: list[float] = []
    for key, fallback in zip(("survival", "cost", "quality"), defaults):
        try:
            values.append(max(0.0, float(raw.get(key, fallback))))
        except (TypeError, ValueError):
            values.append(fallback)
    total = sum(values)
    if total <= 0.0:
        return defaults
    return tuple(value / total for value in values)  # type: ignore[return-value]


def judge_fog_choice(
    payload: Mapping[str, Any] | None = None, **overrides: Any
) -> JudgerResult:
    """雾培方案选择：每个选项算效用 + 硬约束过滤 + softmax 概率。

    选项编号（action）：见 ``_FOG_OPTIONS``；全部不可行时返回 ``stop_and_review``。
    """
    payload = _merge_payload(payload, overrides)
    ec = _num(payload, "ec", 1.4)
    ph = _num(payload, "ph", 5.8)
    vpd = _num(payload, "vpd", 0.9)
    temp = _num(payload, "temp", 24.0)
    do_level = _num(
        payload, "do_mg_l", _num(payload, "do", 6.5)  # 兼容 API sensors.do
    )
    droplet = _num(payload, "droplet_um", 35.0)
    water_temp = _num(payload, "water_temp", min(temp, 22.0))
    weights = _normalised_weights(payload.get("weights"))

    current = (ec, ph, vpd, temp, do_level, droplet)

    # 液温是「整套系统」的前置状态，没有任何候选动作能改变它（靠冷水机/遮阴）。
    # 旧实现把它塞进每个选项的 violations，6 个选项同时不可行，
    # 输出变成「无解、请确认探头」，而真实原因是液温没降下来。
    zone_gates: list[str] = []
    if water_temp > 24.0:
        zone_gates.append(f"营养液 {water_temp:.1f}℃ 超 24℃")

    rows: list[dict[str, Any]] = []
    utilities: list[float] = []
    for action, label, delta, cost_index, quality_penalty in _FOG_OPTIONS:
        applied = list(delta)
        if action == "adjust_ph":
            applied[1] = (FOG_TARGETS[1] - ph) * 0.8
        post = [cur + diff for cur, diff in zip(current, applied)]

        # ---- 硬约束（作用在动作后的数值上）----
        violations: list[str] = []
        if not 0.8 <= post[0] <= 2.0:
            violations.append("ec_range")
        if not 5.3 <= post[1] <= 6.4:
            violations.append("ph_range")
        if post[4] < 5.0:
            violations.append("do_min")
        if post[3] > 26.0:
            violations.append("temp_max")

        # ---- 效用 ----
        dev = [
            clamp(abs(post_value - target) / span, 0.0, 2.0)
            for post_value, target, span in zip(post, FOG_TARGETS, FOG_SPANS)
        ]
        u_surv = 1.0 - sum(
            weight * value / 2.0 for weight, value in zip(FOG_RISK_WEIGHTS, dev)
        )
        u_cost = 1.0 - cost_index
        u_qual = 1.0 - quality_penalty
        utility = (
            weights[0] * u_surv + weights[1] * u_cost + weights[2] * u_qual
        )

        feasible = not violations
        rows.append(
            {
                "action": action,
                "label": label,
                "feasible": feasible,
                "violations": violations,
                "utility": _round(utility, 6),
                "p": 0.0,
                "components": {
                    "survival": _round(u_surv, 6),
                    "cost": _round(u_cost, 6),
                    "quality": _round(u_qual, 6),
                },
                "_post": post,
            }
        )
        utilities.append(utility)

    feasible_indices = [i for i, row in enumerate(rows) if row["feasible"]]

    # ---- 仅在可行选项上做 softmax（beta=6）----
    if feasible_indices:
        best = max(utilities[i] for i in feasible_indices)
        exponentials = {
            i: math.exp(FOG_SOFTMAX_BETA * (utilities[i] - best))
            for i in feasible_indices
        }
        total = sum(exponentials.values())
        for i, value in exponentials.items():
            rows[i]["p"] = round(value / total, 12)

        ranked = sorted((utilities[i] for i in feasible_indices), reverse=True)
        margin = ranked[0] - ranked[1] if len(ranked) > 1 else None
        recommended = max(feasible_indices, key=lambda i: utilities[i])
        recommended_row = rows[recommended]
        decision = recommended_row["action"]
        # 置信度 = σ(ΔU/τ)，不是 softmax 最大值：6 个近似打平的候选里
        # softmax 最高也只有 0.2，会把每个正常批次都推进复核队列。
        if margin is None:
            confidence = 0.88          # 约束把候选压成单选
        else:
            confidence = clamp(
                1.0 / (1.0 + math.exp(-margin / CONF_TAU)), 0.5, 0.99
            )
        post_ec, post_ph = recommended_row["_post"][0], recommended_row["_post"][1]
        best_utility = utilities[recommended]
        violations_on_choice: list[str] = recommended_row["violations"]
    else:
        decision = "stop_and_review"
        confidence = 0.0
        post_ec, post_ph = ec, ph
        best_utility = 0.0
        violations_on_choice = []
        margin: float | None = None

    only_costly = (
        margin is None
        and bool(feasible_indices)
        and next(
            (cost for action, _, _, cost, _ in _FOG_OPTIONS if action == decision),
            0.0,
        ) >= COSTLY_ONLY_THRESHOLD
    )
    human_review = (
        confidence < _HIGH_CONFIDENCE
        or not feasible_indices
        or bool(violations_on_choice)
        or bool(zone_gates)
        or only_costly
    )
    review_reasons: list[str] = []
    if zone_gates:
        review_reasons.append("前置条件未满足：" + "、".join(zone_gates))
    if not feasible_indices:
        review_reasons.append("无满足硬约束的方案，停止自动执行")
    if only_costly:
        review_reasons.append("约束只剩一个高成本动作，需人工确认成本")
    elif confidence < _HIGH_CONFIDENCE:
        review_reasons.append(f"推荐方案概率 {confidence:.3f} 低于 {_HIGH_CONFIDENCE:.2f}")
    if violations_on_choice:
        review_reasons.append("所选方案违反硬约束")

    if zone_gates:
        reason = (
            f"先处理前置条件：{'、'.join(zone_gates)}；此时不建议任何雾化动作。"
        )
        decision = "stop_and_review"
        confidence = 0.0
    elif not feasible_indices:
        reason = "无任何方案满足 EC/pH/DO/温度硬约束，停止执行并转人工复核。"
    else:
        edge = f"领先次优 {margin:.3f}" if margin is not None else "唯一可行动作"
        reason = (
            f"推荐「{recommended_row['label']}」（{decision}）："
            f"效用 {best_utility:.3f}，{edge}，置信 {confidence:.2f}。"
        )

    # 对外输出去掉内部字段 _post
    options = [
        {key: value for key, value in row.items() if not key.startswith("_")}
        for row in rows
    ]
    scores = {
        "utility": _round(best_utility),
        "post_ec": _round(post_ec),
        "post_ph": _round(post_ph),
        "margin": None if margin is None else _round(margin),
        "zone_gates": list(zone_gates),
    }
    return JudgerResult(
        jev_type="choice",
        decision=decision,
        confidence=_round(confidence),
        scores=scores,
        options=options,
        human_review=human_review,
        review_reasons=review_reasons,
        reason=_clip_reason(reason),
    )


# ---------------------------------------------------------------------------
# 判断器注册表与 stage 路由（api.py 复用）
# ---------------------------------------------------------------------------

JEV_TYPES: dict[str, str] = {
    "contamination": "noul",
    "readiness": "score",
    "fog_choice": "choice",
}

JUDGERS = {
    "contamination": judge_contamination,
    "readiness": judge_readiness,
    "fog_choice": judge_fog_choice,
}

STAGE_ROUTES: dict[str, str] = {
    # 组培无菌阶段 -> 污染判定
    "aseptic_establishment": "contamination",
    "callus": "contamination",
    "proliferation": "contamination",
    "rooting_check": "contamination",
    "root_zone_check": "contamination",
    # 生根/驯化阶段 -> 驯化度打分
    "rooting": "readiness",
    "acclimation": "readiness",
    "rooting_to_aeroponics": "readiness",
    # 雾培营养/移栽闸门/采收窗口 -> 方案选择
    "aeroponics_nutrition": "fog_choice",
    "transplant_gate": "fog_choice",
    "harvest_window": "fog_choice",
}
