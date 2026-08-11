import json
import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_HERB_DATA_PATH = _PROJECT_ROOT / "src" / "data" / "herb_raw.json"
_PROMPT_PATH = _PROJECT_ROOT / "docs" / "prompt_templates.md"


def _load_herbs():
    if not _HERB_DATA_PATH.exists():
        return []
    with open(_HERB_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_system_prompt():
    if not _PROMPT_PATH.exists():
        return "你是一位专业的中医药膳养生顾问。"
    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    section_start = content.find("## 药膳养生Agent")
    if section_start == -1:
        return "你是一位专业的中医药膳养生顾问。"
    code_start = content.find("```", section_start)
    if code_start == -1:
        return "你是一位专业的中医药膳养生顾问。"
    text_start = code_start + 3
    code_end = content.find("```", text_start)
    if code_end == -1:
        return "你是一位专业的中医药膳养生顾问。"
    return content[text_start:code_end].strip()


def _local_health_search(constitution, needs, herbs):
    food_herbs = [h for h in herbs if h.get("is_food_medicine", False)]
    keywords = set()
    if constitution:
        keywords.add(constitution)
        const_map = {
            "气虚": ["补气", "益气", "健脾"],
            "阳虚": ["温阳", "散寒", "温中"],
            "阴虚": ["养阴", "滋阴", "润肺"],
            "痰湿": ["祛湿", "利湿", "化痰"],
            "湿热": ["清热", "解毒", "利湿"],
            "血瘀": ["活血", "化瘀", "通络"],
            "气郁": ["疏肝", "理气", "解郁"],
            "特禀": ["固表", "益气", "养血"],
        }
        for k, v in const_map.items():
            if k in constitution:
                keywords.update(v)
    if needs:
        for word in needs.replace("，", " ").replace(",", " ").split():
            if word.strip():
                keywords.add(word.strip())

    results = []
    for herb in food_herbs:
        text = (
            f"{herb.get('name', '')} {herb.get('effect', '')} "
            f"{' '.join(herb.get('components', []))} "
            f"{herb.get('category', '')} {herb.get('meridian', '')}"
        ).lower()
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > 0:
            herb_copy = dict(herb)
            herb_copy["_match_score"] = score
            results.append(herb_copy)

    results.sort(key=lambda x: x["_match_score"], reverse=True)
    for r in results:
        del r["_match_score"]

    return results[:10]


def health_query(constitution, user_needs=""):
    herbs = _load_herbs()
    if not herbs:
        return {
            "mode": "local",
            "success": False,
            "error": "药材数据库为空，请检查 herb_raw.json 文件",
            "recommendations": [],
        }

    system_prompt = _load_system_prompt()

    try:
        from .llm_client import is_llm_available, chat_completion
        if is_llm_available():
            try:
                food_herbs = [h for h in herbs if h.get("is_food_medicine", False)]
                herb_context = []
                for h in food_herbs:
                    herb_context.append(
                        f"药材: {h['name']} | 类别: {h['category']} | 归经: {h['meridian']} | "
                        f"功效: {h['effect']} | 成分: {', '.join(h.get('components', []))} | "
                        f"禁忌: {h.get('contraindication', '')} | 用量: {h.get('dosage', '')}"
                    )
                context_text = "\n".join(herb_context)
                enriched_user = (
                    f"体质类型: {constitution}\n"
                    f"养生需求: {user_needs if user_needs else '综合养生调理'}\n\n"
                    f"药食同源药材库（共{len(food_herbs)}味）:\n{context_text}\n\n"
                    f"请提供个性化的药膳方案、药茶推荐和配伍禁忌提醒。"
                )
                response = chat_completion(system_prompt, enriched_user)
                return {
                    "mode": "llm",
                    "success": True,
                    "answer": response,
                    "source": "deepseek-chat",
                }
            except Exception as e:
                local_results = _local_health_search(constitution, user_needs, herbs)
                return {
                    "mode": "llm",
                    "success": False,
                    "error": f"LLM调用失败: {str(e)}，已切换到本地检索模式",
                    "recommendations": local_results,
                }
    except ImportError:
        pass

    local_results = _local_health_search(constitution, user_needs, herbs)
    food_count = sum(1 for h in herbs if h.get("is_food_medicine", False))
    return {
        "mode": "local",
        "success": True,
        "answer": f"【本地检索模式】根据体质「{constitution}」和需求「{user_needs or '综合养生'}」，从 {food_count} 味药食同源药材中为您推荐：",
        "recommendations": local_results,
        "tip": "配置 DEEPSEEK_API_KEY 后可启用 AI 智能药膳推荐模式",
    }