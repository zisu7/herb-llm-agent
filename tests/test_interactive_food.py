import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.food_pipeline import food_pipeline_handler

def interactive_chat_test():
    print("====药膳体质问诊系统启动====")
    # ========== 会话缓存变量（步骤四核心） ==========
    # 初始化空文本，用来累计保存用户所有描述
    dialog_context = ""
    # 用户固定忌口，可自定义修改
    user_taboo = "无冰饮、寒性瓜果"
    while True:
        # 接收用户最新输入
        user_input = input("\n请描述你的身体感受（输入exit退出）：")
        # 退出指令
        if user_input.lower() == "exit":
            print("程序结束")
            break

        # 【关键：把本轮输入追加到缓存，保存全部对话】
        dialog_context += f"\n用户身体描述：{user_input}"
        # 把完整的全部对话缓存传入流水线
        result = food_pipeline_handler(dialog_context, user_taboo)
        # 分支判断：需要继续提问 / 直接输出药膳方案
        if result["type"] == "ask":
            print(f"\n【智能助手追问补充信息】{result['question']}")
        else:
            print("\n==========体质辨证完成，完整药膳食疗方案==========")
            print(result["food_scheme_markdown"])
            # 拿到完整结果后，结束本轮对话
            break

if __name__ == "__main__":
    interactive_chat_test()
