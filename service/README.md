# CoffeeJeV 参考后端服务（`coffeejev/service/`）

CoffeeJeV（咖啡快判官）决策层的 **Python 参考实现**：面向气雾栽培（雾培）+ 组培咖啡，
把「污染判定 / 驯化度打分 / 雾培方案选择」三个判断器包装成 HTTP 服务，并附带
sha256 哈希链审计账本、人在环（human-in-the-loop）复核与 shadow 影子模式。

本实现与前端 `coffeejev/index.html` 内的 JS 引擎**同口径**（公式、常量、枚举一致），
用于交叉验证与后端集成；只依赖 Python 3.11+ 标准库，**不需要 pip 安装任何东西**。

> ⚠️ **数值说明**：文中所有阈值、权重、系数（如 T=1.35、τ_min=0.15、readiness≥80 等）
> 都是**演示性设计目标**，用于展示「成本推导阈值 + 校准 + 人在环」的决策方法，
> **不是实测数据或田间实验结果**。上线前必须用自有数据重新标定。

---

## 1. 目录与文件

| 文件 | 作用 |
| --- | --- |
| `judgers.py` | 三个判断器的纯函数实现（无 I/O、可单测）+ stage 路由表 |
| `api.py` | `http.server.ThreadingHTTPServer` 路由、请求校验、响应信封、审计哈希链 |
| `test_judgers.py` | `unittest` 测试：单调性、三区间、硬闸门、约束可行性、API 契约 |
| `__init__.py` | 空包声明；让 `python -m unittest discover -s coffeejev/service -t .` 能导入本目录 |
| `README.md` | 本文档 |

严格边界：本目录之外的文件不属于本服务（尤其 **不要修改 `coffeejev/index.html`**）。

---

## 2. 运行

```bash
# 在工作区根目录执行，默认 http://127.0.0.1:8791
python coffeejev/service/api.py

# 覆盖端口 / 监听地址
PORT=9000 python coffeejev/service/api.py
HOST=0.0.0.0 PORT=9000 python coffeejev/service/api.py
```

PowerShell 写法：`$env:PORT=9000; python coffeejev/service/api.py`。
访问日志默认关闭（`COFFEEJEV_LOG=1` 打开）；Ctrl+C 停止。
服务返回的 JSON 一律 `ensure_ascii=False` + UTF-8，中文可直接阅读。

### 2.1 一次性自检（启动 + 请求 + 停止）

```bash
python coffeejev/service/api.py &
curl -s http://127.0.0.1:8791/health
kill %1
```

---

## 3. 端点

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/coffee-jev/decide` | 决策入口：按 `stage` 路由到判断器 |
| `GET` | `/health` | 健康检查，返回判断器清单与 SOP 版本 |
| `GET` | `/coffee-jev/audit` | 最近 50 条审计记录 + `chain_valid` 哈希链校验 |

另有 CORS 预检 `OPTIONS`（便于前端直接调用）与 404/400/413 结构化错误。

### 3.1 污染判定（stage = `aseptic_establishment` 等）

```bash
curl -s -X POST http://127.0.0.1:8791/coffee-jev/decide \
  -H "Content-Type: application/json" \
  -d '{
    "variety": "Caturra",
    "region": "云南保山",
    "stage": "aseptic_establishment",
    "sensors": {"ec": 1.4, "ph": 5.8, "vpd": 0.9, "temp": 24.0,
                "rh": 68.0, "do": 6.5, "droplet_um": 35.0,
                "water_temp": 20.0, "days_in_culture": 10},
    "image_ref": "evidence/tray-042.jpg",
    "batch_history": {"contamination_rate": 0.08},
    "costs": {"fp": 40, "fn": 900, "tau_min": 0.15},
    "mode": "live",
    "reading": {"vision_p": 0.62, "quality": 0.88}
  }'
```

### 3.2 驯化度打分（stage = `rooting` / `acclimation` / `rooting_to_aeroponics`）

```bash
curl -s -X POST http://127.0.0.1:8791/coffee-jev/decide \
  -H "Content-Type: application/json" \
  -d '{
    "variety": "Caturra",
    "region": "云南保山",
    "stage": "acclimation",
    "sensors": {"ec": 1.4, "ph": 5.8, "vpd": 0.9, "temp": 24.0, "rh": 68.0,
                "do": 6.5, "droplet_um": 35.0, "water_temp": 20.0,
                "days_in_culture": 21},
    "reading": {"roots": 12, "browning": 15, "shoot_cm": 6,
                "leaf_color": 90, "stomata_wax": 88,
                "water_loss_pct": 6, "contamination_p": 0.05}
  }'
