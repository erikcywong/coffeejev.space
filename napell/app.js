/* ============================================================
   Napell Agent — iOS-style PWA client for the CoffeeJeV decision layer
   Three languages: 中文 / English / العربية (RTL)
   ============================================================ */
'use strict';

/* ---------------- i18n ---------------- */
const STR = {
  zh: {
    'app':'Napell Agent','app.sub':'咖啡判断层',
    'tab.home':'今日','tab.judges':'判断器','tab.map':'地图','tab.review':'复核','tab.more':'更多',
    'home.hero':'当前批次','home.stage':'阶段','home.ready':'达标度','home.risk':'风险',
    'home.needs':'需要你确认','home.quick':'快速判断','home.kpi':'关键指标','home.batch':'AP-0713 · 480 苗',
    'home.risk.low':'低','home.risk.mid':'中','home.risk.high':'高',
    'kpi.fn':'漏检率','kpi.review':'复核率','kpi.p95':'p95 时延','kpi.ece':'校准 ECE',
    'judge.a':'污染','judge.b':'驯化','judge.c':'营养雾','judge.run':'记入账本','judge.verdict':'判断',
    'a.vision':'视觉模型原始分','a.quality':'图像质量','a.temp':'环境温度','a.rh':'相对湿度',
    'a.days':'继代天数','a.hist':'批次历史污染率','a.cfp':'误隔离成本','a.cfn':'漏检成本','a.tmin':'运营下限',
    'b.roots':'根数','b.brown':'根尖褐变','b.shoot':'株高','b.leaf':'叶色','b.wax':'气孔/蜡质','b.water':'失水测试','b.cont':'并行污染概率',
    'c.ec':'EC','c.ph':'pH','c.vpd':'VPD','c.temp':'根区温度','c.do':'溶氧','c.drop':'雾滴粒径',
    'c.wt':'营养液温度','c.ws':'权重·成活','c.wc':'权重·成本','c.wq':'权重·品质',
    'm.p':'校准后 p','m.tc':'τ_cost','m.thi':'τ_hi','m.tlo':'τ_lo','m.conf':'置信度','m.ood':'OOD',
    'd.continue':'放行','d.review_microscopy':'复核','d.isolate_and_sample':'隔离送检',
    'd.transplant_ready':'可移栽','d.delay_adjust':'延迟调整','d.continue_acclimation':'继续驯化',
    'd.sop_baseline':'按 SOP 维持','d.lower_ec':'降 EC','d.raise_do':'增溶氧','d.adjust_ph':'调 pH',
    'd.dry_back':'停雾降湿','d.flush_reservoir':'换液冲洗','d.stop_and_review':'停止并复核',
    'map.title':'14 个决策节点','map.inputs':'输入','map.outputs':'输出','map.rules':'判据','map.esc':'升级人工','map.metric':'指标',
    'rev.queue':'待复核','rev.accept':'采纳','rev.override':'改判','rev.need':'补证',
    'rev.ledger':'决策账本','rev.verify':'验证链','rev.empty':'暂无记录','rev.ok':'链完整','rev.bad':'链异常',
    'more.lang':'语言','more.econ':'经济性','more.api':'接口','more.api.try':'调用示例','more.about':'关于',
    'econ.n':'年出圃量','econ.v':'单株价值','econ.c0':'基线污染损失率 %','econ.c1':'目标污染损失率 %',
    'econ.s0':'基线成活率 %','econ.s1':'目标成活率 %','econ.capex':'一次性投入','econ.opex':'年运维','econ.d':'日均决策',
    'econ.pay':'回收期（月）','econ.net':'年净现金流','econ.cpd':'单次成本','econ.gain':'年挽回',
    'about.body':'所有数值均为设计目标或可调假设，不是实测结果。判断层只输出决策与置信度，关键动作需人工确认。',
    'about.sop':'SOP 版本','about.model':'模型','about.build':'构建',
    'node.1':'种质准入','node.2':'无菌建立','node.3':'愈伤发生','node.4':'增殖继代','node.5':'生根',
    'node.6':'驯化达标','node.7':'雾培移栽','node.8':'营养雾配方','node.9':'根区异常','node.10':'株型开花',
    'node.11':'采收窗口','node.12':'隔离半径','node.13':'能耗调度','node.14':'复盘归因'
  },
  en: {
    'app':'Napell Agent','app.sub':'coffee decision layer',
    'tab.home':'Today','tab.judges':'Judgers','tab.map':'Map','tab.review':'Review','tab.more':'More',
    'home.hero':'Current batch','home.stage':'Stage','home.ready':'Readiness','home.risk':'Risk',
    'home.needs':'Needs your call','home.quick':'Quick judge','home.kpi':'Key metrics','home.batch':'AP-0713 · 480 plantlets',
    'home.risk.low':'low','home.risk.mid':'medium','home.risk.high':'high',
    'kpi.fn':'missed','kpi.review':'review rate','kpi.p95':'p95 latency','kpi.ece':'calibration ECE',
    'judge.a':'Contamination','judge.b':'Readiness','judge.c':'Nutrient fog','judge.run':'Log decision','judge.verdict':'Decision',
    'a.vision':'Vision model score','a.quality':'Image quality','a.temp':'Ambient temp','a.rh':'Relative humidity',
    'a.days':'Days in culture','a.hist':'Batch contamination rate','a.cfp':'False-quarantine cost','a.cfn':'Missed-detection cost','a.tmin':'Operating floor',
    'b.roots':'Root count','b.brown':'Root-tip browning','b.shoot':'Shoot height','b.leaf':'Leaf colour','b.wax':'Stomata / wax','b.water':'Water-loss test','b.cont':'Contamination probability',
    'c.ec':'EC','c.ph':'pH','c.vpd':'VPD','c.temp':'Root-zone temp','c.do':'Dissolved O₂','c.drop':'Droplet size',
    'c.wt':'Solution temp','c.ws':'Weight · survival','c.wc':'Weight · cost','c.wq':'Weight · quality',
    'm.p':'Calibrated p','m.tc':'τ_cost','m.thi':'τ_hi','m.tlo':'τ_lo','m.conf':'Confidence','m.ood':'OOD',
    'd.continue':'Clear','d.review_microscopy':'Review','d.isolate_and_sample':'Isolate & sample',
    'd.transplant_ready':'Transplant ready','d.delay_adjust':'Delay & adjust','d.continue_acclimation':'Keep acclimating',
    'd.sop_baseline':'Hold SOP','d.lower_ec':'Lower EC','d.raise_do':'Raise O₂','d.adjust_ph':'Adjust pH',
    'd.dry_back':'Dry back','d.flush_reservoir':'Flush reservoir','d.stop_and_review':'Stop & review',
    'map.title':'14 decision nodes','map.inputs':'Inputs','map.outputs':'Outputs','map.rules':'Rule','map.esc':'Escalate','map.metric':'Metric',
    'rev.queue':'Waiting on you','rev.accept':'Accept','rev.override':'Override','rev.need':'Ask for evidence',
    'rev.ledger':'Decision ledger','rev.verify':'Verify chain','rev.empty':'No entries yet','rev.ok':'chain intact','rev.bad':'chain broken',
    'more.lang':'Language','more.econ':'Economics','more.api':'API','more.api.try':'Run example','more.about':'About',
    'econ.n':'Plants per year','econ.v':'Value per plant','econ.c0':'Baseline loss %','econ.c1':'Target loss %',
    'econ.s0':'Baseline survival %','econ.s1':'Target survival %','econ.capex':'One-off cost','econ.opex':'Annual running cost','econ.d':'Decisions per day',
    'econ.pay':'Payback (months)','econ.net':'Net cash flow','econ.cpd':'Cost per decision','econ.gain':'Recovered per year',
    'about.body':'Every number here is a design target or an adjustable assumption, not a measurement. The layer returns a decision and a confidence; irreversible actions still need a human.',
    'about.sop':'SOP version','about.model':'Model','about.build':'Build',
    'node.1':'Germplasm intake','node.2':'Aseptic establishment','node.3':'Callus','node.4':'Proliferation','node.5':'Rooting',
    'node.6':'Acclimation readiness','node.7':'Transplant gate','node.8':'Nutrient fog recipe','node.9':'Root-zone anomaly','node.10':'Flowering',
    'node.11':'Harvest window','node.12':'Isolation radius','node.13':'Power dispatch','node.14':'Retrospective'
  },
  ar: {
    'app':'Napell Agent','app.sub':'طبقة القرار للقهوة',
    'tab.home':'اليوم','tab.judges':'المُحكِّمون','tab.map':'الخريطة','tab.review':'المراجعة','tab.more':'المزيد',
    'home.hero':'الدفعة الحالية','home.stage':'المرحلة','home.ready':'الجاهزية','home.risk':'المخاطر',
    'home.needs':'بحاجة إلى قرارك','home.quick':'حكم سريع','home.kpi':'المؤشرات الرئيسية','home.batch':'AP-0713 · 480 شتلة',
    'home.risk.low':'منخفض','home.risk.mid':'متوسط','home.risk.high':'مرتفع',
    'kpi.fn':'التفويت','kpi.review':'نسبة المراجعة','kpi.p95':'كمون p95','kpi.ece':'خطأ المعايرة',
    'judge.a':'التلوث','judge.b':'الأقلمة','judge.c':'الضباب المغذي','judge.run':'تسجيل القرار','judge.verdict':'القرار',
    'a.vision':'درجة النموذج البصري','a.quality':'جودة الصورة','a.temp':'حرارة البيئة','a.rh':'الرطوبة النسبية',
    'a.days':'أيام الزراعة','a.hist':'معدل التلوث التاريخي','a.cfp':'تكلفة الحجر الخاطئ','a.cfn':'تكلفة تفويت التلوث','a.tmin':'الحد التشغيلي',
    'b.roots':'عدد الجذور','b.brown':'اسمرار أطراف الجذور','b.shoot':'طول الساق','b.leaf':'لون الورق','b.wax':'الثغور والطبقة الشمعية','b.water':'اختبار فقد الماء','b.cont':'احتمال التلوث',
    'c.ec':'التوصيل الكهربائي','c.ph':'الحموضة','c.vpd':'ضغط البخار','c.temp':'حرارة الجذور','c.do':'الأكسجين الذائب','c.drop':'حجم القطرات',
    'c.wt':'حرارة المحلول','c.ws':'الوزن · البقاء','c.wc':'الوزن · التكلفة','c.wq':'الوزن · الجودة',
    'm.p':'p بعد المعايرة','m.tc':'τ_cost','m.thi':'τ_hi','m.tlo':'τ_lo','m.conf':'الثقة','m.ood':'خارج التوزيع',
    'd.continue':'إفراج','d.review_microscopy':'مراجعة','d.isolate_and_sample':'حجر وعينة',
    'd.transplant_ready':'جاهز للنقل','d.delay_adjust':'تأخير وتعديل','d.continue_acclimation':'متابعة الأقلمة',
    'd.sop_baseline':'حسب الإجراء','d.lower_ec':'خفض EC','d.raise_do':'رفع الأكسجين','d.adjust_ph':'تعديل pH',
    'd.dry_back':'إيقاف الضباب','d.flush_reservoir':'تغيير المحلول','d.stop_and_review':'إيقاف ومراجعة',
    'map.title':'أربع عشرة عقدة قرار','map.inputs':'المدخلات','map.outputs':'المخرجات','map.rules':'المعيار','map.esc':'التصعيد','map.metric':'المؤشر',
    'rev.queue':'بانتظار قرارك','rev.accept':'قبول','rev.override':'تصحيح','rev.need':'طلب دليل',
    'rev.ledger':'سجل القرارات','rev.verify':'تحقّق من السلسلة','rev.empty':'لا توجد سجلات','rev.ok':'السلسلة سليمة','rev.bad':'خلل في السلسلة',
    'more.lang':'اللغة','more.econ':'الاقتصاد','more.api':'الواجهة','more.api.try':'تشغيل مثال','more.about':'حول',
    'econ.n':'شتلات في السنة','econ.v':'قيمة الشتلة','econ.c0':'نسبة الفقد الأساسية %','econ.c1':'نسبة الفقد المستهدفة %',
    'econ.s0':'نسبة البقاء الأساسية %','econ.s1':'نسبة البقاء المستهدفة %','econ.capex':'تكلفة لمرة واحدة','econ.opex':'التشغيل السنوي','econ.d':'قرارات يوميًا',
    'econ.pay':'فترة الاسترداد (شهرًا)','econ.net':'صافي التدفق السنوي','econ.cpd':'تكلفة القرار','econ.gain':'الموفَّر سنويًا',
    'about.body':'كل الأرقام هنا أهداف تصميمية أو افتراضات قابلة للتعديل، وليست قياسات. تُخرج الطبقة قرارًا وثقة، وتبقى الإجراءات غير القابلة للتراجع بحاجة إلى إنسان.',
    'about.sop':'إصدار الإجراء','about.model':'النموذج','about.build':'البناء',
    'node.1':'استلام الأصل','node.2':'التعقيم','node.3':'الكالوس','node.4':'الإكثار','node.5':'التجذير',
    'node.6':'جاهزية الأقلمة','node.7':'بوابة النقل','node.8':'تركيبة الضباب','node.9':'شذوذ الجذور','node.10':'الإزهار',
    'node.11':'نافذة الحصاد','node.12':'نطاق الحجر','node.13':'جدولة الطاقة','node.14':'المراجعة اللاحقة'
  }
};

