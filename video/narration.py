# -*- coding: utf-8 -*-
"""Narration scripts for the CoffeeJeV explainer video (zh + en)."""

VOICE = {"zh": "zh-CN-YunxiNeural", "en": "en-US-AndrewNeural"}

# scene_id -> {zh: [sentences], en: [sentences]}
SCRIPT = {
    "s-title": {
        "zh": [
            "这不是又一个会聊天的农业机器人。",
            "它是给气雾培咖啡温室配的一个判断层——",
            "只回答一句话：现在这一步，做，还是不做。",
        ],
        "en": [
            "This is not another farming chatbot.",
            "It is a judgement layer for an aeroponic coffee greenhouse —",
            "built to answer one question: at this step, do we act, or do we wait?",
        ],
    },
    "s-problem": {
        "zh": [
            "雾培咖啡最难的，不是种，是判断。",
            "第一，污染肉眼看不出来，等看出来，一整盘都废了。",
            "第二，探头会骗人——EC、pH 电极几周就被生物膜糊住，可系统还是给你一个特别确定的数字。",
            "第三，老农艺师的本事，全在他脑子里，带不走、复制不了。",
        ],
        "en": [
            "The hardest part of aeroponic coffee isn't growing — it's deciding.",
            "One: contamination is invisible until the whole tray is lost.",
            "Two: probes lie. EC and pH electrodes foul within weeks, yet the system still hands you a very confident number.",
            "Three: a veteran grower's judgement lives in his head — impossible to copy.",
        ],
    },
    "s-layer": {
        "zh": [
            "所以 CoffeeJeV 只做三件事。",
            "把长流程切成 14 个原子判断，每个只答一个是非、一个选择，或者一个分数。",
            "每次判断都带一个校准过的置信度，说 0.8，就真有八成把握。",
            "而且证据不足的时候，它敢说不知道。",
        ],
        "en": [
            "So CoffeeJeV does three things.",
            "It breaks a long process into fourteen atomic decisions — each just a yes-or-no, a pick-one, or a score.",
            "Every judgement carries a calibrated confidence: when it says zero point eight, it is right about eighty percent of the time.",
            "And when evidence is missing, it is allowed to say: I don't know.",
        ],
    },
    "s-map": {
        "zh": [
            "14 个节点串成一条链：无菌建立、愈伤、增殖、生根、驯化、移栽。",
            "再进雾培这一侧：营养雾、根区、设备健康、生长开花、采收。",
            "每个节点挂一个判断器，一共三种：",
            "是非判断叫 Noul，选一个动作叫 Choice，打分叫 Score。",
        ],
        "en": [
            "The fourteen nodes form one chain: sterile establishment, callus, multiplication, rooting, acclimation, transplant.",
            "Then the aeroponic side: fog recipe, root zone, equipment health, growth, and harvest.",
            "Each node runs one of three judger types.",
            "Noul decides yes or no. Choice picks one action. Score grades from zero to a hundred.",
        ],
    },
    "s-bra": {
        "zh": [
            "页面上这三个面板，是可以亲手拨的。",
            "A 是污染判断：拖动图像模型给的原始概率，看决策怎么变。",
            "关键在阈值——它不是固定的 0.7，而是拿成本算出来的。",
            "漏判一盘要赔几十盘的苗，误隔离只浪费一袋培养基，所以阈值会被压到百分之五左右。",
            "但注意，百分之五到五十这一段，它给的不是隔离，是送检镜检——先取证，再动手。",
        ],
        "en": [
            "These three panels are hands-on.",
            "Panel A is contamination: drag the raw vision score and watch the decision change.",
            "The key is the threshold — it isn't a fixed zero point seven, it is computed from cost.",
            "Missing one infected tray costs dozens; a false quarantine wastes one bag of medium. So the threshold sits near five percent.",
            "And between five and fifty percent, it doesn't quarantine — it orders a microscopy check. Evidence first, action later.",
        ],
    },
    "s-brb": {
        "zh": [
            "B 是驯化打分：根数、褐化、株高、蜡质、失水率，加权成 0 到 100 分。",
            "80 分以上可以移栽，60 到 79 延迟几天调环境，60 以下继续驯化。",
            "有个细节：株高除以根数这个比值，太矮和徒长都扣分。",
            "徒长苗看着壮，进雾培最先死。",
        ],
        "en": [
            "Panel B is the readiness score: root count, browning, shoot height, wax, and water loss, weighted into zero to one hundred.",
            "Above eighty, transplant. Sixty to seventy-nine, wait a few days. Below sixty, keep acclimating.",
            "One detail: the shoot-to-root ratio is penalized at both ends.",
            "A tall, leggy plant looks strong — and dies first in the fog.",
        ],
    },
    "s-brc": {
        "zh": [
            "C 是营养雾：EC、pH、VPD、溶氧、雾滴粒径、液温，一起看。",
            "六个候选动作，算效用、算约束、算边际成本，给出推荐和置信度。",
            "参数都正常的时候，正确答案是什么都不做。",
            "这条我们专门修过——早期版本会建议你去停雾降湿，因为它觉得动作越便宜越好。",
        ],
        "en": [
            "Panel C is the fog recipe: EC, pH, VPD, dissolved oxygen, droplet size, and water temperature — all at once.",
            "Six candidate actions, scored on utility, constraints, and marginal cost.",
            "When everything is in band, the right answer is: do nothing.",
            "We fixed that on purpose — an earlier version kept suggesting you stop the fog, because it just liked the cheapest move.",
        ],
    },
    "s-brd": {
        "zh": [
            "对外就一个接口：把批次状态发过去，拿回决策、置信度、候选项，还有要不要人来复核。",
            "缺字段，它直接说 need_more_info，绝不猜。",
            "上线前还能开影子模式：它照样判断、照样记账，但不执行，先跟老师傅比上三个月。",
        ],
        "en": [
            "One API: send a batch state, get back a decision, confidence, options, and whether a human is needed.",
            "Missing fields? It says need_more_info — it never guesses.",
            "Before go-live, run it in shadow mode: it judges and logs everything, executes nothing, and quietly compares itself with your veteran grower for three months.",
        ],
    },
    "s-bre": {
        "zh": [
            "需要人的时候，它不会丢一句请复核就完事，而是附上完整的证据包。",
            "复核的人只有三个动作：采纳、改判放行、要求补证，每一笔都进账本。",
            "账本是一条哈希链，改任何一条历史记录，链就断。",
            "页面上有验证链按钮，可以当场试。",
        ],
        "en": [
            "When a human is needed, it doesn't just say please review — it attaches the full evidence pack.",
            "The reviewer has exactly three moves: accept, override, or request more evidence — and every one is written to the ledger.",
            "The ledger is a hash chain: change any past record, and the chain breaks.",
            "There is a verify button right on the page. Try it.",
        ],
    },
    "s-learn": {
        "zh": [
            "污染标签要七到十四天才能回来，成活率要等上一个月。",
            "所以它有一条延迟标签管线：先记账，标签到了再回填，然后每周重新校准一次。",
            "置信度显示 0.82、实际只有 0.55 的时候，校准曲线会把这条弯线，拉回对角线。",
        ],
        "en": [
            "Contamination labels take one to two weeks; survival rates take a month.",
            "So there is a delayed-label pipeline: log the decision now, backfill the label when it arrives, and recalibrate every week.",
            "When the model says zero point eight two but reality is zero point five five, the calibration curve pulls that bend back onto the diagonal.",
        ],
    },
    "s-brf": {
        "zh": [
            "这个经济性计算器，改个数字，就能看到回收期。",
            "年出圃六万株以下，一年挽回的损失还不够付运维费，回收期是无穷。",
            "这不是模型不行，是固定成本摊不薄。",
            "这个规模的正确做法，是先用区域共享的边缘盒子。",
        ],
        "en": [
            "This economics calculator — change a number, and see the payback.",
            "Below sixty thousand plants a year, the losses you recover don't even cover maintenance, so payback is infinite.",
            "That is not the model failing — fixed costs just don't spread that thin.",
            "At that scale, the right move is a shared regional edge box.",
        ],
    },
    "s-road": {
        "zh": [
            "90 天先交付三个判断器，配三道验收闸门，还有一条事先写进合同的止损规则。",
            "风险清单十条，每条都带一个能观测到的信号。",
            "后面还跟着一张不做清单：不做全自动控制，不集中各农场的原始数据。",
        ],
        "en": [
            "Ninety days deliver three judgers, three acceptance gates, and a stop-loss rule written into the contract in advance.",
            "Ten risks, each with an observable signal.",
            "And a not-to-do list: no full automation, no pooling of raw data across farms.",
        ],
    },
    "s-close": {
        "zh": [
            "一句话总结：把咖啡种植的长流程，拆成一个个马上能答的小问题。",
            "答得准就说准，答不准就说不知道。",
            "整份规格完全离线，双击就能打开；后端是纯 Python，可以直接接进你现有的系统。",
        ],
        "en": [
            "One line: turn a long growing process into small questions you can answer right away.",
            "Say it's sure when it's sure — and say I don't know when it isn't.",
            "The whole spec runs offline: double-click to open. The backend is plain Python, ready to plug into your system.",
        ],
    },
}

# scene order in the video
ORDER = ["s-title", "s-problem", "s-layer", "s-map",
         "s-bra", "s-brb", "s-brc", "s-brd", "s-bre", "s-learn", "s-brf",
         "s-road", "s-close"]
