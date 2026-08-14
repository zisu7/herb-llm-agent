import re
import json
from pathlib import Path
from datetime import datetime
from src.agents.agent_constitution import constitution_analysis
from src.agents.agent_herb_match import herb_matching_agent
from src.agents.agent_food_recipe import food_recipe_agent


def extract_json(raw_text: str) -> str:
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, raw_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return raw_text.strip()


# ========== 本地药材安全校验：高危药材黑名单 + 安全药食同源替换池 ==========
# 高危药材黑名单（毒性药材、峻烈猛药，均不属于药食同源，禁止进入药膳输出）
HIGH_RISK_HERB_BLACKLIST = {
    # 有毒类
    "附子", "川乌", "草乌", "雪上一枝蒿", "马钱子", "斑蝥", "蟾酥", "生半夏", "生南星",
    "生川乌", "生草乌", "雷公藤", "巴豆", "牵牛子", "甘遂", "京大戟", "芫花", "商陆",
    "狼毒", "川楝子", "苦楝皮", "朱砂", "雄黄", "轻粉", "砒石", "砒霜", "洋金花",
    "香加皮", "北豆根", "山豆根",
    # 峻下逐水 / 峻烈泻下类
    "大黄", "芒硝", "玄明粉", "番泻叶", "芦荟",
    # 破血逐瘀峻烈类
    "莪术", "三棱", "水蛭", "虻虫", "穿山甲", "干漆", "土鳖虫", "㒆虫",
    # 开窍峻烈类
    "麝香",
}

# 安全药食同源替换池（命中黑名单时按序补位，自动规避与已有药材重名）
SAFE_FOOD_HERB_POOL = [
    {"name": "山药", "usage": "10-30g", "nature_channel": "甘平，归脾肺肾经", "reason": "药食同源，平和补脾益气"},
    {"name": "大枣", "usage": "6-15g", "nature_channel": "甘温，归脾胃经", "reason": "药食同源，补中益气养血安神"},
    {"name": "枸杞子", "usage": "6-12g", "nature_channel": "甘平，归肝肾经", "reason": "药食同源，滋补肝肾益精明目"},
    {"name": "百合", "usage": "6-12g", "nature_channel": "甘微寒，归心肺经", "reason": "药食同源，润肺清心安神"},
    {"name": "莲子", "usage": "6-15g", "nature_channel": "甘涩平，归脾肾心经", "reason": "药食同源，补脾止泻养心安神"},
    {"name": "薏苡仁", "usage": "9-30g", "nature_channel": "甘淡凉，归脾胃肺经", "reason": "药食同源，健脾利湿"},
    {"name": "龙眼肉", "usage": "9-15g", "nature_channel": "甘温，归心脾经", "reason": "药食同源，补益心脾养血安神"},
    {"name": "陈皮", "usage": "3-9g", "nature_channel": "辛苦温，归脾肺经", "reason": "药食同源，理气健脾燥湿"},
    {"name": "菊花", "usage": "5-9g", "nature_channel": "辛甘苦微寒，归肺肝经", "reason": "药食同源，疏散风热清肝明目"},
    {"name": "决明子", "usage": "9-15g", "nature_channel": "甘苦咸微寒，归肝大肠经", "reason": "药食同源，清热明目润肠"},
    {"name": "玉竹", "usage": "6-12g", "nature_channel": "甘微寒，归肺胃经", "reason": "药食同源，养阴润燥生津"},
    {"name": "黄精", "usage": "9-15g", "nature_channel": "甘平，归脾肺肾经", "reason": "药食同源，补气养阴健脾润肺"},
]


