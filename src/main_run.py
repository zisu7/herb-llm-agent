import sys
import os
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.data_loader import load_tcm_herbs, load_food_herbs
from src.agent_entry import (
    research_query,
    health_query,
    is_llm_available,
    food_pipeline_handler,
    export_consultation_txt,
)


def safe_input(prompt=""):
    try:
        return input(prompt)
    except EOFError:
        return "0"


def safe_input_int(prompt="", min_val=None, max_val=None):
    while True:
        try:
            val = safe_input(prompt).strip()
            if not val:
                if min_val is not None:
                    return min_val
                continue
            num = int(val)
            if min_val is not None and num < min_val:
                print(f"请输入 {min_val}-{max_val} 之间的数字")
                continue
            if max_val is not None and num > max_val:
                print(f"请输入 {min_val}-{max_val} 之间的数字")
                continue
            return num
        except ValueError:
            print("输入错误，请输入有效数字")


def display_herbs(herbs_list):
    if not herbs_list:
        print("\n暂无药材数据")
        return
    print(f"\n共找到 {len(herbs_list)} 味药材:")
    print("-" * 100)
    print(f"{'序号':<4} {'名称':<8} {'类别':<10} {'归经':<12} {'功效':<25} {'主要成分':<20} {'用量'}")
    print("-" * 100)
    for i, h in enumerate(herbs_list, 1):
        print(f"{i:<4} {h['name']:<8} {h['category']:<10} {h['meridian']:<12} {h['effect']:<25} {h['component']:<20} {h['dosage']}")
    print("-" * 100)


def display_food_herbs(herbs_list):
    if not herbs_list:
        print("\n暂无药食同源药材数据")
        return
    print(f"\n共找到 {len(herbs_list)} 味药食同源药材:")
    print("-" * 100)
    print(f"{'序号':<4} {'名称':<8} {'类别':<10} {'功效':<25} {'养生用途':<20} {'推荐用量'}")
    print("-" * 100)
    for i, h in enumerate(herbs_list, 1):
        print(f"{i:<4} {h['name']:<8} {h['category']:<10} {h['effect']:<25} {h['usage']:<20} {h['dosage']}")
    print("-" * 100)