/* ---------------- IoT strings (added after the core dictionary) ---------------- */
const STR_EXT = {
  zh: {
    'tab.devices':'设备',
    'dev.platform':'平台地址','dev.connect':'连接','dev.demo':'离线演示数据','dev.live':'已连接','dev.err':'连不上',
    'dev.online':'在线','dev.offline':'离线','dev.open':'未确认告警','dev.ack':'确认','dev.none':'没有设备',
    'dev.keys':'关键量','dev.lastSeen':'最后上报','dev.transport':'通道','dev.profile':'Profile',
    'dev.rpc':'下发命令','dev.rpc.ok':'已下发','dev.rpc.blocked':'被硬限位拒绝','dev.rpc.pending':'等待回执',
    'dev.hint':'填 platform 地址即可读取真实设备；留空使用离线演示数据。',
    'dev.ingest':'入站','dev.rate':'条/分','dev.values':'数值'
  },
  en: {
    'tab.devices':'Devices',
    'dev.platform':'Platform URL','dev.connect':'Connect','dev.demo':'offline demo data','dev.live':'connected','dev.err':'unreachable',
    'dev.online':'online','dev.offline':'offline','dev.open':'open alarms','dev.ack':'Ack','dev.none':'no devices',
    'dev.keys':'keys','dev.lastSeen':'last seen','dev.transport':'transport','dev.profile':'Profile',
    'dev.rpc':'Send command','dev.rpc.ok':'sent','dev.rpc.blocked':'blocked by hard limit','dev.rpc.pending':'awaiting ack',
    'dev.hint':'Point this at the platform URL to read real devices; leave it empty to use the offline demo data.',
    'dev.ingest':'ingest','dev.rate':'msgs/min','dev.values':'values'
  },
  ar: {
    'tab.devices':'الأجهزة',
    'dev.platform':'عنوان المنصة','dev.connect':'اتصال','dev.demo':'بيانات عرض دون اتصال','dev.live':'متصل','dev.err':'تعذّر الاتصال',
    'dev.online':'متصل','dev.offline':'غير متصل','dev.open':'تنبيهات مفتوحة','dev.ack':'تأكيد','dev.none':'لا توجد أجهزة',
    'dev.keys':'القياسات','dev.lastSeen':'آخر إرسال','dev.transport':'القناة','dev.profile':'الملف',
    'dev.rpc':'إرسال أمر','dev.rpc.ok':'أُرسل','dev.rpc.blocked':'مرفوض بحدّ صلب','dev.rpc.pending':'بانتظار التأكيد',
    'dev.hint':'ضع عنوان المنصة لقراءة الأجهزة الحقيقية؛ اتركه فارغًا لاستخدام بيانات العرض.',
    'dev.ingest':'الوارد','dev.rate':'رسالة/دقيقة','dev.values':'قيم'
  }
};
Object.keys(STR_EXT).forEach(l => Object.assign(STR[l], STR_EXT[l]));

