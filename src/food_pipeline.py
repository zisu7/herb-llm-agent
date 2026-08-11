import re
import json
from src.agents.agent_constitution import constitution_analysis
from src.agents.agent_herb_match import herb_matching_agent
from src.agents.agent_food_recipe import food_recipe_agent


def extract_json(raw_text: str) -> str:
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, raw_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return raw_text.strip()


def food_pipeline_handler(user_dialog_text: str, user_taboo: str):
     agent1_output = constitution_analysis(user_dialog_text)
     if "【NEED_ASK】" in agent1_output:
         question = agent1_output.replace("【NEED_ASK】", "").strip()
         return {
             "type": "ask",
             "question": question
         }
     json_str = extract_json(agent1_output)
     res_bianzheng = json.loads(json_str)
     # Agent1 体质推理打印
     print("\n=====【Agent1 体质辨析推理过程】=====")
     print(f"核心体质：{res_bianzheng['main_constitution']}")
     print(f"兼夹体质：{res_bianzheng['secondary_constitution']}")
     print(f"推理依据：{res_bianzheng['reason_analysis']}")
     print(f"养生禁忌&风险提示：{res_bianzheng['special_taboo']}")
     print("=====================================\n")
     print("【日志：开始调用Agent2药材筛选】")
     res_herb = herb_matching_agent(res_bianzheng)
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