from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
import shutil
import pandas as pd

from langgraph.checkpoint.postgres import PostgresSaver  # 生产推荐持久化检查点
from langgraph.types import Command

# 导入你之前的 Agent 创建逻辑与工具
from agents.M_Agent.main_agent import agent, sync_local_file_to_sandbox

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
        res =await agent.ainvoke(
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
        final_res =await agent.ainvoke(decision, config=config)

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


def _save_and_parse_excel(file: UploadFile):
    """内部通用函数：负责保存 Excel 文件并解析出 DataFrame"""
    if not file.filename.endswith((".xlsx", ".xls")):
        raise ValueError("仅支持上传 Excel 文件 (.xlsx, .xls)")

    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    engine = "openpyxl" if file.filename.endswith(".xlsx") else "xlrd"
    df = pd.read_excel(file_path, engine=engine).fillna("")

    return file_path, df


# ==================== 接口函数（极简版） ==================== #

@app.post("/api/v1/upload_excel")
async def upload_excel(file: UploadFile = File(...)):
    """仅上传并返回解析结果"""
    try:
        file_path, df = _save_and_parse_excel(file)
        return {
            "status": "success",
            "filename": file.filename,
            "total_rows": len(df),
            "data": df.to_dict(orient="records"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/upload_and_chat")
async def upload_and_chat(
        thread_id: str = Form(...),
        message: str = Form("请分析我上传的这份表格"),
        file: UploadFile = File(...)
):
    """上传并触发 Agent 对话"""
    try:
        # 保存 Excel 到 API 服务器本地
        file_path, _ = _save_and_parse_excel(file)

        # 方案 A：立即同步到 E2B 沙箱，避免 Agent 在沙箱内找不到文件
        sandbox_file_path = sync_local_file_to_sandbox(file_path)

        full_message = (
            f"{message}。"
            f"数据文件已同步至 E2B 沙箱，请直接使用路径 `{sandbox_file_path}` 进行分析，"
            f"无需再次上传或搜索其他目录。"
        )
        config = {"configurable": {"thread_id": thread_id}}

        res = await agent.ainvoke(
            {"messages": [{"role": "user", "content": full_message}]},
            config=config
        )

        # 与 chat 接口一致，处理 Agent 执行过程中的中断
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

        return ChatResponse(status="completed", content=res["messages"][-1].content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