const LANG_META = { zh:{dir:'ltr', locale:'zh-CN'}, en:{dir:'ltr', locale:'en'}, ar:{dir:'rtl', locale:'ar-SA'} };

let state = {
  lang: localStorage.getItem('napell-lang') || 'zh',
  tab: 'home',
  judge: 'a',
  hidden: false,
  a: { p:0.62, q:0.90, t:24.5, rh:68, d:18, hist:0.03, cfp:40, cfn:900, tmin:0.15 },
  b: { roots:5, brown:22, shoot:3.2, leaf:78, wax:70, water:9.5, cont:0.08 },
  c: { ec:1.2, ph:5.8, vpd:0.9, t:24, do:6.5, drop:35, wt:21, ws:0.5, wc:0.2, wq:0.3 },
  econ: { n:240000, v:0.45, c0:8, c1:4, s0:72, s1:84, capex:18000, opex:4800, d:800 },
  ledger: [],
  platform: localStorage.getItem('napell-platform') || '',
  live: null,            // last /api/overview payload when connected
  liveErr: ''
};

const t = k => (STR[state.lang] && STR[state.lang][k]) || STR.en[k] || k;
const clamp = (v,a,b)=>Math.min(b,Math.max(a,v));
const r4 = x => Math.round(x*1e4)/1e4;
const sig = x => 1/(1+Math.exp(-x));
const logit = p => { p=clamp(p,1e-4,1-1e-4); return Math.log(p/(1-p)); };
const money = n => Math.round(n).toLocaleString('en-US');

/* ---------------- the three judgers (same maths as the spec) ---------------- */
function judgeContamination(i){
  const prior = clamp(i.hist,1e-3,0.5);
  const blend = i.q*logit(i.p) + (1-i.q)*logit(prior)
    + 0.35*(i.t-24)/3 + 0.25*(i.rh-65)/15 + 0.12*(i.d-14)/7;
  const pCal = sig(blend/1.35);
  const tauCost = clamp(i.cfp/(i.cfp+i.cfn),0.02,0.5);
  const tauHi = clamp(Math.max(tauCost,i.tmin),0.02,0.5);
  const tauLo = Math.max(0.06,0.45*tauHi);
  const decision = pCal>=tauHi?'isolate_and_sample':(pCal>=tauLo?'review_microscopy':'continue');
  const conf = Math.max(pCal,1-pCal);
  const ood = i.q<0.55 || i.hist===0;
  const reasons=[];
  if(conf<0.70) reasons.push('low_confidence');
  if(ood) reasons.push('ood');
  if(pCal>=tauLo&&pCal<tauHi) reasons.push('boundary_zone');
  return { jev:'noul', decision, conf:r4(conf), p:pCal, tauCost, tauHi, tauLo, ood, reasons };
}
function judgeReadiness(i){
  const s = [
    Math.min(100, i.roots/12*100),
    100-i.brown,
    clamp((i.shoot/Math.max(i.roots,1))/0.6*100,0,100),
    i.leaf, i.wax,
    clamp(100-i.water/25*100,0,100)
  ];
  const W=[0.22,0.20,0.10,0.12,0.18,0.18];
  let raw = s.reduce((a,v,k)=>a+v*W[k],0);
  let score = Math.round(raw);
  const caps=[];
  if(i.roots<3){score=Math.min(score,55);caps.push('roots');}
  if(i.brown>60){score=Math.min(score,60);caps.push('browning');}
  if(i.cont>=0.5){score=Math.min(score,40);caps.push('contamination');}
  const band = score>=80?'transplant_ready':(score>=60?'delay_adjust':'continue_acclimation');
  const sd = Math.sqrt(s.reduce((a,v)=>a+(v-s.reduce((x,y)=>x+y,0)/s.length)**2,0)/s.length);
  const conf = clamp(0.62+0.30-0.35*(sd/50),0.35,0.97);
  return { jev:'score', decision:band, conf:r4(conf), score, subs:s, caps };
}
const FT={ec:1.4,ph:5.8,vpd:0.9,t:24,do:6.5,drop:35};
const FS={ec:0.8,ph:0.9,vpd:0.5,t:6,do:3,drop:25};
const FR={do:.28,t:.24,ph:.18,ec:.16,vpd:.09,drop:.05};
const OPTS=[
  {id:'sop_baseline',d:[0,0,0,0,0,0],cost:.30,qual:.05},
  {id:'lower_ec',d:[-0.25,0,0,0,0,0],cost:.28,qual:.12},
  {id:'raise_do',d:[0,0,0,-0.5,1.2,0],cost:.55,qual:.02},
  {id:'adjust_ph',d:[0,-999,0,0,0,0],cost:.33,qual:.04},
  {id:'dry_back',d:[0.1,0,0.25,0.5,0,0],cost:.12,qual:.08},
  {id:'flush_reservoir',d:[-0.45,0,0,0,0.5,0],cost:.40,qual:.18}
];
const KEYS=['ec','ph','vpd','t','do','drop'];
function judgeFog(i){
  const cur={ec:i.ec,ph:i.ph,vpd:i.vpd,t:i.t,do:i.do,drop:i.drop};
  const Wt=i.ws+i.wc+i.wq||1, W={s:i.ws/Wt,c:i.wc/Wt,q:i.wq/Wt};
  const opts=OPTS.map(o=>{
    const delta=o.d.map((v,k)=>v===-999?(FT.ph-cur.ph)*0.8:v);
    const post={},dev={},viol=[];
    KEYS.forEach((k,idx)=>{post[k]=cur[k]+delta[idx];dev[k]=clamp(Math.abs(post[k]-FT[k])/FS[k],0,2);});
    if(post.ec<0.8||post.ec>2.0)viol.push('ec');
    if(post.ph<5.3||post.ph>6.4)viol.push('ph');
    if(post['do']<5.0)viol.push('do');
    if(post.t>26)viol.push('temp');
    if(i.wt>24)viol.push('water_temp');
    const uSurv=1-KEYS.reduce((a,k)=>a+FR[k]*dev[k]/2,0);
    const uCost=1-o.cost,uQual=1-o.qual;
    return {action:o.id,feasible:viol.length===0,viol,utility:W.s*uSurv+W.c*uCost+W.q*uQual,post,
      comp:{surv:uSurv,cost:uCost,qual:uQual}};
  });
  const feas=opts.filter(o=>o.feasible);
  if(feas.length){
    const mx=Math.max(...feas.map(o=>o.utility));
    let sum=0; feas.forEach(o=>{o.p=Math.exp(6*(o.utility-mx));sum+=o.p;});
    feas.forEach(o=>o.p/=sum);
  }
  opts.forEach(o=>{if(!o.feasible)o.p=0;});
  const best=feas.slice().sort((a,b)=>b.utility-a.utility)[0]||null;
  return { jev:'choice', decision:best?best.action:'stop_and_review', conf:best?r4(best.p):0, options:opts, best };
}


/* ---------------- the fleet (matches the IoT platform 1:1) ---------------- */
const DEMO_FLEET = [
  {name:'fog-ctrl-A3', profile:'fog-controller', transport:'mqtt', online:true, last:{ec:1.41,ph:5.83,do:7.8,water_temp:19.8,vpd:0.38,air_temp:25.1,rh:62}},
  {name:'root-cam-A3', profile:'vision-edge', transport:'http', online:true, last:{vision_p:0.09,image_quality:0.88,roots_count:7}},
  {name:'tray-scan-TC118', profile:'vision-edge', transport:'http', online:true, last:{contaminated_p:0.12,image_quality:0.76}},
  {name:'climate-PuEr-01', profile:'climate', transport:'http', online:true, last:{air_temp:24.8,rh:64,vpd:0.96,co2:642}},
  {name:'power-meter-PuEr-01', profile:'energy', transport:'http', online:true, last:{power_kw:3.42,kwh_total:18432,tariff:0.68}},
  {name:'micro-lab-01', profile:'lab', transport:'http', online:false, last:{sample_cfu:6,coliform:0}},
  {name:'valve-4A', profile:'actuator', transport:'http', online:true, last:{state:'closed',pressure_bar:2.72,cycles:1841}},
  {name:'gateway-edge-01', profile:'gateway', transport:'http', online:true, last:{cpu_pct:41,mem_pct:58,temp_c:46.2,buffer_depth:3}}
];
const fleet = () => (state.live && state.live.devices) ? state.live.devices : DEMO_FLEET;
const liveAlarms = () => (state.live && state.live.alarms) ? state.live.alarms.filter(a => !a.acked) : [];

