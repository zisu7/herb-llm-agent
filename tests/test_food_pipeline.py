import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.food_pipeline import generate_food_plan

def test_food_agent_pipeline():
    # 重点：不再手动写体质！只写症状
    constitution = "未知"
    symptom = "长期身体困重乏力，吃完饭后肚子发胀，大便黏腻粘马桶，受凉容易拉肚子"
    taboo = "冰镇饮料、西瓜、苦瓜等寒性食物"
    print("=======启动药膳多智能体链式流水线=======")
    result = generate_food_plan(constitution, symptom, taboo)
    print("\n【1.Agent1 自主辨证结果】")
    print(result["constitution_info"])
    print("\n【2.Agent2 筛选配伍药材】")
    print(result["selected_herbs"])
    print("\n【3.Agent3 药膳方案（含烹饪做法）】")
    print(result["food_scheme_markdown"])

if __name__ == "__main__":
    test_food_agent_pipeline()