def safety_check_herbs(res_herb: dict) -> dict:
    """
    本地高危药材校验拦截：
    扫描 Agent2 输出的 selected_herbs 与代茶饮材料，
    命中黑名单的高危药材直接剔除，补位替换为安全药食同源药材，
    并把被剔除药材计入 avoid_herbs；命中时在控制台输出提示。
    """
    if not isinstance(res_herb, dict):
        return res_herb

    selected = res_herb.get("selected_herbs") or []
    existing_names = {h.get("name", "").strip() for h in selected if isinstance(h, dict)}
    new_selected = []
    detected = []
    pool_idx = 0

    def _next_safe_replacement():
        nonlocal pool_idx
        while pool_idx < len(SAFE_FOOD_HERB_POOL):
            cand = SAFE_FOOD_HERB_POOL[pool_idx]
            pool_idx += 1
            if cand["name"] not in existing_names:
                return dict(cand)
        return None

    # 1) 主药材清单校验
    for herb in selected:
        if not isinstance(herb, dict):
            new_selected.append(herb)
            continue
        name = (herb.get("name") or "").strip()
        if name and name in HIGH_RISK_HERB_BLACKLIST:
            detected.append(name)
            replacement = _next_safe_replacement()
            if replacement:
                new_selected.append(replacement)
                existing_names.add(replacement["name"])
        else:
            new_selected.append(herb)
    res_herb["selected_herbs"] = new_selected

    # 2) 代茶饮材料校验（materials 可能是 list 或 string）
    tea = res_herb.get("tea_recipe") or {}
    materials = tea.get("materials")
    # 先登记代茶饮中已有的安全药材名，避免替换时与之重名
    if isinstance(materials, list):
        for m in materials:
            mname = m if isinstance(m, str) else (m.get("name", "") if isinstance(m, dict) else str(m))
            mname = mname.strip()
            if mname and mname not in HIGH_RISK_HERB_BLACKLIST:
                existing_names.add(mname)
    elif isinstance(materials, str):
        for t in re.split(r"[、,，\s]+", materials):
            t = t.strip()
            if t and t not in HIGH_RISK_HERB_BLACKLIST:
                existing_names.add(t)
    if isinstance(materials, list):
        new_materials = []
        for m in materials:
            mname = m if isinstance(m, str) else (m.get("name", "") if isinstance(m, dict) else str(m))
            mname = mname.strip()
            if mname and mname in HIGH_RISK_HERB_BLACKLIST:
                if mname not in detected:
                    detected.append(mname)
                replacement = _next_safe_replacement()
                if replacement:
                    new_materials.append(replacement["name"])
                    existing_names.add(replacement["name"])
            else:
                new_materials.append(m)
        tea["materials"] = new_materials
    elif isinstance(materials, str):
        tokens = [t for t in re.split(r"[、,，\s]+", materials) if t]
        changed = False
        new_tokens = []
        for t in tokens:
            if t.strip() and t.strip() in HIGH_RISK_HERB_BLACKLIST:
                if t.strip() not in detected:
                    detected.append(t.strip())
                replacement = _next_safe_replacement()
                if replacement:
                    new_tokens.append(replacement["name"])
                    existing_names.add(replacement["name"])
                changed = True
            else:
                new_tokens.append(t)
        if changed:
            tea["materials"] = "、".join(new_tokens)
    res_herb["tea_recipe"] = tea

    # 3) 把命中黑名单的药材追加进 avoid_herbs
    avoid = res_herb.get("avoid_herbs") or []
    if isinstance(avoid, list):
        avoid_set = {a for a in avoid if isinstance(a, str)}
        for d in detected:
            avoid_set.add(d)
        res_herb["avoid_herbs"] = sorted(avoid_set)

    # 4) 控制台提示
    if detected:
        print(f"⚠️ 检测到高危药材：{'、'.join(detected)}，已做替换为安全药食同源药材。")
    else:
        print("✅ 本地药材安全校验通过，未发现高危药材。")
    return res_herb