/* ---------------- 14 nodes ---------------- */
const NODES = [
  {id:1, jev:'choice', stage:'intake',
    zh:['品种、来源、检疫、授权标记 → 准入 / 隔离 / 拒收','历史污染 >10% 或授权缺失'],
    en:['Variety, origin, phytosanitary, licence → accept / quarantine / reject','history >10% or licence missing'],
    ar:['الصنف والمصدر والحجر والترخيص → قبول / حجر / رفض','التاريخ >10% أو الترخيص ناقص']},
  {id:2, jev:'noul', stage:'aseptic_establishment',
    zh:['图像、温湿度、继代天数、批次先验 → 放行 / 复核 / 隔离','置信度 <0.70 或图像质量 <0.55'],
    en:['Image, temp, humidity, days, prior → clear / review / isolate','confidence <0.70 or image quality <0.55'],
    ar:['الصورة والحرارة والرطوبة والأيام → إفراج / مراجعة / حجر','الثقة <0.70 أو جودة الصورة <0.55']},
  {id:3, jev:'score', stage:'callus',
    zh:['形态、颜色、生长速率 → 胚性潜力 0–100','分数落在 40–60'],
    en:['Morphology, colour, growth rate → embryogenic score 0–100','score lands in 40–60'],
    ar:['الشكل واللون ومعدل النمو → درجة جنينية 0–100','الدرجة بين 40–60']},
  {id:4, jev:'choice', stage:'proliferation',
    zh:['增殖系数、玻璃化率、激素 → 继代 / 降激素 / 弃用','连续两代增殖系数 <2'],
    en:['Multiplication rate, vitrification, hormones → subculture / reduce / discard','two generations below 2×'],
    ar:['معامل الإكثار والتزجيج والهرمونات → إكثار / تخفيض / إهمال','جيلان متتاليان أقل من 2×']},
  {id:5, jev:'noul', stage:'rooting',
    zh:['根数、根色、愈伤量、根尖图像 → 可生根 / 调整 / 弃用','根区异味或褐变突增'],
    en:['Root count, colour, callus, root-tip image → rooted / adjust / discard','odour record or sudden browning'],
    ar:['عدد الجذور واللون والكالوس → تجذير / تعديل / إهمال','رائحة أو اسمرار مفاجئ']},
  {id:6, jev:'score', stage:'acclimation',
    zh:['根数、褐变、株高、叶色、气孔、失水 → 可移栽 / 延迟 / 继续','60–80 分或置信度 <0.70'],
    en:['Roots, browning, height, leaf, stomata, water loss → ready / delay / continue','score 60–80 or confidence <0.70'],
    ar:['الجذور والاسمرار والطول والورق والثغور → جاهز / تأخير / متابعة','الدرجة 60–80 أو الثقة <0.70']},
  {id:7, jev:'choice', stage:'transplant_gate',
    zh:['达标度、菌检、根团、槽位 → 立即 / 延迟 3–7 天 / 先隔离','任何首次移栽、任何阳性'],
    en:['Readiness, lab test, root ball, slot → now / delay 3–7 d / isolate first','any first transplant, any positive'],
    ar:['الجاهزية والفحص وكرة الجذور → الآن / تأخير / حجر أولًا','أي نقل أول أو نتيجة موجبة']},
  {id:8, jev:'choice', stage:'aeroponics_nutrition',
    zh:['EC、pH、VPD、溶氧、雾滴、液温、电价 → 6 个候选动作','全部候选不可行 → 停止并复核'],
    en:['EC, pH, VPD, O₂, droplet, temp, tariff → six candidate actions','nothing feasible → stop and review'],
    ar:['EC و pH و VPD والأكسجين والقطرات → ستة إجراءات','لا خيار ممكن → إيقاف ومراجعة']},
  {id:9, jev:'anomaly', stage:'root_zone_check',
    zh:['根尖图像、气味记录、溶氧、微生物快检 → 正常 / 预警 / 停雾','疑似病原'],
    en:['Root-tip image, odour log, O₂, rapid test → normal / warn / stop fog','suspected pathogen'],
    ar:['صورة الجذور والرائحة والأكسجين والفحص → طبيعي / تحذير / إيقاف','اشتباه ممرض']},
  {id:10, jev:'score', stage:'flowering',
    zh:['株型、叶色、花芽、温光累积 → 健康度 + 促花优先级','多目标冲突'],
    en:['Habit, leaf, buds, heat/light sum → health score + forcing priority','competing objectives'],
    ar:['الشكل والورق والبراعم والحرارة → درجة الصحة والأولوية','تعارض الأهداف']},
  {id:11, jev:'choice', stage:'harvest_window',
    zh:['糖度、成熟度、杯测趋势、交期 → 采 / 延 / 分批','合约品质争议'],
    en:['Brix, ripeness, cup trend, delivery → harvest / delay / split','contract quality dispute'],
    ar:['السكر والنضج والاتجاه والتسليم → حصاد / تأخير / تقسيم','نزاع على الجودة']},
  {id:12, jev:'choice', stage:'quarantine',
    zh:['谱系图、污染类别、位置、时间窗 → 单盘 / 1–3 层 / 整室','任何污染事件'],
    en:['Lineage, class, position, time window → tray / 1–3 shelves / room','any contamination event'],
    ar:['النسب والصنف والموقع والوقت → صينية / رفوف / غرفة','أي حدث تلوث']},
  {id:13, jev:'choice', stage:'power_dispatch',
    zh:['分时电价、泵组负荷、天气、交期 → 正常 / 错峰 / 降占空比','削峰影响交期'],
    en:['Tariff, pump load, weather, delivery → normal / shift / reduce duty','peak shifting hits delivery'],
    ar:['التعرفة والحمل والطقس والتسليم → عادي / إزاحة / تخفيض','الإزاحة تؤثر على التسليم']},
  {id:14, jev:'score', stage:'retro_review',
    zh:['成活率、污染、能耗、成本、复核记录 → 根因排序 + 更新建议','数据漂移或连续三周恶化'],
    en:['Survival, contamination, energy, cost, reviews → ranked causes + updates','drift or three worsening weeks'],
    ar:['البقاء والتلوث والطاقة والتكلفة → أسباب مرتبة وتحديثات','انحراف أو ثلاث أسابيع تدهور']}
];
const nodeTxt = n => n[state.lang] || n.en;

/* ---------------- ledger ---------------- */
function fnv(s){let h=0x811c9dc5;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,0x01000193)>>>0;}return ('0000000'+h.toString(16)).slice(-8);}
function payloadOf(e){ return JSON.stringify([e.stage,e.decision,e.conf,e.seq]); }
function pushLedger(entry){
  const prev = state.ledger.length ? state.ledger[state.ledger.length-1].hash : 'genesis';
  const e = {...entry, seq:state.ledger.length+1, prev};
  e.hash = fnv(prev + payloadOf(e));
  state.ledger.push(e);
}
function chainOk(){
  let prev='genesis';
  for(const e of state.ledger){
    if(e.prev!==prev) return false;
    if(fnv(prev + payloadOf(e))!==e.hash) return false;
    prev = e.hash;
  }
  return true;
}

