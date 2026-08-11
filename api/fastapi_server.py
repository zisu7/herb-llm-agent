from src.food_pipeline import food_pipeline_handler
 from pydantic import BaseModel
 from fastapi import APIRouter
 router = APIRouter()
 class FoodChatRequest(BaseModel):
     dialog_context: str   # 累计全部对话文本
     taboo: str            # 用户忌口
 @router.post("/api/food-chat")
 def food_chat(req: FoodChatRequest):
     output = food_pipeline_handler(req.dialog_context, req.taboo)
     return output