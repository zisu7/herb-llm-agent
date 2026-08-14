import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.food_pipeline import food_pipeline_handler, export_consultation_txt

def interactive_chat_test():
    print("====药膳体质问诊系统启动====")
    # ========== 会话缓存变量（步骤四核心） ==========
    # 初始化空文本，用来累计保存用户所有描述
    dialog_context = ""
    # 用户固定忌口，可自定义修改
    user_taboo = "无冰饮、寒性瓜果"
    # 特殊人群信息由用户在终端直接输入，禁止程序默认填“无”
    print("\n请问您是否属于孕妇、哺乳期、儿童，或是存在严重基础病这类特殊人群？")
    print("如果属于，请直接说明你的情况（例如：我是孕妇 / 哺乳期）；若无，则直接回复：无")
    while True:
        try:
            special_population = input("请输入：").strip()
        except EOFError:
            special_population = "无"
            break
        if special_population:
            break
        print("输入不能为空，若无特殊人群情况请直接回复：无")
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
        result = food_pipeline_handler(dialog_context, user_taboo, special_population)
        # 分支判断：需要继续提问 / 直接输出药膳方案
        if result["type"] == "ask":
            print(f"\n【智能助手追问补充信息】{result['question']}")
        else:
            print("\n==========体质辨证完成，完整药膳食疗方案==========")
            print(result["food_scheme_markdown"])
            # 问诊流程末尾：询问是否导出本次问诊结果为本地txt
            try:
                export_choice = input("\n请问您是否需要将本次问诊结果导出为本地txt文件保存？【是/否】: ").strip()
            except EOFError:
                export_choice = "否"
            if export_choice in ("是", "y", "Y", "yes", "YES"):
                saved_path = export_consultation_txt(dialog_context, result)
                print(f"✅ 问诊记录已保存至：{saved_path}")
            else:
                print("好的，本次问诊不导出文件。")
            # 拿到完整结果后，结束本轮对话
            break

if __name__ == "__main__":
    interactive_chat_test()