```

### 3.3 雾培方案选择（stage = `aeroponics_nutrition` / `transplant_gate` / `harvest_window`）

```bash
curl -s -X POST http://127.0.0.1:8791/coffee-jev/decide \
  -H "Content-Type: application/json" \
  -d '{
    "variety": "Caturra",
    "region": "云南保山",
    "stage": "aeroponics_nutrition",
    "sensors": {"ec": 1.4, "ph": 5.8, "vpd": 0.9, "temp": 24.0, "rh": 68.0,
                "do": 6.5, "droplet_um": 35.0, "water_temp": 20.0},
    "objective": {"weights": {"survival": 0.5, "cost": 0.2, "quality": 0.3}},
    "mode": "shadow"
  }'
```

### 3.4 缺字段 -> `need_more_info`

```bash
curl -s -X POST http://127.0.0.1:8791/coffee-jev/decide \
  -H "Content-Type: application/json" \
  -d '{"stage": "callus", "sensors": {"ec": 1.4, "ph": 5.8, "vpd": 0.9}}'
# => {"decision":"need_more_info","missing":["variety","region","sensors.temp"],...}
```

### 3.5 健康检查与审计

```bash
curl -s http://127.0.0.1:8791/health
curl -s http://127.0.0.1:8791/coffee-jev/audit
```

> 中文请求体建议先保存为 UTF-8 文件，再用 `curl --data-binary "@req.json"`；
> Windows 下请用 `curl.exe`（PowerShell 的 `curl` 是 `Invoke-WebRequest` 别名）。

---

## 4. 请求字段契约

`POST /coffee-jev/decide` 的请求体：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `variety` | string | ✅ | 品种，非空 |
| `region` | string | ✅ | 产区，非空 |
| `stage` | string | ✅ | 决策节点，决定路由（见 4.1），未知值返回 `need_more_info` |
| `sensors` | object | ✅ | 传感器读数；其中 `ec/ph/vpd/temp` 必须是数字 |
| `sensors.rh` | number | | 相对湿度 %，缺省 65 |
| `sensors.do` | number | | 溶氧 mg/L，缺省 6.5（雾培选择用） |
| `sensors.droplet_um` | number | | 雾滴粒径 μm，缺省 35 |
| `sensors.water_temp` | number | | 水温 ℃，缺省 `min(temp, 22)` |
| `sensors.days_in_culture` | number | | 继代天数，缺省 14 |
| `image_ref` | string | | 图像证据引用，非空时进入 `evidence_refs` |
| `batch_history.contamination_rate` | number | | 批次历史污染率 0..1，缺省 0.02 |
| `costs.fp` | number | | 隔离一个干净盘的代价，缺省 1.0 |
| `costs.fn` | number | | 漏检一个真实污染的代价，缺省 9.0 |
| `costs.tau_min` / `params.tau_min` | number | | 污染阈值运营下限，缺省 0.15 |
| `objective.weights` | object | | `{survival, cost, quality}`，缺省 0.5 / 0.2 / 0.3 |
| `mode` | string | | `live`（默认）或 `shadow` |
| `reading` | object | | 判断器专用字段（见 4.1）；整体缺失时用默认值并回填 `defaulted` |

### 4.1 stage 路由与判断器专用字段

| stage | 判断器 | `jev_type` | `reading` 字段（缺省值） |
| --- | --- | --- | --- |
| `aseptic_establishment` / `callus` / `proliferation` / `rooting_check` / `root_zone_check` | contamination | `noul` | `vision_p`(0.2，兼容 `p_raw`)、`quality`(0.9) |
| `rooting` / `acclimation` / `rooting_to_aeroponics` | readiness | `score` | `roots`(4)、`browning`(20)、`shoot_cm`(2)、`leaf_color`(70)、`stomata_wax`(70)、`water_loss_pct`(8)、`contamination_p`(0) |
| `aeroponics_nutrition` / `transplant_gate` / `harvest_window` | fog_choice | `choice` | `do_mg_l`(← `sensors.do`)、`droplet_um`(← `sensors.droplet_um`)、`water_temp`(← `sensors.water_temp`) |

判断器专用字段缺失时，服务使用上表默认值，并在响应中追加
`"defaulted": ["reading.vision_p", ...]`。`reading` 中真实提供的六项证据
（roots/browning/shoot_cm/leaf_color/stomata_wax/water_loss_pct）参与 readiness 的
`completeness` 计算；默认值不算证据，会拉低置信度并触发人工复核。

---

## 5. 响应信封

成功决策（`mode=live`）的键固定为：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `agent` | string | 固定 `"CoffeeJeV"` |
| `version` | string | 固定 `"1.0.0"` |
| `stage` | string | 回显请求 stage |
| `jev_type` | string | `noul` / `score` / `choice`（校验失败时为 `unknown`） |
| `decision` | string | 判断器输出枚举（见 5.1） |
| `confidence` | number | 0..1，4 位小数 |
| `scores` | object | 关键量化指标（判断器相关） |
| `options` | array | 仅 choice 判断器给出候选方案，其余为 `[]` |
| `human_review` | bool | 是否必须人工复核 |
| `review_reasons` | array | 中文复核原因列表 |
| `reason` | string | 中文决策理由，≤80 字符 |
| `sop_version` | string | 固定 `"coffee-tc-aero-v1.0"` |
| `evidence_refs` | array | 图像等证据引用（来自 `image_ref`） |
| `latency_ms` | number | 服务端处理耗时（毫秒） |
| `model_ids` | object | 模型标识占位（当前 `{}`，便于以后挂多模型） |
| `audit_id` | string | 审计记录 id（同时写入哈希链） |
| `mode` | string | `live` / `shadow` |

条件字段：

- `missing`: `["variety", ...]` —— 仅 `need_more_info` 时出现；
- `defaulted`: `[...]` —— 仅使用了默认值时出现（非空才出现）；
- `would_decide` / `executed: false` —— 仅 `shadow` 模式，影子决策不执行。

### 5.1 决策枚举

| 判断器 | decision 取值 |
| --- | --- |
| contamination | `isolate_and_sample` / `review_microscopy` / `continue` |
| readiness | `transplant_ready` / `delay_adjust` / `continue_acclimation` |
| fog_choice | 选项 id：`sop_baseline` / `lower_ec` / `raise_do` / `adjust_ph` / `dry_back` / `flush_reservoir`；全部不可行时 `stop_and_review` |

### 5.2 示例（污染判定，摘要）

```json
{
  "agent": "CoffeeJeV",
  "version": "1.0.0",
  "stage": "aseptic_establishment",
  "jev_type": "noul",
  "decision": "isolate_and_sample",
  "confidence": 0.5221,
  "scores": {"p_contaminated": 0.5221, "tau_cost": 0.0426,
             "tau_hi": 0.15, "tau_lo": 0.0675, "image_quality": 0.88},
  "options": [],
  "human_review": true,
  "review_reasons": ["置信度 0.522 低于 0.70", "隔离采样不可逆，需人工复核"],
  "reason": "校准后污染概率 52%，已超生效阈值 15.0%（成本解 4.3% 被运营下限 15.0% 抬高），建议整盘隔离送检。",
  "sop_version": "coffee-tc-aero-v1.0",
  "evidence_refs": ["evidence/tray-042.jpg"],
  "latency_ms": 0.22,
  "model_ids": {},
  "audit_id": "7692998fd3ba4ef69b021dfaddd7d4df",
  "mode": "live"
}
```

---

## 6. 判断器数学契约

### 6.1 contamination（jev_type `noul`）

```
prior     = clamp(batch_hist_rate, 1e-3, 0.5)
blend     = quality*logit(vision_p) + (1-quality)*logit(prior)
            + 0.35*(temp-24)/3 + 0.25*(rh-65)/15 + 0.12*(days_in_culture-14)/7
