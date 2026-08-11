import sys
import os
from pathlib import Path

_project_root = Path(__file__).resolve().parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.llm.agent_research import research_query
from src.llm.agent_health import health_query

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
    herbs = [
        {"name":"人参","category":"补虚药","meridian":"脾肺心经","effect":"大补元气，复脉固脱","component":"人参皂苷、多糖","dosage":"3-9g"},
        {"name":"黄芪","category":"补虚药","meridian":"脾肺经","effect":"补气升阳，固表止汗","component":"黄芪多糖、皂苷","dosage":"9-30g"},
        {"name":"当归","category":"补虚药","meridian":"肝心脾经","effect":"补血活血，调经止痛","component":"阿魏酸、当归多糖","dosage":"6-12g"},
        {"name":"白术","category":"补虚药","meridian":"脾胃经","effect":"健脾益气，燥湿利水","component":"挥发油、白术多糖","dosage":"6-12g"},
        {"name":"甘草","category":"补虚药","meridian":"心肺脾胃经","effect":"益气补中，清热解毒","component":"甘草酸、甘草苷","dosage":"2-10g"},
        {"name":"党参","category":"补虚药","meridian":"脾肺经","effect":"补中益气，健脾益肺","component":"党参多糖、皂苷","dosage":"9-30g"},
        {"name":"西洋参","category":"补虚药","meridian":"心肺肾经","effect":"补气养阴，清热生津","component":"西洋参皂苷","dosage":"3-6g"},
        {"name":"麦冬","category":"补虚药","meridian":"心肺胃经","effect":"养阴生津，润肺清心","component":"麦冬多糖、皂苷","dosage":"6-12g"},
        {"name":"枸杞子","category":"补虚药","meridian":"肝肾经","effect":"滋补肝肾，益精明目","component":"枸杞多糖、胡萝卜素","dosage":"6-12g"},
        {"name":"熟地黄","category":"补虚药","meridian":"肝肾经","effect":"补血养阴，填精益髓","component":"地黄多糖、梓醇","dosage":"9-15g"},
        {"name":"肉桂","category":"温里药","meridian":"肾脾心肝经","effect":"补火助阳，散寒止痛","component":"桂皮醛、挥发油","dosage":"1-5g"},
        {"name":"干姜","category":"温里药","meridian":"脾胃肾心肺经","effect":"温中散寒，回阳通脉","component":"姜辣素、挥发油","dosage":"3-10g"},
        {"name":"高良姜","category":"温里药","meridian":"脾胃经","effect":"温中止痛，温中止呕","component":"高良姜素、挥发油","dosage":"3-6g"},
        {"name":"吴茱萸","category":"温里药","meridian":"肝脾胃肾经","effect":"散寒止痛，降逆止呕","component":"吴茱萸碱、挥发油","dosage":"2-5g"},
        {"name":"丁香","category":"温里药","meridian":"脾胃肺肾经","effect":"温中降逆，散寒止痛","component":"丁香油酚、挥发油","dosage":"1-3g"},
        {"name":"陈皮","category":"理气药","meridian":"脾肺经","effect":"理气健脾，燥湿化痰","component":"挥发油、橙皮苷","dosage":"3-10g"},
        {"name":"枳实","category":"理气药","meridian":"脾胃大肠经","effect":"破气消积，化痰散痞","component":"挥发油、黄酮","dosage":"3-10g"},
        {"name":"木香","category":"理气药","meridian":"脾胃大肠胆三焦经","effect":"行气止痛，健脾消食","component":"挥发油、木香碱","dosage":"3-10g"},
        {"name":"香附","category":"理气药","meridian":"肝脾三焦经","effect":"疏肝解郁，理气宽中","component":"挥发油、香附烯","dosage":"6-10g"},
        {"name":"砂仁","category":"理气药","meridian":"脾胃肾经","effect":"化湿开胃，温脾止泻","component":"挥发油、砂仁苷","dosage":"3-6g"},
        {"name":"黄连","category":"清热药","meridian":"心肝胃大肠经","effect":"清热燥湿，泻火解毒","component":"黄连素、黄连碱","dosage":"2-5g"},
        {"name":"黄芩","category":"清热药","meridian":"肺胆脾大肠小肠经","effect":"清热燥湿，泻火解毒","component":"黄芩苷、黄芩素","dosage":"3-10g"},
        {"name":"金银花","category":"清热药","meridian":"肺心胃经","effect":"清热解毒，疏散风热","component":"绿原酸、黄酮","dosage":"6-15g"},
        {"name":"连翘","category":"清热药","meridian":"肺心小肠经","effect":"清热解毒，消肿散结","component":"连翘苷、挥发油","dosage":"6-15g"},
        {"name":"板蓝根","category":"清热药","meridian":"心胃经","effect":"清热解毒，凉血利咽","component":"靛蓝、靛玉红","dosage":"9-15g"},
        {"name":"蒲公英","category":"清热药","meridian":"肝胃经","effect":"清热解毒，消肿散结","component":"蒲公英甾醇、黄酮","dosage":"10-15g"},
        {"name":"牡丹皮","category":"清热药","meridian":"心肝肾经","effect":"清热凉血，活血化瘀","component":"丹皮酚、牡丹苷","dosage":"6-12g"},
        {"name":"玄参","category":"清热药","meridian":"肺胃肾经","effect":"清热凉血，滋阴降火","component":"玄参素、多糖","dosage":"9-15g"},
        {"name":"赤芍","category":"清热药","meridian":"肝经","effect":"清热凉血，散瘀止痛","component":"芍药苷、赤芍素","dosage":"6-12g"},
        {"name":"石膏","category":"清热药","meridian":"肺胃经","effect":"清热泻火，除烦止渴","component":"含水硫酸钙","dosage":"15-60g"}
    ]
    food_herbs = [
        {"name":"枸杞","category":"补虚药","effect":"滋补肝肾，益精明目","usage":"煲汤、泡茶、煮粥","dosage":"6-12g"},
        {"name":"山药","category":"补虚药","effect":"益气养阴，补脾肺肾","usage":"煲汤、煮粥、清蒸","dosage":"15-30g"},
        {"name":"薏米","category":"利水渗湿药","effect":"利水渗湿，健脾止泻","usage":"煮粥、煲汤","dosage":"9-30g"},
        {"name":"红枣","category":"补虚药","effect":"补中益气，养血安神","usage":"煲汤、泡茶、煮粥","dosage":"6-15g"},
        {"name":"桂圆","category":"补虚药","effect":"补益心脾，养血安神","usage":"煲汤、泡茶","dosage":"9-15g"},
        {"name":"莲子","category":"收涩药","effect":"补脾止泻，益肾涩精","usage":"煮粥、煲汤","dosage":"6-15g"},
        {"name":"百合","category":"补虚药","effect":"养阴润肺，清心安神","usage":"煮粥、煲汤","dosage":"6-12g"},
        {"name":"生姜","category":"温里药","effect":"温中散寒，解表发汗","usage":"调味、泡茶","dosage":"3-10g"},
        {"name":"大蒜","category":"温里药","effect":"解毒杀虫，温中消食","usage":"调味","dosage":"3-5瓣"},
        {"name":"花椒","category":"温里药","effect":"温中止痛，杀虫止痒","usage":"调味","dosage":"3-6g"},
        {"name":"陈皮","category":"理气药","effect":"理气健脾，燥湿化痰","usage":"煲汤、泡茶","dosage":"3-10g"},
        {"name":"山楂","category":"消食药","effect":"消食化积，活血化瘀","usage":"泡茶、煮粥","dosage":"10-15g"},
        {"name":"荷叶","category":"清热药","effect":"清热解暑，升发清阳","usage":"泡茶","dosage":"3-6g"},
        {"name":"金银花","category":"清热药","effect":"清热解毒，疏散风热","usage":"泡茶","dosage":"6-15g"},
        {"name":"菊花","category":"解表药","effect":"疏散风热，清肝明目","usage":"泡茶","dosage":"5-10g"},
        {"name":"蜂蜜","category":"补虚药","effect":"补中润燥，止痛解毒","usage":"冲服、调味","dosage":"10-20g"},
        {"name":"阿胶","category":"补虚药","effect":"补血滋阴，润燥止血","usage":"烊化冲服","dosage":"3-9g"},
        {"name":"茯苓","category":"利水渗湿药","effect":"利水渗湿，健脾宁心","usage":"煲汤、煮粥","dosage":"10-15g"},
        {"name":"芡实","category":"收涩药","effect":"益肾固精，补脾止泻","usage":"煮粥、煲汤","dosage":"9-15g"},
        {"name":"葛根","category":"解表药","effect":"解肌退热，生津止渴","usage":"煲汤、泡茶","dosage":"10-15g"}
    ]
    categories = sorted(set(h["category"] for h in herbs))
    meridian_list = ["心","肝","脾","肺","肾","胃","大肠","小肠","胆","膀胱","三焦","心包"]
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
        print("7.输入体质生成药膳、药茶推荐方案，附带配伍禁忌提醒")
        print("0.退出系统")
        try:
            choice = int(input("请输入选择(0-7): "))
        except ValueError:
            print("\n输入错误，请输入数字0-7")
            input("按回车继续...")
            continue
        if choice == 0:
            print("\n感谢使用，再见！")
            break
        elif choice == 1:
            display_herbs(herbs)
        elif choice == 2:
            keyword = input("\n请输入药材名称或研发问题: ")
            print(f"\n正在分析「{keyword}」...")
            research_result = research_query(keyword)
            if research_result.get("mode") == "llm" and research_result.get("success"):
                print(f"\n{'='*60}")
                print(f"【AI研发分析】来源: {research_result.get('source', 'deepseek-chat')}")
                print(f"{'='*60}")
                print(research_result["answer"])
            elif research_result.get("mode") == "local" and research_result.get("success"):
                print(f"\n{'='*60}")
                print(f"【本地检索】(配置API Key后启用AI研发分析)")
                print(f"{'='*60}")
                print(research_result.get("answer", ""))
                results = research_result.get("results", [])
                if results:
                    print(f"\n匹配药材详情:")
                    for i, r in enumerate(results, 1):
                        print(f"  {i}. {r['name']} ({r['category']}) - {r['effect']}")
                        print(f"     成分: {', '.join(r.get('components', []))}")
                        print(f"     禁忌: {r.get('contraindication', '')}")
                else:
                    print(f"\n未找到匹配的药材")
            else:
                print(f"\n检索失败: {research_result.get('error', '未知错误')}")
            if research_result.get("tip"):
                print(f"\n💡 提示: {research_result['tip']}")
        elif choice == 3:
            print("\n中药类别列表:")
            for i, cat in enumerate(categories, 1):
                print(f"  {i}. {cat}")
            try:
                cat_idx = int(input("请输入类别序号: ")) - 1
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
                mer_idx = int(input("请输入归经序号: ")) - 1
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
            const_map = {1:"气虚质", 2:"阳虚质", 3:"阴虚质", 4:"痰湿质", 5:"湿热质", 6:"血瘀质", 7:"气郁质", 8:"特禀质"}
            try:
                const_choice = int(input("请输入体质序号(1-8): "))
                if const_choice in const_map:
                    constitution = const_map[const_choice]
                    user_needs = input("请输入您的养生需求(可选，直接回车跳过): ").strip()
                    print(f"\n正在为您生成「{constitution}」的养生方案...")
                    result = health_query(constitution, user_needs)
                    if result.get("mode") == "llm" and result.get("success"):
                        print(f"\n{'='*60}")
                        print(f"【AI智能推荐】来源: {result.get('source', 'deepseek-chat')}")
                        print(f"{'='*60}")
                        print(result["answer"])
                    elif result.get("mode") == "local" and result.get("success"):
                        print(f"\n{'='*60}")
                        print(f"【本地检索推荐】(配置API Key后启用AI模式)")
                        print(f"{'='*60}")
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
        else:
            print("\n输入错误，请输入数字0-7")
        if choice != 0:
            input("\n按回车继续...")

if __name__ == "__main__":
    main()