import os
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException,File, UploadFile
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
import shutil
import pandas as pd

from langgraph.checkpoint.postgres import PostgresSaver  # 生产推荐持久化检查点
from langgraph.types import Command

# 导入你之前的 Agent 创建逻辑与工具
from agents.M_Agent.main_agent import agent

app = FastAPI(title="DeepAgent API Service", version="1.0.0")


# ==================== 请求与响应模型 ==================== #

class ChatRequest(BaseModel):
    thread_id: str  # 区分不同会话/用户的ID
    message: str  # 用户输入的文本


class ApproveRequest(BaseModel):
    thread_id: str  # 会话ID
    action_name: str  # 调用的工具名（如 'add'）
    type: str  # 'approve' 或 'reject'


class ChatResponse(BaseModel):
    status: str  # 'completed' 或 'interrupted'
    content: Optional[str] = None  # 智能体最终回复
    interrupt_info: Optional[Dict[str, Any]] = None  # 拦截信息（若被拦截）


# ==================== API 路由接口 ==================== #

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    1. 发起对话/发起任务接口
    """
    config = {"configurable": {"thread_id": req.thread_id}}

    try:
        # 调用 Agent
        res = agent.invoke(
            {"messages": [{"role": "user", "content": req.message}]},
            config=config
        )

        # 检查是否有敏感操作触发了中断拦截
        if "__interrupt__" in res and res["__interrupt__"]:
            interrupt_data = res["__interrupt__"][0].value
            action_req = interrupt_data["action_requests"][0]

            return ChatResponse(
                status="interrupted",
                interrupt_info={
                    "action_name": action_req["name"],
                    "args": action_req["args"],
                    "description": action_req.get("description", "")
                }
            )

        # 正常完成，返回最后一条消息
        final_message = res["messages"][-1].content
        return ChatResponse(status="completed", content=final_message)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/approve", response_model=ChatResponse)
async def approve_endpoint(req: ApproveRequest):
    """
    2. 人工审核/批准恢复接口
    """
    config = {"configurable": {"thread_id": req.thread_id}}

    # 构造 LangGraph 的 Resume 决策指令
    decision = Command(
        resume={
            "decisions": [
                {"action_name": req.action_name, "type": req.type}
            ]
        }
    )

    try:
        # 带着决策命令恢复 Agent 执行
        final_res = agent.invoke(decision, config=config)

        final_message = final_res["messages"][-1].content
        return ChatResponse(status="completed", content=final_message)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 健康检查
@app.get("/health")
def health_check():
    return {"status": "ok", "time": datetime.now().isoformat()}
# =============================================================================
#Excel表格上传

UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.post("/api/v1/upload_excel")
async def upload_excel(file: UploadFile = File(...)):
    # 1. 校验扩展名
    if not file.filename.endswith((".xlsx", ".xls")):
        return {"error": "仅支持上传 Excel 文件 (.xlsx, .xls)"}

    # 2. 保存上传的文件
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. 读取并解析文件
    try:
        # 根据文件类型指定解析引擎
        engine = "openpyxl" if file.filename.endswith(".xlsx") else "xlrd"
        df = pd.read_excel(file_path, engine=engine)

        # 替换 NaN 空值，避免 JSON 转换报错
        df = df.fillna("")

        return {
            "status": "success",
            "filename": file.filename,
            "total_rows": len(df),
            "data": df.to_dict(orient="records"),  # 返回解析后的列表数据
        }
    except Exception as e:
        return {"error": f"解析失败: {str(e)}"}