p_cal     = sigmoid(blend / 1.35)
tau_cost  = clamp(cost_fp/(cost_fp+cost_fn), 0.02, 0.5)     # 纯成本解
tau_min   = 0.15（默认，可用 costs.tau_min / params.tau_min 覆盖）
tau_hi    = clamp(max(tau_cost, tau_min), 0.02, 0.5)        # 生效阈值
tau_lo    = max(0.06, 0.45*tau_hi)
decision  = p_cal>=tau_hi ? isolate_and_sample
          : p_cal>=tau_lo ? review_microscopy : continue
confidence = max(p_cal, 1-p_cal)
ood        = quality < 0.55 或 batch_hist_rate == 0
human_review = confidence<0.70 或 ood 或 decision==isolate_and_sample
```

**两段式阈值**：纯成本比在 `C_FP` 远小于 `C_FN` 时会给出极低阈值（如 40:900 得 4.3%），
几乎每盘都隔离、不可操作；因此叠加运营下限 `tau_min`（默认 15%）。`scores` 同时输出
`tau_cost`（成本解）与 `tau_hi`（生效值），前端可展示「阈值被下限抬高」的解释。

### 6.2 readiness（jev_type `score`）

| 子分数 | 公式 | 闸门 |
| --- | --- | --- |
| `s_roots` | `min(100, roots/12*100)` | `roots < 3` → 总分 ≤55 |
| `s_brown` | `100 - browning` | `browning > 60` → 总分 ≤60 |
| `s_ratio` | `clamp((shoot_cm/max(roots,1))/0.6*100, 0, 100)` | — |
| `s_leaf` | `leaf_color` | — |
| `s_wax` | `stomata_wax` | — |
| `s_water` | `clamp(100 - water_loss_pct/25*100, 0, 100)` | — |

```
raw = 0.22*s_roots + 0.20*s_brown + 0.10*s_ratio + 0.12*s_leaf + 0.18*s_wax + 0.18*s_water
readiness = round(min(raw, 闸门封顶))            # 0..100
band = readiness>=80 ? transplant_ready : readiness>=60 ? delay_adjust : continue_acclimation
completeness = 六项证据中真实提供的比例
sd = 六个子分数的总体标准差（ddof=0）
confidence = clamp(0.62 + 0.30*completeness - 0.35*(sd/50), 0.35, 0.97)
human_review = confidence<0.70 或 band==transplant_ready   # 移栽不可逆，必人工
```

### 6.3 fog_choice（jev_type `choice`）

维度顺序 `[ec, ph, vpd, temp, do, droplet]`；目标 `[1.4, 5.8, 0.9, 24, 6.5, 35]`，
容差 `[0.8, 0.9, 0.5, 6, 3.0, 25]`，风险权重 `do .28 / temp .24 / ph .18 / ec .16 / vpd .09 / droplet .05`。

| action | 增量（ec, ph, vpd, temp, do, droplet） | cost_index | quality_penalty |
| --- | --- | --- | --- |
cost_index 是**相对 SOP 的边际成本**：维持 = 0，改配方/停机才是额外支出。
（旧版给 SOP 基线挂 0.30、dry_back 只挂 0.12，导致「最便宜的任意动作」总是赢，
状态全好时也会建议停雾降湿——这是 v1.0.1 修正的核心。）

| `sop_baseline` | 0 | 0.00 | 0.05 |
| `lower_ec` | −0.25 | 0.06 | 0.12 |
| `raise_do` | temp −0.5, do +1.2 | 0.18 | 0.02 |
| `adjust_ph` | ph += (5.8−ph)*0.8 | 0.10 | 0.04 |
| `dry_back` | ec +0.1, vpd +0.25, temp +0.5 | 0.04 | 0.08 |
| `flush_reservoir` | ec −0.45, do +0.5 | 0.30 | 0.18 |

```
post_j  = current_j + delta_j
dev_j   = clamp(|post_j - target_j|/span_j, 0, 2)
u_surv  = 1 - Σ risk_weights_j * dev_j/2
u_cost  = 1 - cost_index ;  u_qual = 1 - quality_penalty
utility = w_survival*u_surv + w_cost*u_cost + w_quality*u_qual   # 权重归一并截断负值
```

硬约束（作用于动作后的数值）：`0.8 ≤ ec ≤ 2.0`、`5.3 ≤ ph ≤ 6.4`、`do ≥ 5.0`、
`temp ≤ 26`；违反即不可行，violations 使用
`ec_range / ph_range / do_min / temp_max`。液温 `water_temp > 24` 是**前置闸门**
（zone gate，没有任何候选动作能改变它）：`decision=stop_and_review`、
`scores.zone_gates` 给出原因、选项表仍按 Nutrient 排序供冷却后参考。

可行选项按 `softmax(beta=6.0)` 归一概率（仅用于排序展示）；`confidence`
是**边际置信** `σ(ΔU/τ)`，τ=0.01，ΔU 为最优与次优效用差；约束压成单选时
confidence=0.88，若该动作边际成本 ≥0.20 则追加 `value_threshold` 复核理由。
全部不可行时 `decision=stop_and_review`、`confidence=0`、`human_review=true`。

---

## 7. 审计哈希链

账本为进程内 append-only 列表，每条记录：

```json
{"seq": 1, "ts": "2026-11-01T11:34:52.123+00:00", "audit_id": "...",
 "prev": "<上一条 hash，首条为 64 个 0>",
 "hash": "sha256(prev + json.dumps(payload, sort_keys=True))"}