/* ---------------- helpers ---------------- */
const esc = s => String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
function hl(obj){
  const s = esc(JSON.stringify(obj,null,2));
  return s.replace(/("(?:\\.|[^"\\])*")(\s*:)?|\b(true|false|null)\b|(-?\d+(?:\.\d+)?)/g,(m,str,col,lit,num)=>{
    if(str!==undefined) return col?`<span class="k">${str}</span>${col}`:`<span class="s">${str}</span>`;
    if(lit!==undefined) return lit==='null'?`<span class="nl">null</span>`:`<span class="b">${lit}</span>`;
    return `<span class="n">${num}</span>`;
  });
}
const chev = `<svg class="chev" viewBox="0 0 8 13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1.5 1.5L6.5 6.5L1.5 11.5"/></svg>`;
const row = (title,sub,value) => `<div class="row"><div class="txt"><div class="t">${title}</div>${sub?`<div class="s">${sub}</div>`:''}</div>${value!==undefined?`<div class="v">${value}</div>`:''}</div>`;

/* ---------------- screens ---------------- */
function screenHome(){
  const r = judgeReadiness(state.b);
  const riskKey = r.score>=80?'low':(r.score>=60?'mid':'high');
  const riskCls = riskKey==='low'?'b-ok':(riskKey==='mid'?'b-warn':'b-bad');
  return `
  <div class="nav"><h1>${t('tab.home')}</h1></div>
  <div class="hero">
    <div class="k">${t('home.hero')}</div>
    <div class="big">${r.score}<small>/100</small></div>
    <div style="font-size:13px;color:var(--tx2)">${t('home.batch')}</div>
    <div class="row2">
      <div class="stat"><div class="k2">${t('home.stage')}</div><div class="v2">${t('judge.b')}</div></div>
      <div class="stat"><div class="k2">${t('home.risk')}</div><div class="v2"><span class="badge ${riskCls}">${t('home.risk.'+riskKey)}</span></div></div>
    </div>
  </div>
  <div class="group"><div class="h">${t('home.needs')}</div><div class="card">
    <div class="row" data-review="RV-2411"><div class="txt">
      <div class="t"><span class="badge b-warn" style="margin-inline-end:6px">RV-2411</span>79/100</div>
      <div class="s">AP-0713 · ${t('d.delay_adjust')}</div></div>${chev}</div>
    <div class="row" data-review="RV-2413"><div class="txt">
      <div class="t"><span class="badge b-bad" style="margin-inline-end:6px">RV-2413</span>${t('d.stop_and_review')}</div>
      <div class="s">A3 · pH 5.24</div></div>${chev}</div>
  </div></div>
  <div class="group"><div class="h">${t('home.quick')}</div><div class="card">
    ${['a','b','c'].map(k=>`<div class="row" data-goto="judges" data-judge="${k}">
      <div class="txt"><div class="t">${t('judge.'+k)}</div></div>${chev}</div>`).join('')}
  </div></div>
  <div class="group"><div class="h">${t('home.kpi')}</div><div class="card">
    ${row(t('kpi.fn'),'','3.1%')}${row(t('kpi.review'),'','12%')}${row(t('kpi.p95'),'','210 ms')}${row(t('kpi.ece'),'','0.042')}
  </div></div>
  <div class="note">${t('about.body')}</div>`;
}

function screenJudges(){
  const seg = `<div class="seg">${['a','b','c'].map(k=>
    `<button data-judge="${k}" class="${state.judge===k?'on':''}">${t('judge.'+k)}</button>`).join('')}</div>`;
  const j = state.judge;
  const sl = (g,k,label,sub,min,max,step,val) => `
    <div class="sl"><div class="top"><div class="lbl">${label}${sub?`<small>${sub}</small>`:''}</div>
      <div class="val" id="v-${k}">${val}</div></div>
      <input type="range" data-g="${g}" data-k="${k}" min="${min}" max="${max}" step="${step}" value="${val}" data-fmt="${
        ['p','q','ph','vpd'].includes(k)?2:(['hist','tmin','cont','ws','wc','wq'].includes(k)?2:1)}">
    </div>`;
  let controls='';
  if(j==='a'){
    const a=state.a;
    controls = sl('a','p',t('a.vision'),'p_raw',0,1,0.01,a.p.toFixed(2))
      + sl('a','q',t('a.quality'),'',0,1,0.01,a.q.toFixed(2))
      + sl('a','t',t('a.temp'),'°C',18,32,0.5,a.t.toFixed(1))
      + sl('a','rh',t('a.rh'),'%RH',40,95,1,a.rh.toFixed(0))
      + sl('a','d',t('a.days'),'d',0,40,1,a.d.toFixed(0))
      + sl('a','hist',t('a.hist'),'',0,0.2,0.005,a.hist.toFixed(3))
      + sl('a','cfp',t('a.cfp'),'$',5,200,5,'$'+a.cfp)
      + sl('a','cfn',t('a.cfn'),'$',100,5000,50,'$'+money(a.cfn))
      + sl('a','tmin',t('a.tmin'),'',0.05,0.30,0.01,a.tmin.toFixed(2));
  } else if(j==='b'){
    const b=state.b;
    controls = sl('b','roots',t('b.roots'),'',0,20,1,b.roots)
      + sl('b','brown',t('b.brown'),'0–100',0,100,1,b.brown)
      + sl('b','shoot',t('b.shoot'),'cm',0.5,8,0.1,b.shoot.toFixed(1))
      + sl('b','leaf',t('b.leaf'),'',0,100,1,b.leaf)
      + sl('b','wax',t('b.wax'),'',0,100,1,b.wax)
      + sl('b','water',t('b.water'),'%',0,30,0.5,b.water.toFixed(1))
      + sl('b','cont',t('b.cont'),'',0,1,0.01,b.cont.toFixed(2));
  } else {
    const c=state.c;
    controls = sl('c','ec',t('c.ec'),'mS/cm',0.6,2.4,0.02,c.ec.toFixed(2))
      + sl('c','ph',t('c.ph'),'',4.8,7,0.02,c.ph.toFixed(2))
      + sl('c','vpd',t('c.vpd'),'kPa',0.3,1.8,0.02,c.vpd.toFixed(2))
      + sl('c','t',t('c.temp'),'°C',18,30,0.5,c.t.toFixed(1))
      + sl('c','do',t('c.do'),'mg/L',3,9,0.1,c.do.toFixed(1))
      + sl('c','drop',t('c.drop'),'µm',10,80,1,c.drop)
      + sl('c','wt',t('c.wt'),'°C',16,28,0.5,c.wt.toFixed(1))
      + sl('c','ws',t('c.ws'),'',0,1,0.05,c.ws.toFixed(2))
      + sl('c','wc',t('c.wc'),'',0,1,0.05,c.wc.toFixed(2))
      + sl('c','wq',t('c.wq'),'',0,1,0.05,c.wq.toFixed(2));
  }
  return `<div class="nav"><h1>${t('tab.judges')}</h1></div>
    ${seg}
    <div class="group"><div class="card">${controls}</div></div>
    <div id="verdict"></div><div id="jsonbox"></div>
    <button class="btn" data-act="log">${t('judge.run')}</button>`;
}