def recommend_dietary_therapy(constitution):
    recipes = {
        "气虚质": {
            "desc": "元气不足，易疲劳、气短、自汗",
            "soups": [
                {"name": "黄芪炖鸡汤", "ingredients": ["黄芪15g", "党参10g", "鸡肉500g", "红枣5颗"], "effect": "补气养血，健脾益肺"},
                {"name": "山药薏米粥", "ingredients": ["山药30g", "薏米30g", "大米50g"], "effect": "健脾益气，祛湿养胃"}
            ],
            "teas": [
                {"name": "黄芪红枣茶", "ingredients": ["黄芪5g", "红枣3颗", "枸杞5g"], "effect": "补气养血"},
                {"name": "人参须茶", "ingredients": ["人参须3g", "麦冬5g"], "effect": "益气生津"}
            ],
            "taboos": ["生冷寒凉食物", "辛辣刺激食物", "过度劳累"]
        },
        "阳虚质": {
            "desc": "阳气不足，畏寒怕冷、手脚冰凉",
            "soups": [
                {"name": "当归生姜羊肉汤", "ingredients": ["当归15g", "生姜30g", "羊肉500g"], "effect": "温中散寒，养血补虚"},
                {"name": "肉桂炖牛肉", "ingredients": ["肉桂5g", "牛肉500g", "八角2颗"], "effect": "温补肾阳，散寒止痛"}
            ],
            "teas": [
                {"name": "生姜红枣茶", "ingredients": ["生姜5g", "红枣5颗"], "effect": "温中散寒"},
                {"name": "鹿茸茶", "ingredients": ["鹿茸2g", "枸杞5g"], "effect": "温补肾阳"}
            ],
            "taboos": ["生冷食物", "西瓜、苦瓜等寒性食物", "冷饮"]
        },
        "阴虚质": {
            "desc": "阴液不足，口干咽燥、手足心热",
            "soups": [
                {"name": "百合莲子粥", "ingredients": ["百合30g", "莲子20g", "大米50g"], "effect": "养阴润肺，清心安神"},
                {"name": "麦冬沙参炖老鸭", "ingredients": ["麦冬15g", "沙参15g", "老鸭500g"], "effect": "养阴生津，润肺止咳"}
            ],
            "teas": [
                {"name": "麦冬茶", "ingredients": ["麦冬5g", "玉竹5g"], "effect": "养阴生津"},
                {"name": "枸杞菊花茶", "ingredients": ["枸杞5g", "菊花3g"], "effect": "滋阴明目"}
            ],
            "taboos": ["辛辣燥热食物", "羊肉、狗肉等温性食物", "酒精"]
        },
        "痰湿质": {
            "desc": "体内痰湿积聚，体型肥胖、痰多粘稠",
            "soups": [
                {"name": "冬瓜海带排骨汤", "ingredients": ["冬瓜300g", "海带50g", "排骨500g"], "effect": "清热利湿，化痰消肿"},
                {"name": "陈皮茯苓粥", "ingredients": ["陈皮5g", "茯苓10g", "大米50g"], "effect": "健脾祛湿，理气化痰"}
            ],
            "teas": [
                {"name": "陈皮茶", "ingredients": ["陈皮3g", "荷叶3g"], "effect": "理气化痰"},
                {"name": "薏米茶", "ingredients": ["薏米10g", "赤小豆10g"], "effect": "利水渗湿"}
            ],
            "taboos": ["油腻厚味食物", "甜食", "生冷食物"]
        },
        "湿热质": {
            "desc": "湿热内蕴，口苦口臭、大便黏滞",
            "soups": [
                {"name": "绿豆汤", "ingredients": ["绿豆50g", "冰糖适量"], "effect": "清热解毒，消暑利湿"},
                {"name": "冬瓜薏米汤", "ingredients": ["冬瓜200g", "薏米30g"], "effect": "清热利湿"}
            ],
            "teas": [
                {"name": "金银花茶", "ingredients": ["金银花5g", "连翘3g"], "effect": "清热解毒"},
                {"name": "蒲公英茶", "ingredients": ["蒲公英5g"], "effect": "清热解毒，利湿通淋"}
            ],
            "taboos": ["辛辣刺激食物", "油腻食物", "温热食物"]
        },
        "血瘀质": {
            "desc": "血液运行不畅，面色暗沉、易瘀斑",
            "soups": [
                {"name": "当归川芎炖排骨", "ingredients": ["当归10g", "川芎5g", "排骨500g"], "effect": "活血化瘀，养血调经"},
                {"name": "山楂红糖水", "ingredients": ["山楂10g", "红糖适量"], "effect": "活血化瘀"}
            ],
            "teas": [
                {"name": "红花茶", "ingredients": ["红花2g", "枸杞5g"], "effect": "活血通经"},
                {"name": "丹参茶", "ingredients": ["丹参5g"], "effect": "活血化瘀"}
            ],
            "taboos": ["寒凉凝滞食物", "过饱过饥"]
        },
        "气郁质": {
            "desc": "气机郁滞，情绪抑郁、胸闷嗳气",
            "soups": [
                {"name": "玫瑰花茶", "ingredients": ["玫瑰花5g", "佛手3g"], "effect": "疏肝理气，活血解郁"},
                {"name": "柴胡疏肝粥", "ingredients": ["柴胡5g", "大米50g"], "effect": "疏肝解郁"}
            ],
            "teas": [
                {"name": "茉莉花茶", "ingredients": ["茉莉花3g", "绿茶3g"], "effect": "理气解郁"},
                {"name": "合欢花茶", "ingredients": ["合欢花3g"], "effect": "解郁安神"}
            ],
            "taboos": ["生冷食物", "思虑过度"]
        },
        "特禀质": {
            "desc": "过敏体质，易过敏、皮肤瘙痒",
            "soups": [
                {"name": "黄芪防风粥", "ingredients": ["黄芪10g", "防风5g", "大米50g"], "effect": "益气固表"},
                {"name": "红枣山药粥", "ingredients": ["红枣5颗", "山药30g", "大米50g"], "effect": "健脾养血"}
            ],
            "teas": [
                {"name": "甘草茶", "ingredients": ["甘草3g"], "effect": "调和诸药"},
                {"name": "乌梅茶", "ingredients": ["乌梅3g"], "effect": "敛肺生津"}
            ],
            "taboos": ["过敏原食物", "辛辣刺激食物"]
        }
    }
    if constitution not in recipes:
        print("\n暂不支持该体质类型")
        return
    data = recipes[constitution]
    print(f"\n【{constitution}】{data['desc']}")
    print("\n=== 推荐药膳 ===")
    for i, soup in enumerate(data["soups"], 1):
        print(f"\n{i}. {soup['name']}")
        print(f"   食材: {', '.join(soup['ingredients'])}")
        print(f"   功效: {soup['effect']}")
    print("\n=== 推荐药茶 ===")
    for i, tea in enumerate(data["teas"], 1):
        print(f"\n{i}. {tea['name']}")
        print(f"   食材: {', '.join(tea['ingredients'])}")
        print(f"   功效: {tea['effect']}")
    print("\n=== 配伍禁忌提醒 ===")
    print("禁忌食物/行为:")
    for taboo in data["taboos"]:
        print(f"  • {taboo}")