def export_consultation_txt(user_dialog_text: str, result: dict, save_dir=None) -> str:
    """
    将本次问诊结果导出为本地txt文件，保存到项目根目录。
    仅在用户明确选择“是”时由调用方触发，禁止自动导出。
    返回：保存文件绝对路径；失败返回以“导出失败：”开头的说明字符串。
    """
    try:
        if save_dir is None:
            # food_pipeline.py 位于 herb-llm-agent/src/，项目根目录 = 上三级目录
            save_dir = Path(__file__).resolve().parent.parent.parent
        save_dir = Path(save_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = save_dir / f"问诊记录_{timestamp}.txt"

        constitution_info = result.get("constitution_info", {}) or {}
        selected_herbs = result.get("selected_herbs", {}) or {}
        food_md = result.get("food_scheme_markdown", "") or ""

        lines = []
        lines.append("=" * 60)
        lines.append("药膳问诊记录")
        lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)

        lines.append("\n【一、用户口述信息】")
        lines.append(user_dialog_text.strip() if user_dialog_text else "（无）")

        lines.append("\n【二、体质倾向】")
        lines.append(f"核心体质：{constitution_info.get('main_constitution', '')}")
        lines.append(f"兼夹体质：{constitution_info.get('secondary_constitution', '')}")
        lines.append(f"特殊人群：{constitution_info.get('special_population', '无')}")
        lines.append(f"推理依据：{constitution_info.get('reason_analysis', '')}")
        lines.append(f"养生禁忌&风险提示：{constitution_info.get('special_taboo', '')}")

        lines.append("\n【三、适配药材与代茶饮】")
        for herb in selected_herbs.get("selected_herbs", []) or []:
            lines.append(
                f"【{herb.get('name', '')}】用量：{herb.get('usage', '')}"
                f"｜性味归经：{herb.get('nature_channel', '')}｜适配理由：{herb.get('reason', '')}"
            )
        tea = selected_herbs.get("tea_recipe", {}) or {}
        lines.append(f"代茶饮药材：{tea.get('materials', '')}")
        lines.append(f"冲泡方法：{tea.get('method', '')}")
        lines.append(f"注意事项：{tea.get('note', '')}")

        lines.append("\n【四、药膳方案与禁忌】")
        lines.append(food_md)

        lines.append("\n" + "=" * 60)
        lines.append("免责声明：本记录仅作日常养生参考，不能替代执业医师诊疗；如有持续不适请前往正规医疗机构就诊。")
        lines.append("=" * 60)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return str(filepath)
    except Exception as e:
        return f"导出失败：{e}"


def food_pipeline_handler(user_dialog_text: str, user_taboo: str, special_population: str = ""):
     agent1_output = constitution_analysis(user_dialog_text)
     if "【NEED_ASK】" in agent1_output:
         question = agent1_output.replace("【NEED_ASK】", "").strip()
         return {
             "type": "ask",
             "question": question
         }
     json_str = extract_json(agent1_output)
     res_bianzheng = json.loads(json_str)
     # 特殊人群字段以用户在终端直接输入的真实内容为准，禁止程序默认填“无”
     res_bianzheng["special_population"] = special_population
     # Agent1 体质推理打印
     print("\n=====【Agent1 体质辨析推理过程】=====")
     print(f"核心体质：{res_bianzheng['main_constitution']}")
     print(f"兼夹体质：{res_bianzheng['secondary_constitution']}")
     print(f"特殊人群：{res_bianzheng.get('special_population', '无')}")
     print(f"推理依据：{res_bianzheng['reason_analysis']}")
     print(f"养生禁忌&风险提示：{res_bianzheng['special_taboo']}")
     print("=====================================\n")
     print("【日志：开始调用Agent2药材筛选】")
     res_herb = herb_matching_agent(res_bianzheng)
     # 本地高危药材校验拦截：剔除黑名单药材并替换为安全药食同源药材
     res_herb = safety_check_herbs(res_herb)
     print("【日志：Agent2调用完成，开始打印药材信息】")
     # Agent2 输出展示：药材性味归经 + 代茶饮
     print("\n=====【Agent2 适配药材清单（含性味归经）】=====")
     for herb in res_herb["selected_herbs"]:
         print(f"【{herb['name']}】用量：{herb['usage']}｜性味归经：{herb['nature_channel']}｜适配理由：{herb['reason']}")
     print("\n【日常简易代茶饮方案】")
     tea = res_herb["tea_recipe"]
     print(f"药材：{tea['materials']}")
     print(f"冲泡方法：{tea['method']}")
     print(f"注意事项：{tea['note']}")
     print("=====================================\n")
     print("【日志：开始调用Agent3药膳生成】")
     res_food = food_recipe_agent(res_bianzheng, res_herb)
     print("【日志：Agent3调用完成】")
     return {
         "type": "result",
         "constitution_info": res_bianzheng,
         "selected_herbs": res_herb,
         "food_scheme_markdown": res_food
     }