function verdictHTML(){
  const j = state.judge;
  if(j==='a'){
    const r = judgeContamination(state.a);
    const cls = r.decision==='isolate_and_sample'?'bad':(r.decision==='review_microscopy'?'warn':'');
    const lo=r.tauLo*100, hi=r.tauHi*100, p=r.p*100;
    const reason = r.decision==='isolate_and_sample'
      ? `p=${p.toFixed(0)}% ≥ τ_hi ${hi.toFixed(1)}%`
      : r.decision==='review_microscopy'
        ? `p=${p.toFixed(0)}% ∈ [${lo.toFixed(1)}%, ${hi.toFixed(1)}%)`
        : `p=${p.toFixed(0)}% < τ_lo ${lo.toFixed(1)}%`;
    return {html:`<div class="verdict ${cls}">
        <span class="badge ${cls==='bad'?'b-bad':cls==='warn'?'b-warn':'b-ok'}">${t('judge.verdict')}</span>
        <div class="dec">${r.decision}</div>
        <div class="why">${reason}${r.ood?' · OOD':''}</div>
        <div class="bar">
          <div class="z" style="width:${lo}%;background:rgba(48,209,88,.35)"></div>
          <div class="z" style="width:${hi-lo}%;background:rgba(255,159,10,.32)"></div>
          <div class="z" style="width:${100-hi}%;background:rgba(255,69,58,.32)"></div>
          <div class="mk" style="inset-inline-start:${clamp(p,0,100)}%"></div>
        </div>
        <div class="meters">
          <div class="meter"><div class="k">${t('m.p')}</div><div class="v">${(r.p*100).toFixed(1)}%</div></div>
          <div class="meter"><div class="k">${t('m.tc')}</div><div class="v">${(r.tauCost*100).toFixed(1)}%</div></div>
          <div class="meter"><div class="k">${t('m.thi')}</div><div class="v">${(r.tauHi*100).toFixed(1)}%</div></div>
          <div class="meter"><div class="k">${t('m.tlo')}</div><div class="v">${(r.tauLo*100).toFixed(1)}%</div></div>
          <div class="meter"><div class="k">${t('m.conf')}</div><div class="v">${r.conf.toFixed(2)}</div></div>
          <div class="meter"><div class="k">${t('m.ood')}</div><div class="v">${r.ood?'yes':'no'}</div></div>
        </div></div>`,
      json:{agent:'Napell Agent',stage:'aseptic_establishment',jev_type:'noul',decision:r.decision,
        confidence:r.conf,p:r4(r.p),tau_cost:r4(r.tauCost),tau_hi:r4(r.tauHi),tau_lo:r4(r.tauLo),
        human_review:r.conf<0.7||r.ood,reason_codes:r.reasons,sop_version:'coffee-tc-aero-v1.0'}};
  }
  if(j==='b'){
    const r = judgeReadiness(state.b);
    const cls = r.decision==='continue_acclimation'?'bad':(r.decision==='delay_adjust'?'warn':'');
    return {html:`<div class="verdict ${cls}">
        <span class="badge ${cls==='bad'?'b-bad':cls==='warn'?'b-warn':'b-ok'}">${t('judge.verdict')}</span>
        <div class="dec">${r.decision} · ${r.score}/100</div>
        ${r.caps.length?`<div class="why">${r.caps.join(" · ")}</div>`:''}
        <div class="bar">
          <div class="z" style="width:60%;background:rgba(255,69,58,.28)"></div>
          <div class="z" style="width:20%;background:rgba(255,159,10,.28)"></div>
          <div class="z" style="width:20%;background:rgba(48,209,88,.30)"></div>
          <div class="mk" style="inset-inline-start:${clamp(r.score,0,100)}%"></div>
        </div>
        <div class="meters">
          <div class="meter"><div class="k">${t('m.conf')}</div><div class="v">${r.conf.toFixed(2)}</div></div>
          <div class="meter"><div class="k">readiness</div><div class="v">${r.score}</div></div>
        </div></div>`,
      json:{agent:'Napell Agent',stage:'acclimation',jev_type:'score',decision:r.decision,
        readiness:r.score,confidence:r.conf,subscores:r.subs.map(v=>Math.round(v)),caps:r.caps,
        human_review:r.decision==='transplant_ready'||r.conf<0.7,sop_version:'coffee-tc-aero-v1.0'}};
  }
  const r = judgeFog(state.c);
  const bad = r.decision==='stop_and_review';
  return {html:`<div class="verdict ${bad?'bad':''}">
      <span class="badge ${bad?'b-bad':'b-ok'}">${t('judge.verdict')}</span>
      <div class="dec">${r.decision}</div>
      <div class="why">${r.best?('utility '+r.best.utility.toFixed(3)+' · p='+(r.conf*100).toFixed(0)+'%'):'no feasible option'}</div>
      <div class="meters">
        ${r.options.slice(0,4).map(o=>`<div class="meter"><div class="k">${o.action}</div>
          <div class="v">${o.feasible?(o.p*100).toFixed(0)+'%':'×'}</div></div>`).join('')}
      </div></div>`,
    json:{agent:'Napell Agent',stage:'aeroponics_nutrition',jev_type:'choice',decision:r.decision,
      confidence:r.conf,options:r.options.map(o=>({action:o.action,feasible:o.feasible,utility:r4(o.utility),p:r4(o.p)})),
      human_review:!r.best||r.conf<0.7,sop_version:'coffee-tc-aero-v1.0'}};
}

function screenMap(){
  return `<div class="nav"><h1>${t('tab.map')}</h1></div>
    <div class="note" style="margin-bottom:14px">${t('map.title')}</div>
    <div class="group"><div class="card">
      ${NODES.map(n=>`<div class="row" data-node="${n.id}">
        <div class="txt"><div class="t"><span style="font-family:var(--mono);font-size:11px;color:var(--tx3);margin-inline-end:8px">${String(n.id).padStart(2,'0')}</span>${t('node.'+n.id)}</div>
        <div class="s">${n.jev} · ${n.stage}</div></div>${chev}</div>`).join('')}
    </div></div>`;
}

function screenReview(){
  const items = [
    {id:'RV-2411', decision:'delay_adjust', cls:'b-warn',
     zh:'建议延迟 3–7 天', en:'Suggests delay 3–7 days', ar:'يقترح تأخير 3–7 أيام'},
    {id:'RV-2413', decision:'stop_and_review', cls:'b-bad',
     zh:'全部候选不可行', en:'No feasible option', ar:'لا خيار ممكن'}
  ];
  const ledger = state.ledger.length
    ? state.ledger.slice().reverse().map(e=>`<div class="row"><div class="txt">
        <div class="t" style="font-family:var(--mono);font-size:13px">#${e.seq} ${e.stage} → ${e.decision}</div>
        <div class="s" style="font-family:var(--mono);font-size:11px">${e.hash.slice(0,12)}… p=${e.conf??'—'}</div>
      </div></div>`).join('')
    : `<div class="empty">${t('rev.empty')}</div>`;
  const ok = state.ledger.length ? chainOk() : null;
  return `<div class="nav"><h1>${t('tab.review')}</h1></div>
    <div class="group"><div class="h">${t('rev.queue')}</div><div class="card">
      ${items.map(it=>`<div class="row" data-review="${it.id}"><div class="txt">
        <div class="t"><span class="badge ${it.cls}" style="margin-inline-end:6px">${it.id}</span>${it.decision}</div>
        <div class="s">${it[state.lang]||it.en}</div></div>${chev}</div>`).join('')}
    </div></div>
    <div class="group"><div class="h">${t('rev.ledger')}
      <span class="badge ${ok===null?'b-gray':(ok?'b-ok':'b-bad')}" style="margin-inline-start:6px">
        ${ok===null?'—':t(ok?'rev.ok':'rev.bad')}</span></div>
      <div class="card">${ledger}</div></div>`;
}

function screenMore(){
  const e = state.econ;
  const loss0 = e.c0/100 + (1-e.c0/100)*(1-e.s0/100);
  const loss1 = e.c1/100 + (1-e.c1/100)*(1-e.s1/100);
  const gain = e.n*e.v*(loss0-loss1);
  const net = gain - e.opex;
  const pay = net>0 ? e.capex/(net/12) : null;
  const cpd = (e.capex/3 + e.opex)/(e.d*365);
  return `<div class="nav"><h1>${t('tab.more')}</h1></div>
    <div class="group"><div class="h">${t('dev.platform')}</div><div class="card">
      ${row(t('dev.platform'), state.platform || t('dev.demo'), state.live ? '✓' : (state.liveErr ? '!' : '—'))}
      <div class="row" data-act="platform"><div class="txt"><div class="t">${t('dev.connect')}</div></div>${chev}</div>
    </div><div class="note">${t('dev.hint')}</div></div>
    <div class="group"><div class="h">${t('more.lang')}</div><div class="card">
      ${['zh','en','ar'].map(l=>`<div class="row" data-lang="${l}"><div class="txt">
        <div class="t">${l==='zh'?'中文':l==='en'?'English':'العربية'}</div>
        <div class="s">${l==='zh'?'普通话':l==='en'?'English':'Arabic (Saudi Arabia)'}</div></div>
        ${state.lang===l?'<span class="badge b-ok">✓</span>':''}</div>`).join('')}
    </div></div>
    <div class="group"><div class="h">${t('more.econ')}</div><div class="card">
      ${row(t('econ.gain'),'','$'+money(gain))}
      ${row(t('econ.pay'),'',pay?pay.toFixed(1):'∞')}
      ${row(t('econ.net'),'','$'+money(net))}
      ${row(t('econ.cpd'),'','$'+cpd.toFixed(3))}
    </div><div class="note">${t('econ.n')} ${money(e.n)} · ${t('econ.v')} ${e.v}</div></div>
    <div class="group"><div class="h">${t('more.api')}</div><div class="card">
      <div class="row" data-act="api"><div class="txt"><div class="t">POST /coffee-jev/decide</div>
        <div class="s">${t('more.api.try')}</div></div>${chev}</div>
    </div></div>
    <div class="group"><div class="h">${t('more.about')}</div><div class="card">
      ${row(t('about.sop'),'','coffee-tc-aero-v1.0')}
      ${row(t('about.model'),'','noul · score · choice')}
      ${row(t('about.build'),'','1.0 · 2026-11')}
    </div><div class="note">${t('about.body')}</div></div>`;
}


