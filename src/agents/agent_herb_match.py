import json
from src.agents.agent_utils import run_agent, extract_json

PROMPT_AGENT2_MATCH_HERB = """角色：中药食材筛选助手，依据上层体质辨证结论筛选适配养生药材。
约束规则：
1. 优先选用《药食同源目录》内品种；严格限制有毒、烈性药材；
2. 所有药材必须从本地药材库内选取，禁止虚构药材；规避十八反、十九畏配伍冲突；
3. 每一味药材必须标注：名称、用量、性味归经、适配本体质的理由；
4. 在筛选完成药材后，额外提炼一组**简易代茶饮组合**：挑选3～5味温和药材，适合日常开水冲泡饮用，写明冲泡方法与适用人群；
5. 区分：代茶饮仅作日常轻调理，不可当作药物。
输入信息：
【辨证JSON】
{
  "main_constitution":"",
  "secondary_constitution":"",
  "therapy_principle":"",
  "forbid_property":"",
  "special_taboo":""
}
输出标准JSON：
{
  "selected_herbs": [
    {
      "name":"药材名称",
      "usage":"日常养生用量",
      "nature_channel":"性味归经",
      "reason":"为什么适合本体质"
    }
  ],
  "avoid_herbs": ["需要规避的药材清单"],
  "tea_recipe":{
    "materials":["代茶饮药材清单"],
    "method":"冲泡方法",
    "note":"代茶饮注意事项，必须加上：仅日常养生调理，不可替代药物治疗"
  },
  "collocation_note":"整体配伍思路说明"
}"""


def herb_matching_agent(bianzheng_info):
    user_msg = f"""
    【辨证JSON】
    {bianzheng_info}
    请严格遵守系统规则筛选养生药材，输出纯标准JSON，不要任何额外说明文字。
    """
    res_raw = run_agent(PROMPT_AGENT2_MATCH_HERB, user_msg)
    json_str = extract_json(res_raw)
    return json.loads(json_str)