```

`GET /coffee-jev/audit` 返回最近 50 条（每条附 `payload`，便于离线复算）与
`chain_valid`：服务会从头重算每条 hash 并核对 `prev` 链接，任一不匹配即为 `false`。
注意：哈希对 `sort_keys=True` 的规范化 JSON 计算，`payload` 含中文转义，属正常现象。

---

## 8. 测试

```bash
# 方式一（工作区根目录）
python -m unittest discover -s coffeejev/service -t .

# 方式二（直接运行测试文件）
python coffeejev/service/test_judgers.py
```

覆盖范围：通用数学工具；污染判断器单调性 / `tau_cost` 成本阈值 / 运营下限抬高阈值 /
三区间可达 / OOD；readiness 三道硬闸门封顶、0..100 边界、移栽必人工、证据完整度影响置信度；
fog_choice 硬约束不可行、无可行方案降级、softmax 概率归一（1e-6）、推荐项满足约束、
达标态保持 sop_baseline、液温前置闸门、唯一高成本动作需人工；
API 信封键、need_more_info、未知 stage、shadow 模式、defaulted 回填、tau_min 透传、
health 与审计链 `chain_valid`。

---

## 9. 实现约定与已知差异

1. `__init__.py` 是为满足 `python -m unittest discover -s coffeejev/service -t .`
   （起始目录必须可导入）而加的空包文件，不影响运行。
2. `defaulted` 仅在确有默认值填充时出现；`missing` 仅在 `need_more_info` 时出现。
3. `evidence_refs` 取请求中的 `image_ref`（契约示例中为 `[]` 是空请求时的形态）。
4. `/coffee-jev/audit` 的 entries 除契约五键外附带 `payload`，否则无法离线复核哈希。
5. `stage` 不在路由表内视为校验失败，返回 `need_more_info`（`missing:["stage"]`）。
6. fog_choice 的选项条目不回传内部中间量，仅返回契约字段；概率不做 4 位截断
   （避免和为 1 的误差超限），`confidence` 保留 4 位。
7. 判断器函数同时支持「传 dict」与「关键字参数」两种调用方式，
   污染判断器的原始视觉分兼容 `vision_p`（API 契约）与 `p_raw`（前端引擎）。
8. 审计账本为内存实现（重启清空）；生产环境需替换为持久化存储。

---

## 10. 与前端 `index.html` 引擎的对应关系

| 前端 JS 引擎（`coffeejev/index.html`） | 本目录实现 |
| --- | --- |
| 污染判断器（Noul / noul） | `judgers.judge_contamination()`，`jev_type="noul"` |
| 驯化度打分（Score / score） | `judgers.judge_readiness()`，`jev_type="score"` |
| 雾培方案选择（Choice / choice） | `judgers.judge_fog_choice()`，`jev_type="choice"` |
| 判断器注册表 / 节点 → 判断器映射 | `judgers.JUDGERS`、`judgers.JEV_TYPES`、`judgers.STAGE_ROUTES` |
| 成本推导阈值（两段式） | `tau_cost` + 运营下限 `tau_min`（默认 0.15） |
| 置信度、OOD、人在环规则 | 各判断器返回值中的 `confidence` / `review_reasons` / `human_review` |
| 审计链（prev/hash） | `api.AuditLedger`，`sha256(prev + json.dumps(payload, sort_keys=True))` |
| 「不执行、只记录」影子模式 | 响应 `mode="shadow"` + `would_decide` + `executed=false` |

两边的**公式、常量、枚举字符串**必须保持一致：修改任一侧时请同步另一边与
`test_judgers.py`，并以本 README 作为契约记录。