/* ---------------- devices ---------------- */
async function syncLive(){
  if(!state.platform){ state.live = null; state.liveErr = ''; return; }
  try{
    const r = await fetch(state.platform.replace(/\/+$/,'') + '/api/overview', {cache:'no-store'});
    if(!r.ok) throw new Error('HTTP ' + r.status);
    state.live = await r.json(); state.liveErr = '';
  }catch(e){ state.live = null; state.liveErr = e.message || 'error'; }
}

function screenDevices(){
  const ds = fleet();
  const al = liveAlarms();
  const conn = state.platform
    ? (state.liveErr ? `<span class="badge b-bad">${t('dev.err')}</span>`
       : state.live ? `<span class="badge b-ok">${t('dev.live')}</span>`
       : `<span class="badge b-gray">…</span>`)
    : `<span class="badge b-gray">${t('dev.demo')}</span>`;
  const kpi = state.live ? `
    <div class="hero" style="padding:14px">
      <div class="k">${t('dev.ingest')}</div>
      <div class="big" style="font-size:34px">${state.live.ingest.messages}<small> msgs</small></div>
      <div style="font-size:12px;color:var(--tx2)">${state.live.ingest.rate_per_min} ${t('dev.rate')} · ${state.live.ingest.values} ${t('dev.values')}</div>
    </div>` : '';
  return `<div class="nav"><h1>${t('tab.devices')}</h1>
      <div class="actions"><button class="iconbtn" data-act="platform" aria-label="platform">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/><circle cx="8" cy="7" r="1.4" fill="currentColor"/></svg>
      </button></div></div>
    <div style="margin:0 16px 14px;display:flex;align-items:center;gap:8px">
      <div class="mono" style="font-size:11px;color:var(--tx3);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(state.platform || t('dev.demo'))}</div>${conn}
    </div>
    ${kpi}
    ${al.length ? `<div class="group"><div class="h">${t('dev.open')} · ${al.length}</div><div class="card">
      ${al.slice(0,3).map(a=>`<div class="row" data-ack="${esc(a.id)}">
        <div class="txt"><div class="t"><span class="badge ${a.severity==='critical'?'b-bad':'b-warn'}" style="margin-inline-end:6px">${esc(a.severity)}</span>${esc(a.type)}</div>
        <div class="s">${esc(a.message)}</div></div>
        <span class="badge b-gray">${t('dev.ack')}</span></div>`).join('')}
    </div></div>` : ''}
    <div class="group"><div class="h">${ds.length} ${t('tab.devices')}</div><div class="card">
      ${ds.map(d=>`<div class="row" data-dev="${esc(d.name)}">
        <div class="txt"><div class="t" style="display:flex;align-items:center;gap:6px">
          <span style="width:7px;height:7px;border-radius:50%;background:${d.online?'var(--green)':'#5d6673'}"></span>${esc(d.name)}</div>
          <div class="s">${esc(d.profile)} · ${d.transport=='mqtt'?'MQTT':'HTTP'}</div></div>
        <div class="v mono" style="font-size:11px">${Object.entries(d.last||{}).slice(0,2).map(([k,v])=>`${k}=${typeof v==='number'?fmtShort(v):v}`).join(' ')}</div>
        ${chev}</div>`).join('')}
    </div></div>
    <div class="note">${t('dev.hint')}</div>`;
}

const fmtShort = v => Number.isInteger(v) ? String(v) : (Math.abs(v)>=100 ? v.toFixed(0) : Math.abs(v)>=10 ? v.toFixed(1) : v.toFixed(2));

function openDeviceSheet(name){
  const d = fleet().find(x=>x.name===name);
  if(!d) return;
  const kv = Object.entries(d.last||{}).map(([k,v])=>`<div class="meter"><div class="k">${esc(k)}</div><div class="v">${typeof v==='number'?fmtShort(v):esc(v)}</div></div>`).join('');
  const isFog = name.indexOf('fog-ctrl')===0;
  const isValve = name.indexOf('valve')===0;
  openSheet(`<h2>${esc(d.name)}</h2>
    <div style="padding:0 20px 10px;display:flex;gap:6px;flex-wrap:wrap">
      <span class="badge ${d.online?'b-ok':'b-gray'}">${d.online?t('dev.online'):t('dev.offline')}</span>
      <span class="badge b-info">${d.transport=='mqtt'?'MQTT':'HTTP'}</span>
      <span class="badge b-gray">${esc(d.profile)}</span>
    </div>
    <div class="meters" style="padding:0 16px">${kv}</div>
    ${(isFog||isValve)?`<div style="display:flex;gap:8px;padding:14px 16px 4px">
      ${isFog?`<button class="btn sm" data-rpc="set_fog_recipe">${t('dev.rpc')}<br><span style="font-size:10px">EC 1.35 · pH 5.90</span></button>
               <button class="btn sm ghost" data-rpc="stop_fog">stop_fog</button>`
              :`<button class="btn sm" data-rpc="open">open</button><button class="btn sm ghost" data-rpc="close">close</button>`}
    </div>`:''}
    <div id="rpcMsg" style="padding:8px 20px 16px;font-size:12px;color:var(--tx3)"></div>`);
}

async function sendRpc(method){
  const msg = document.getElementById('rpcMsg');
  const name = document.getElementById('sheetBody').querySelector('h2').textContent;
  if(!state.platform){ if(msg) msg.textContent = t('dev.demo'); return; }
  const params = method==='set_fog_recipe' ? {ec:1.35, ph:5.9} : {};
  try{
    const r = await fetch(state.platform.replace(/\/+$/,'') + '/api/rpc', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({device:name, method, params})
    });
    const body = await r.json().catch(()=>({}));
    if(!r.ok){
      if(msg) msg.textContent = t('dev.rpc.blocked') + ' · ' + (body.error||r.status);
      return;
    }
    if(msg) msg.textContent = t('dev.rpc.ok') + ' · #' + body.rpc.id;
    setTimeout(syncLive, 900);
  }catch(e){ if(msg) msg.textContent = t('dev.err') + ': ' + e.message; }
}

/* ---------------- render ---------------- */
const TABS = [
  ['home','M3 11l9-7 9 7v9a1 1 0 01-1 1h-5v-6H9v6H4a1 1 0 01-1-1z'],
  ['judges','M4 7h9M17 7h3M4 12h3M11 12h9M4 17h11M19 17h1'],
  ['devices','M6 8h3v3H6zM6 14h3v3H6zM12 9.5h7M12 15.5h7'],
  ['map','M9 4l6 2 5-2v14l-5 2-6-2-5 2V6zM9 4v14M15 6v14'],
  ['review','M4 12.5l5 5L20 6.5'],
  ['more','M6 12h.01M12 12h.01M18 12h.01']
];

function render(){
  const s = document.getElementById('scroll');
  const html = state.tab==='home'?screenHome()
    : state.tab==='judges'?screenJudges()
    : state.tab==='devices'?screenDevices()
    : state.tab==='map'?screenMap()
    : state.tab==='review'?screenReview()
    : screenMore();
  s.innerHTML = html;
  document.getElementById('tabbar').innerHTML = TABS.map(([id,d])=>`
    <button class="tab ${state.tab===id?'on':''}" data-tab="${id}">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="${d}"/></svg>
      <span>${t('tab.'+id)}</span></button>`).join('');
  if(state.tab==='judges') refreshJudge();
}