def main():
    herbs = load_tcm_herbs()
    food_herbs = load_food_herbs()
    categories = sorted(set(h["category"] for h in herbs))
    meridian_list = ["心", "肝", "脾", "肺", "肾", "胃", "大肠", "小肠", "胆", "膀胱", "三焦", "心包"]
    meridians = sorted(m for m in meridian_list if any(m in h["meridian"] for h in herbs))
    while True:
        print("\n========《基于LLM多智能体的中药天然产物研发+药膳智能养生辅助系统》========")
        print("----------【模块一：中药天然产物研发模块｜科研方向，模拟AI制药、天然产物研发】----------")
        print("1.浏览全部药材数据")
        print("2.药名关键词检索药材")
        print("3.按中药类别筛选")
        print("4.按归经条件筛选药材")
        print("5.数据统计功能")
        print("----------【模块二：药膳智能养生辅助模块｜落地应用方向，药食同源】----------")
        print("6.查看全部药食同源药材清单")
        print("7.输入体质（直接提供体质，输出药膳、药茶推荐方案）")
        print("8.问诊系统（多轮采集身体症状，推导体质后生成药膳药茶，附带配伍禁忌提醒）")
        print("0.退出系统")
        try:
            choice = safe_input_int("请输入选择(0-8): ", 0, 8)
        except (ValueError, EOFError):
            print("\n输入错误，请输入数字0-8")
            safe_input("按回车继续...")
            continue
        if choice == 0:
            print("\n感谢使用，再见！")
            break
        elif choice == 1:
            display_herbs(herbs)
        elif choice == 2:
            keyword = safe_input("\n请输入药材名称或研发问题: ").strip()
            if not keyword:
                print("\n输入不能为空")
            else:
                print(f"\n正在检索「{keyword}」...")
                kw_lower = keyword.lower()
                local_matches = []
                for h in herbs:
                    haystack = f"{h.get('name', '')} {h.get('category', '')} {h.get('meridian', '')} {h.get('effect', '')} {h.get('component', '')}".lower()
                    if kw_lower in haystack:
                        local_matches.append(h)
                    elif any(seg.strip() and seg.strip() in haystack for seg in kw_lower.split()):
                        if h not in local_matches:
                            local_matches.append(h)
                if local_matches:
                    print(f"\n{'=' * 60}")
                    print(f"【本地检索】共找到 {len(local_matches)} 味匹配药材")
                    print(f"{'=' * 60}")
                    for i, r in enumerate(local_matches, 1):
                        print(f"  {i}. {r['name']} ({r['category']}) - {r['effect']}")
                        print(f"     归经: {r['meridian']} | 成分: {r['component']} | 用量: {r['dosage']}")
                    try:
                        if is_llm_available():
                            print(f"\n🔍 AI正在拓展天然产物研发资料...")
                            llm_result = research_query(keyword)
                            if llm_result.get("mode") == "llm" and llm_result.get("success"):
                                print(f"\n{'=' * 60}")
                                print(f"【AI研发分析】来源: {llm_result.get('source', 'deepseek-chat')}")
                                print(f"{'=' * 60}")
                                print(llm_result["answer"])
                            elif llm_result.get("error"):
                                print(f"\n⚠️ AI拓展失败: {llm_result['error']}")
                    except Exception:
                        pass
                    if not is_llm_available():
                        print(f"\n💡 配置 DEEPSEEK_API_KEY 后可启用 AI 研发拓展分析")
                else:
                    print(f"\n本地库未找到「{keyword}」，正在搜索扩展数据库...")
                    research_result = research_query(keyword)
                    if research_result.get("mode") == "llm" and research_result.get("success"):
                        print(f"\n{'=' * 60}")
                        print(f"【AI研发分析】来源: {research_result.get('source', 'deepseek-chat')}")
                        print(f"{'=' * 60}")
                        print(research_result["answer"])
                    elif research_result.get("mode") == "local" and research_result.get("success"):
                        print(f"\n{'=' * 60}")
                        print(f"【扩展库检索】(共找到 {len(research_result.get('results', []))} 味)")
                        print(f"{'=' * 60}")
                        print(research_result.get("answer", ""))
                        ext_results = research_result.get("results", [])
                        if ext_results:
                            for i, r in enumerate(ext_results, 1):
                                comp = r.get("component", "") or ", ".join(r.get("components", []))
                                print(f"  {i}. {r['name']} ({r['category']}) - {r['effect']}")
                                print(f"     成分: {comp} | 禁忌: {r.get('contraindication', '')}")
                        else:
                            print(f"\n未找到匹配的药材")
                    else:
                        print(f"\n检索失败: {research_result.get('error', '未知错误')}")
        elif choice == 3:
            print("\n中药类别列表:")
            for i, cat in enumerate(categories, 1):
                print(f"  {i}. {cat}")
            try:
                cat_idx = safe_input_int("请输入类别序号: ", 1, len(categories)) - 1
                if 0 <= cat_idx < len(categories):
                    selected_cat = categories[cat_idx]
                    results = [h for h in herbs if h["category"] == selected_cat]
                    display_herbs(results)
                else:
                    print("\n序号无效")
            except ValueError:
                print("\n输入错误")
        elif choice == 4:
            print("\n归经列表:")
            for i, mer in enumerate(meridians, 1):
                print(f"  {i}. {mer}")
            try:
                mer_idx = safe_input_int("请输入归经序号: ", 1, len(meridians)) - 1
                if 0 <= mer_idx < len(meridians):
                    selected_mer = meridians[mer_idx]
                    results = [h for h in herbs if selected_mer in h["meridian"]]
                    display_herbs(results)
                else:
                    print("\n序号无效")
            except ValueError:
                print("\n输入错误")
        elif choice == 5:
            print("\n【数据统计】")
            print(f"药材总数量: {len(herbs)} 味")
            print(f"\n各类药材计数:")
            for cat in categories:
                count = sum(1 for h in herbs if h["category"] == cat)
                print(f"  {cat}: {count}味")
        elif choice == 6:
            display_food_herbs(food_herbs)
        elif choice == 7:
            print("\n【体质辨识与药膳智能推荐】")
            print("请输入您的体质类型：")
            print("  1. 气虚质  2. 阳虚质  3. 阴虚质  4. 痰湿质")
            print("  5. 湿热质  6. 血瘀质  7. 气郁质  8. 特禀质")
            const_map = {1: "气虚质", 2: "阳虚质", 3: "阴虚质", 4: "痰湿质", 5: "湿热质", 6: "血瘀质", 7: "气郁质", 8: "特禀质"}
            try:
                const_choice = safe_input_int("请输入体质序号(1-8): ", 1, 8)
                if const_choice in const_map:
                    constitution = const_map[const_choice]
                    user_needs = safe_input("请输入您的养生需求(可选，直接回车跳过): ").strip()
                    print(f"\n正在为您生成「{constitution}」的养生方案...")
                    result = health_query(constitution, user_needs)
                    if result.get("mode") == "llm" and result.get("success"):
                        print(f"\n{'=' * 60}")
                        print(f"【AI智能推荐】来源: {result.get('source', 'deepseek-chat')}")
                        print(f"{'=' * 60}")
                        print(result["answer"])
                    elif result.get("mode") == "local" and result.get("success"):
                        print(f"\n{'=' * 60}")
                        print(f"【本地检索推荐】(配置API Key后启用AI模式)")
                        print(f"{'=' * 60}")
                        print(result.get("answer", ""))
                        recommendations = result.get("recommendations", [])
                        if recommendations:
                            print(f"\n推荐药材（按匹配度排序）:")
                            for i, r in enumerate(recommendations, 1):
                                print(f"  {i}. {r['name']} ({r['category']}) - {r['effect']}")
                                print(f"     成分: {', '.join(r.get('components', []))}")
                                print(f"     禁忌: {r.get('contraindication', '')}")
                    else:
                        print(f"\n推荐失败: {result.get('error', '未知错误')}")
                        print("已切换到本地模式:")
                        recommend_dietary_therapy(constitution)
                    if result.get("tip"):
                        print(f"\n💡 提示: {result['tip']}")
                else:
                    print("\n序号无效")
            except ValueError:
                print("\n输入错误，请输入数字1-8")
        elif choice == 8:
            print("\n【药膳智能问诊流水线】")
            print("=" * 60)
            print("系统将通过多轮对话收集您的身体症状，")
            print("依次由三个AI智能体完成：")
            print("  Agent1 → 体质辨证（输出推理依据+免责声明）")
            print("  Agent2 → 药材匹配（性味归经+代茶饮方案）")
            print("  Agent3 → 食疗药膳（详细做法）")
            print("=" * 60)
            try:
                dialog_history = []
                round_num = 1
                print(f"\n--- 第{round_num}轮问诊 ---")
                symptom = safe_input("请描述您的主要身体症状和不适感受: ").strip()
                if not symptom:
                    print("\n未输入症状信息，返回主菜单")
                    continue
                dialog_history.append(f"第{round_num}轮: {symptom}")
                taboo = safe_input("请输入您的忌口/过敏信息（可选，直接回车跳过）: ").strip()
                print("\n请问您是否属于孕妇、哺乳期、儿童，或是存在严重基础病这类特殊人群？")
                print("如果属于，请直接说明你的情况（例如：我是孕妇 / 哺乳期）；若无，则直接回复：无")
                while True:
                    special_population = safe_input("请输入：").strip()
                    if special_population:
                        break
                    print("输入不能为空，若无特殊人群情况请直接回复：无")
                user_dialog_text = "\n".join(dialog_history)
                while True:
                    result = food_pipeline_handler(user_dialog_text, taboo, special_population)
                    if result.get("type") == "ask":
                        question = result.get("question", "")
                        print(f"\n🤖 系统追问: {question}")
                        answer = safe_input("请回答: ").strip()
                        if not answer:
                            answer = "无补充"
                        round_num += 1
                        dialog_history.append(f"第{round_num}轮: {answer}")
                        user_dialog_text = "\n".join(dialog_history)
                        continue
                    elif result.get("type") == "result":
                        print("\n=====【Agent3 食疗药膳方案】=====")
                        print(result.get("food_scheme_markdown", ""))
                        print("=====================================\n")
                        export_choice = safe_input("请问您是否需要将本次问诊结果导出为本地txt文件保存？【是/否】: ").strip()
                        if export_choice in ("是", "y", "Y", "yes", "YES"):
                            saved_path = export_consultation_txt(user_dialog_text, result)
                            print(f"✅ 问诊记录已保存至：{saved_path}")
                        else:
                            print("好的，本次问诊不导出文件。")
                        print("\n✅ 问诊流水线已完成，即将返回主菜单")
                        break
                    else:
                        print(f"\n⚠️ 流水线异常: {result}")
                        break
            except Exception as e:
                print(f"\n⚠️ 药膳问诊流水线运行失败: {e}")
                print("请检查 DEEPSEEK_API_KEY 配置是否正确")
        else:
            print("\n输入错误，请输入数字0-8")
        if choice != 0:
            safe_input("\n按回车继续...")


if __name__ == "__main__":
    main()
