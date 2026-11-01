"""CoffeeJeV 参考后端 HTTP 服务（纯标准库）。

端点：
    POST /coffee-jev/decide   决策入口（按 stage 路由到三个判断器）
    GET  /health              健康检查
    GET  /coffee-jev/audit    审计账本（最近 50 条）与哈希链校验

运行：
    python coffeejev/service/api.py            # 默认 http://127.0.0.1:8791
    PORT=9000 python coffeejev/service/api.py  # 覆盖端口

响应全部为 UTF-8 中文可读 JSON；数值为演示性设计目标，不是实测结果。
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:  # 支持 python -m unittest discover 与直接运行两种方式
    sys.path.insert(0, _HERE)

import judgers  # noqa: E402  （需在 sys.path 调整之后导入）

# ---------------------------------------------------------------------------
# 常量与契约
# ---------------------------------------------------------------------------

AGENT = "CoffeeJeV"
VERSION = "1.0.0"
SOP_VERSION = "coffee-tc-aero-v1.0"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8791
MAX_BODY_BYTES = 1 << 20  # 1 MiB

# 判断器专用字段的默认值（reading / sensors / batch_history / costs 缺失时使用）
CONTAMINATION_DEFAULTS = {
    "vision_p": 0.2,
    "quality": 0.9,
    "rh": 65.0,
    "days_in_culture": 14.0,
    "batch_hist_rate": 0.02,
    "cost_fp": 1.0,
    "cost_fn": 9.0,
    "tau_min": 0.15,
}
READINESS_DEFAULTS = {
    "roots": 4.0,
    "browning": 20.0,
    "shoot_cm": 2.0,
    "leaf_color": 70.0,
    "stomata_wax": 70.0,
    "water_loss_pct": 8.0,
    "contamination_p": 0.0,
}
FOG_DEFAULT_WEIGHTS = {"survival": 0.5, "cost": 0.2, "quality": 0.3}

REQUIRED_SENSOR_KEYS = ("ec", "ph", "vpd", "temp")

# ---------------------------------------------------------------------------
# 审计账本：append-only + sha256(prev + json.dumps(payload, sort_keys=True))
# ---------------------------------------------------------------------------


class AuditLedger:
    """进程内不可变审计链：每条记录的 hash 绑定上一条 hash 与自身 payload。"""

    GENESIS = "0" * 64

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: list[dict[str, Any]] = []
        self._payloads: list[dict[str, Any]] = []

    @staticmethod
    def _digest(prev_hash: str, payload: Mapping[str, Any]) -> str:
        canonical = json.dumps(payload, sort_keys=True)
        return hashlib.sha256((prev_hash + canonical).encode("utf-8")).hexdigest()

    def append(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """追加一条记录并返回账本条目（含 seq/ts/audit_id/prev/hash）。"""
        with self._lock:
            seq = len(self._entries) + 1
            prev_hash = self._entries[-1]["hash"] if self._entries else self.GENESIS
            stored = dict(payload)
            audit_id = str(stored.get("audit_id") or uuid.uuid4().hex)
            entry = {
                "seq": seq,
                "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                "audit_id": audit_id,
                "prev": prev_hash,
                "hash": self._digest(prev_hash, stored),
            }
            self._entries.append(entry)
            self._payloads.append(stored)
            return entry

    def entries(self, limit: int = 50) -> list[dict[str, Any]]:
        """返回最近 ``limit`` 条记录（含 payload，便于离线复算哈希）。"""
        with self._lock:
            if limit <= 0:
                return []
            start = max(0, len(self._entries) - limit)
            rows = []
            for index in range(start, len(self._entries)):
                row = dict(self._entries[index])
                row["payload"] = dict(self._payloads[index])
                rows.append(row)
            return rows

    def verify_chain(self) -> bool:
        """从头复算整条链；任一 prev 或 hash 不匹配即返回 False。"""
        with self._lock:
            prev_hash = self.GENESIS
            for entry, payload in zip(self._entries, self._payloads):
                if entry["prev"] != prev_hash:
                    return False
                if self._digest(entry["prev"], payload) != entry["hash"]:
                    return False
                prev_hash = entry["hash"]
            return True


LEDGER = AuditLedger()

# ---------------------------------------------------------------------------
# 请求校验与字段收集
# ---------------------------------------------------------------------------


@dataclass
class JudgerInputs:
    """判断器入参 + 被默认值填充的字段清单 + 真实提供的证据字段。"""

    values: dict[str, Any] = field(default_factory=dict)
    defaulted: list[str] = field(default_factory=list)
    supplied: set[str] = field(default_factory=set)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _is_number(value: Any) -> bool:
    """JSON 数字（排除 bool）且有限。"""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(float(value))


def _coercible(value: Any) -> bool:
    if value is None or isinstance(value, bool):
        return False
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _pick_float(
    default_args: JudgerInputs,
    label: str,
    default: float,
    sources: Sequence[tuple[Mapping[str, Any], str]],
) -> float:
    """按顺序从 (来源, 键) 读取数值；全部缺失时登记 defaulted 并返回默认值。"""
    for source, key in sources:
        value = source.get(key)
        if not _coercible(value):
            continue
        return float(value)
    default_args.defaulted.append(label)
    return float(default)


# 每个判断器真正需要的传感器：组培瓶里没有 EC/pH 探头，
# 用「全都必须」的规则会把真实的无菌检查请求误判成 need_more_info。
REQUIRED_BY_JUDGER: dict[str, tuple[str, ...]] = {
    "contamination": ("temp",),
    "readiness": (),            # 依赖 reading 里的形态学读数，见下
    "fog_choice": ("ec", "ph", "vpd", "temp"),
}

READINESS_EVIDENCE_KEYS = (
    "roots", "browning", "shoot_cm", "leaf_color", "stomata_wax", "water_loss_pct",
)


def _validate_request(payload: Mapping[str, Any], judger_name: str | None = None) -> list[str]:
    """返回缺失/非法的必填字段列表（空列表表示通过）。"""
    missing: list[str] = []
    for key in ("variety", "region", "stage"):
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            missing.append(key)
    sensors = payload.get("sensors")
    if not isinstance(sensors, Mapping):
        missing.append("sensors")
    else:
        for key in REQUIRED_BY_JUDGER.get(judger_name or "", REQUIRED_SENSOR_KEYS):
            if not _is_number(sensors.get(key)):
                missing.append(f"sensors.{key}")
    if judger_name == "readiness" and not missing:
        reading = _as_mapping(payload.get("reading"))
        if not any(_is_number(reading.get(key)) for key in READINESS_EVIDENCE_KEYS):
            missing.append("reading(roots/browning/…)")
    return missing


def _build_contamination_inputs(payload: Mapping[str, Any]) -> JudgerInputs:
    inputs = JudgerInputs()
    sensors = _as_mapping(payload.get("sensors"))
    reading = _as_mapping(payload.get("reading"))
    history = _as_mapping(payload.get("batch_history"))
    costs = _as_mapping(payload.get("costs"))
    params = _as_mapping(payload.get("params"))
    defaults = CONTAMINATION_DEFAULTS

    inputs.values = {
        # 兼容前端引擎的 p_raw 键名
        "vision_p": _pick_float(
            inputs, "reading.vision_p", defaults["vision_p"],
            ((reading, "vision_p"), (reading, "p_raw")),
        ),
        "quality": _pick_float(inputs, "reading.quality", defaults["quality"],
                               ((reading, "quality"),)),
        "temp": _pick_float(inputs, "sensors.temp", 24.0, ((sensors, "temp"),)),
        "rh": _pick_float(inputs, "sensors.rh", defaults["rh"], ((sensors, "rh"),)),
        "days_in_culture": _pick_float(
            inputs, "sensors.days_in_culture", defaults["days_in_culture"],
            ((sensors, "days_in_culture"), (reading, "days_in_culture")),
        ),
        "batch_hist_rate": _pick_float(
            inputs, "batch_history.contamination_rate", defaults["batch_hist_rate"],
            ((history, "contamination_rate"),),
        ),
        "cost_fp": _pick_float(inputs, "costs.fp", defaults["cost_fp"],
                               ((costs, "fp"),)),
        "cost_fn": _pick_float(inputs, "costs.fn", defaults["cost_fn"],
                               ((costs, "fn"),)),
        # 运营下限：costs.tau_min 优先，其次 params.tau_min，缺省 0.15
        "tau_min": _pick_float(
            inputs, "costs.tau_min", defaults["tau_min"],
            ((costs, "tau_min"), (params, "tau_min")),
        ),
    }
    return inputs


def _build_readiness_inputs(payload: Mapping[str, Any]) -> JudgerInputs:
    inputs = JudgerInputs()
    reading = _as_mapping(payload.get("reading"))
    defaults = READINESS_DEFAULTS

    # completeness 只统计「真实提供」的六项证据，默认值不算证据
    inputs.supplied = {
        key for key in judgers.EVIDENCE_KEYS if _coercible(reading.get(key))
    }
    inputs.values = {
        key: _pick_float(inputs, f"reading.{key}", defaults[key], ((reading, key),))
        for key in judgers.EVIDENCE_KEYS
    }
    inputs.values["contamination_p"] = _pick_float(
        inputs, "reading.contamination_p", defaults["contamination_p"],
        ((reading, "contamination_p"),),
    )
    return inputs


def _weights_from_objective(objective: Any) -> tuple[dict[str, float], bool]:
    """从 objective 提取 {survival, cost, quality}；返回 (权重, 是否使用默认值)。"""
    if isinstance(objective, Mapping):
        candidate = objective.get("weights")
        if not isinstance(candidate, Mapping):
            if all(key in objective for key in ("survival", "cost", "quality")):
                candidate = objective
            else:
                candidate = None
        if isinstance(candidate, Mapping):
            weights: dict[str, float] = {}
            for key in ("survival", "cost", "quality"):
                value = candidate.get(key)
                if not _coercible(value):
                    continue
                weights[key] = float(value)
            if weights:
                return weights, False
    return dict(FOG_DEFAULT_WEIGHTS), True


def _build_fog_inputs(payload: Mapping[str, Any]) -> JudgerInputs:
    inputs = JudgerInputs()
    sensors = _as_mapping(payload.get("sensors"))
    reading = _as_mapping(payload.get("reading"))

    temp = _pick_float(inputs, "sensors.temp", 24.0, ((sensors, "temp"),))
    inputs.values = {
        "ec": _pick_float(inputs, "sensors.ec", 1.4, ((sensors, "ec"),)),
        "ph": _pick_float(inputs, "sensors.ph", 5.8, ((sensors, "ph"),)),
        "vpd": _pick_float(inputs, "sensors.vpd", 0.9, ((sensors, "vpd"),)),
        "temp": temp,
        "do_mg_l": _pick_float(
            inputs, "sensors.do", 6.5,
            ((sensors, "do"), (reading, "do_mg_l"), (reading, "do")),
        ),
        "droplet_um": _pick_float(
            inputs, "sensors.droplet_um", 35.0,
            ((sensors, "droplet_um"), (reading, "droplet_um")),
        ),
        "water_temp": _pick_float(
            inputs, "sensors.water_temp", min(temp, 22.0),
            ((sensors, "water_temp"), (reading, "water_temp")),
        ),
    }
    weights, used_default = _weights_from_objective(payload.get("objective"))
    inputs.values["weights"] = weights
    if used_default:
        inputs.defaulted.append("objective.weights")
    return inputs


def _build_inputs(judger_name: str, payload: Mapping[str, Any]) -> JudgerInputs:
    if judger_name == "contamination":
        return _build_contamination_inputs(payload)
    if judger_name == "readiness":
        return _build_readiness_inputs(payload)
    return _build_fog_inputs(payload)


# ---------------------------------------------------------------------------
# 响应信封
# ---------------------------------------------------------------------------


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 2)


def _evidence_refs(payload: Mapping[str, Any]) -> list[str]:
    ref = payload.get("image_ref")
    return [ref] if isinstance(ref, str) and ref.strip() else []


def _new_envelope(
    stage: str,
    jev_type: str,
    mode: str,
    evidence_refs: list[str],
) -> dict[str, Any]:
    """按契约顺序创建信封骨架，后续按键赋值不改变顺序。"""
    return {
        "agent": AGENT,
        "version": VERSION,
        "stage": stage,
        "jev_type": jev_type,
        "decision": "",
        "confidence": 0.0,
        "scores": {},
        "options": [],
        "human_review": True,
        "review_reasons": [],
        "reason": "",
        "sop_version": SOP_VERSION,
        "evidence_refs": evidence_refs,
        "latency_ms": 0.0,
        "model_ids": {},
        "audit_id": "",
        "mode": mode,
    }


def _finalise(
    envelope: dict[str, Any],
    mode: str,
    started: float,
) -> dict[str, Any]:
    """补齐 latency/audit_id，写入审计链，并按 shadow 模式补充字段。"""
    envelope["latency_ms"] = _elapsed_ms(started)
    envelope["audit_id"] = uuid.uuid4().hex
    if mode == "shadow":
        envelope["would_decide"] = envelope["decision"]
        envelope["executed"] = False
    LEDGER.append(envelope)
    return envelope


def _need_more_info(
    payload: Mapping[str, Any],
    stage: str,
    judger_name: str | None,
    missing: list[str],
    mode: str,
    started: float,
    unknown_stage: bool,
) -> dict[str, Any]:
    if unknown_stage:
        reason = f"无法判定：stage={stage!r} 不在路由表内，请检查请求。"
    else:
        reason = (
            f"无法判定：缺少或非法字段 {', '.join(missing)}，请补充后重试。"
        )
    envelope = _new_envelope(
        stage=stage,
        jev_type=judgers.JEV_TYPES.get(judger_name or "", "unknown"),
        mode=mode,
        evidence_refs=_evidence_refs(payload),
    )
    envelope.update(
        {
            "decision": "need_more_info",
            "confidence": 0.0,
            "scores": {},
            "options": [],
            "human_review": True,
            "review_reasons": ["请求校验未通过"],
            "reason": judgers._clip_reason(reason),
            "missing": missing,
        }
    )
    return _finalise(envelope, mode, started)


def decide(payload: Any) -> dict[str, Any]:
    """核心决策函数：校验 -> 路由 -> 判断器 -> 响应信封（可直接单测调用）。"""
    started = time.perf_counter()
    if not isinstance(payload, Mapping):
        payload = {}

    stage_value = payload.get("stage")
    stage = stage_value.strip() if isinstance(stage_value, str) else ""
    mode_value = payload.get("mode")
    mode = "shadow" if str(mode_value or "live").strip().lower() == "shadow" else "live"

    judger_name = judgers.STAGE_ROUTES.get(stage)
    missing = _validate_request(payload, judger_name)
    unknown_stage = False
    if not missing and judger_name is None:
        missing.append("stage")
        unknown_stage = True
    if missing:
        return _need_more_info(
            payload, stage, judger_name, missing, mode, started, unknown_stage
        )

    assert judger_name is not None  # 校验通过后必然有路由
    inputs = _build_inputs(judger_name, payload)
    if judger_name == "readiness":
        result = judgers.judge_readiness(inputs.values, supplied=inputs.supplied)
    else:
        result = judgers.JUDGERS[judger_name](inputs.values)

    envelope = _new_envelope(
        stage=stage,
        jev_type=result.jev_type,
        mode=mode,
        evidence_refs=_evidence_refs(payload),
    )
    envelope.update(
        {
            "decision": result.decision,
            "confidence": result.confidence,
            "scores": result.scores,
            "options": result.options,
            "human_review": bool(result.human_review),
            "review_reasons": list(result.review_reasons),
            "reason": result.reason,
        }
    )
    if inputs.defaulted:
        envelope["defaulted"] = inputs.defaulted
    return _finalise(envelope, mode, started)


# ---------------------------------------------------------------------------
# HTTP 处理
# ---------------------------------------------------------------------------


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


class CoffeeJevHandler(BaseHTTPRequestHandler):
    """极简路由：3 个端点 + CORS 预检；协议用 HTTP/1.0 避免连接复用挂起。"""

    server_version = f"CoffeeJeV/{VERSION}"
    protocol_version = "HTTP/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: D401
        """默认静默；设置环境变量 COFFEEJEV_LOG=1 时打印访问日志。"""
        if os.environ.get("COFFEEJEV_LOG"):
            super().log_message(fmt, *args)

    # -- 基础工具 ---------------------------------------------------------
    def _send_json(self, status: int, payload: Any) -> None:
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def _path(self) -> str:
        path = urlsplit(self.path).path
        return path.rstrip("/") or "/"

    # -- 路由 -------------------------------------------------------------
    def do_OPTIONS(self) -> None:  # noqa: N802 （BaseHTTPRequestHandler 约定）
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = self._path()
        if path == "/health":
            self._send_json(
                200,
                {
                    "status": "ok",
                    "judgers": ["contamination", "readiness", "fog_choice"],
                    "sop_version": SOP_VERSION,
                },
            )
            return
        if path == "/coffee-jev/audit":
            self._send_json(
                200,
                {"entries": LEDGER.entries(50), "chain_valid": LEDGER.verify_chain()},
            )
            return
        self._send_json(404, {"error": "not_found", "path": path})

    def do_POST(self) -> None:  # noqa: N802
        path = self._path()
        if path != "/coffee-jev/decide":
            self._send_json(404, {"error": "not_found", "path": path})
            return

        try:
            length = int(self.headers.get("Content-Length") or 0)
        except (TypeError, ValueError):
            length = 0
        if length > MAX_BODY_BYTES:
            self._send_json(413, {"error": "request_too_large"})
            return
        raw = self.rfile.read(length) if length > 0 else b""
        try:
            # utf-8-sig：容忍 Windows 工具链常见的 UTF-8 BOM
            payload = json.loads(raw.decode("utf-8-sig")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._send_json(
                400, {"error": "invalid_json", "detail": str(exc)}
            )
            return
        if not isinstance(payload, Mapping):
            self._send_json(400, {"error": "body_must_be_json_object"})
            return

        try:
            response = decide(payload)
        except Exception as exc:  # 防御性兜底：任何判断器异常都返回结构化错误
            self._send_json(
                500,
                {"agent": AGENT, "version": VERSION, "error": "internal_error",
                 "detail": str(exc)},
            )
            return
        self._send_json(200, response)


def make_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    """创建服务器（测试时传 port=0 获取临时端口）。"""
    server = ThreadingHTTPServer((host, int(port)), CoffeeJevHandler)
    server.daemon_threads = True
    return server


def _force_utf8_stdout() -> None:
    """Windows 控制台下尽量保证中文输出为 UTF-8。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError, OSError):
            pass


def main() -> None:
    _force_utf8_stdout()
    host = os.environ.get("HOST", DEFAULT_HOST).strip() or DEFAULT_HOST
    try:
        port = int(os.environ.get("PORT", str(DEFAULT_PORT)))
    except ValueError:
        port = DEFAULT_PORT
    server = make_server(host, port)
    bound_host, bound_port = server.server_address[0], server.server_address[1]
    print(f"CoffeeJeV 参考后端已启动：http://{bound_host}:{bound_port}", flush=True)
    print("  POST /coffee-jev/decide", flush=True)
    print("  GET  /health", flush=True)
    print("  GET  /coffee-jev/audit", flush=True)
    print("Ctrl+C 停止。", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCoffeeJeV 参考后端已停止。", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