function refreshJudge(){
  const v = verdictHTML();
  const vd = document.getElementById('verdict');
  const jb = document.getElementById('jsonbox');
  if(vd) vd.innerHTML = v.html;
  if(jb) jb.innerHTML = `<div class="json">${hl(v.json)}</div>`;
}

/* ---------------- language ---------------- */
function applyLang(l){
  state.lang = l;
  localStorage.setItem('napell-lang', l);
  document.documentElement.lang = LANG_META[l].locale;
  document.documentElement.dir = LANG_META[l].dir;
  document.documentElement.dataset.lang = l;
  render();
}

/* ---------------- sheet ---------------- */
function openSheet(html){
  document.getElementById('sheetBody').innerHTML = html;
  document.getElementById('backdrop').classList.add('on');
  document.getElementById('sheet').classList.add('on');
}
function closeSheet(){
  document.getElementById('backdrop').classList.remove('on');
  document.getElementById('sheet').classList.remove('on');
}

/* ---------------- events ---------------- */
document.getElementById('scroll').addEventListener('input', ev=>{
  const el = ev.target;
  if(el.type!=='range') return;
  const g = el.dataset.g, k = el.dataset.k, val = parseFloat(el.value);
  state[g][k] = val;
  const lab = document.getElementById('v-'+k);
  if(lab){
    const dec = parseInt(el.dataset.fmt || '1', 10);
    lab.textContent = (k==='hist') ? val.toFixed(3) : val.toFixed(dec);
  }
  refreshJudge();
});

document.getElementById('scroll').addEventListener('click', ev=>{
  const el = ev.target.closest('[data-tab],[data-goto],[data-judge],[data-node],[data-review],[data-lang],[data-act]');
  if(!el) return;

  if(el.dataset.tab){ state.tab = el.dataset.tab; render(); return; }
  if(el.dataset.goto){ state.tab = el.dataset.goto; if(el.dataset.judge) state.judge = el.dataset.judge; render(); return; }
  if(el.dataset.judge){ state.judge = el.dataset.judge; render(); return; }
  if(el.dataset.lang){ applyLang(el.dataset.lang); return; }

  if(el.dataset.dev){ openDeviceSheet(el.dataset.dev); return; }
  if(el.dataset.ack){ ackAlarm(el.dataset.ack); return; }
  if(el.dataset.act==='platform'){ openPlatformSheet(); return; }
  if(el.dataset.node){
    const n = NODES.find(x=>x.id===+el.dataset.node);
    const [d,e] = nodeTxt(n);
    openSheet(`<h2>${t('node.'+n.id)}</h2><div class="kv">
      <div class="kvrow"><div class="k">${t('map.inputs')} → ${t('map.outputs')}</div><div class="v">${esc(d)}</div></div>
      <div class="kvrow"><div class="k">${t('map.esc')}</div><div class="v">${esc(e)}</div></div>
      <div class="kvrow"><div class="k">jev_type / stage</div><div class="v" style="font-family:var(--mono)">${n.jev} · ${n.stage}</div></div>
    </div>`);
    return;
  }

  if(el.dataset.review){
    const id = el.dataset.review;
    openSheet(`<h2>${id}</h2><div class="kv">
      <div class="kvrow"><div class="k">${t('judge.verdict')}</div>
      <div class="v">${id==='RV-2411'?'delay_adjust · 79/100':'stop_and_review · pH 5.24'}</div></div>
      <div class="kvrow"><div class="k">${t('map.esc')}</div><div class="v">${id==='RV-2411'?'boundary_zone':'sensor_unhealthy'}</div></div>
    </div>
    <div style="display:flex;gap:8px;padding:0 16px 8px">
      <button class="btn sm ghost" data-act="rv-accept">${t('rev.accept')}</button>
      <button class="btn sm ghost" data-act="rv-override">${t('rev.override')}</button>
      <button class="btn sm" data-act="rv-need">${t('rev.need')}</button>
    </div>`);
    return;
  }

  if(el.dataset.act==='log'){
    const v = verdictHTML();
    pushLedger({stage:v.json.stage, decision:v.json.decision, conf:v.json.confidence, at:Date.now()});
    state.tab = 'review'; render(); return;
  }
  if(el.dataset.act==='api'){
    const v = verdictHTML();
    openSheet(`<h2>POST /coffee-jev/decide</h2>
      <div class="json" style="margin:0 16px 14px">${hl({stage:v.json.stage,jev_type:v.json.jev_type,decision:v.json.decision,confidence:v.json.confidence,sop_version:v.json.sop_version})}</div>`);
    return;
  }
});

function openPlatformSheet(){
  openSheet(`<h2>${t('dev.platform')}</h2>
    <div style="padding:6px 20px 12px">
      <input id="platInput" type="text" inputmode="url" placeholder="http://127.0.0.1:8090"
        value="${esc(state.platform)}" style="width:100%">
      <div style="display:flex;gap:8px;margin-top:12px">
        <button class="btn sm ghost" data-act="plat-clear">${t('dev.demo')}</button>
        <button class="btn sm" data-act="plat-save">${t('dev.connect')}</button>
      </div>
      <div id="platMsg" style="margin-top:10px;font-size:12px;color:var(--tx3)">${t('dev.hint')}</div>
    </div>`);
}

async function ackAlarm(id){
  if(!state.platform) return;
  try{
    await fetch(state.platform.replace(/\/+$/,'') + '/api/alarms/'+encodeURIComponent(id)+'/ack', {method:'POST'});
    await syncLive(); render();
  }catch(e){}
}

document.getElementById('sheet').addEventListener('click', async ev=>{
  const rpc = ev.target.closest('[data-rpc]');
  if(rpc){ sendRpc(rpc.dataset.rpc); return; }
  const actEl = ev.target.closest('[data-act]');
  if(actEl && actEl.dataset.act==='plat-save'){
    const v = (document.getElementById('platInput').value || '').trim().replace(/\/+$/,'');
    state.platform = v; localStorage.setItem('napell-platform', v);
    const m = document.getElementById('platMsg');
    if(m) m.textContent = '…';
    await syncLive();
    if(m) m.textContent = state.liveErr ? (t('dev.err') + ' · ' + state.liveErr) : `${t('dev.live')} · ${(state.live&&state.live.devices.length)||0} ${t('tab.devices')}`;
    render(); return;
  }
  if(actEl && actEl.dataset.act==='plat-clear'){
    state.platform=''; localStorage.removeItem('napell-platform'); state.live=null; state.liveErr='';
    closeSheet(); render(); return;
  }
  const lang = ev.target.closest('[data-lang]');
  if(lang){ applyLang(lang.dataset.lang); closeSheet(); return; }
  const act = ev.target.closest('[data-act]');
  if(act && act.dataset.act.startsWith('rv-')){
    pushLedger({stage:'review', decision:'reviewer_'+act.dataset.act.slice(3), conf:null, at:Date.now()});
    closeSheet(); state.tab='review'; render();
  }
});
document.getElementById('backdrop').addEventListener('click', closeSheet);

/* clock + boot */
function tick(){
  const d = new Date();
  const el = document.getElementById('clock');
  if(el) el.textContent = String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0');
}
tick(); setInterval(tick, 20000);

pushLedger({stage:'aseptic_establishment', decision:'review_microscopy', conf:0.59, at:Date.now()});
if(state.platform){ syncLive().then(render); setInterval(()=>{ if(state.platform) syncLive().then(()=>{ if(['devices','more'].includes(state.tab)) render(); }); }, 6000); }
const _qs = new URLSearchParams(location.search);
const _q = _qs.get('lang');
if(['home','judges','devices','map','review','more'].includes(_qs.get('tab'))) state.tab = _qs.get('tab');
if(['a','b','c'].includes(_qs.get('judge'))) state.judge = _qs.get('judge');
applyLang(['zh','en','ar'].includes(_q) ? _q : state.lang);





