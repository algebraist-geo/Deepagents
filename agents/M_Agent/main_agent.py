# 修改后的 test_1.py
import os
import asyncio
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np  # main 运行需要
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StoreBackend
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.tools import tool
# from pathlib import Path # 重复导入
from langchain_e2b import E2BSandbox
from e2b import Sandbox
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command
from llms import llm  # 确保你的项目里有 llms.py 并导出了 llm 实例
from skills.data_analysis.data_analysis import (
    e2b_upload_dataset,
    e2b_execute_python,
    e2b_download_artifact,
    close_sandbox,
    e2b_list_workspace
)

# ----------------------------------------------------------------------------------
# 【修正核心】将 Agent 的所有依赖初始化逻辑移到全局根目录下，使其可以被外部 import
# ----------------------------------------------------------------------------------

# 1. 基础配置
SKILL_ROOT = Path('./skills')
test_csv_path = Path('sales_data.csv')
today_time = datetime.now().strftime("%Y年%m月%d日")

# 根据文件层级定位到根目录 (在全局定义时 Path(__file__) 是准确的)
base_dir = Path(__file__).resolve().parent.parent.parent
save_dir = base_dir / "agents" / "work_result"
save_dir.mkdir(parents=True, exist_ok=True)

hum_middleware = HumanInTheLoopMiddleware(interrupt_on={'e2b_upload_dataset': True})


# 2. 定义一个通用的 Prompt 加载工具函数
def load_prompt(file_name: str, **kwargs) -> str:
    """从 prompts 文件夹读取 markdown prompt 并填充参数"""
    print(f'正在读取 {file_name} 的提示词')
    # 使用 Path(__file__).parent 确保路径相对于 test_1.py
    prompt_path = Path(__file__).parent / "prompts" / file_name
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt 文件不存在: {prompt_path}")

    template = prompt_path.read_text(encoding="utf-8")
    print(f'{file_name} 的提示词读取成功')
    return template.format(**kwargs)


# 3. 初始化原子工具、E2B 沙盒、后端、存储、检查点
print('初始化工具与环境...')

# 注意：请确保这些环境变量在运行 server.py 时也已正确设置
search = TavilySearch(api_key=os.environ.get('Tavily_api_key'), max_results=3)
e2b_sandbox = Sandbox.create(api_key=os.environ.get('SandBoxE2B'))
e2b_backend = E2BSandbox(sandbox=e2b_sandbox)

checkpointer = MemorySaver()
store = InMemoryStore()
backend = CompositeBackend(
    default=StoreBackend(namespace=lambda rt: ('workspace', 'hanxd')),
    routes={
        '/memories/': StoreBackend(namespace=lambda rt: ('memories', 'hanxd')),
        '/skills/': StoreBackend(namespace=lambda _rt: ('skills',))
    }
)

# 4. 加载提示词
analyst_prompt = load_prompt("data_analyst_subagent.md", today_time=today_time, save_dir=save_dir)
search_prompt = load_prompt("data_search.md", today_time=today_time)
main_prompt = load_prompt("root_agent.md", today_time=today_time, save_dir=save_dir)

# 5. 定义子代理配置
data_analyst_subagent = {
    "name": "data_analyst",
    "description": "专职负责沙箱数据分析、图表生成、Markdown报告编写以及文件打包下载的专家。",
    'middleware': [hum_middleware],
    "system_prompt": analyst_prompt,
    "tools": [e2b_upload_dataset, e2b_execute_python, e2b_download_artifact,e2b_list_workspace]
}
data_search = {
    'name': '王怀婷',
    'description': '专门负责数据搜集和整理',
    'tools': [search],
    'skills': [],
    'system_prompt': search_prompt,
}

# -------------------------------------------------------------
# 【修正关键】将 agent 定义为全局变量
# -------------------------------------------------------------
print("创建 Agent 实例...")
agent = create_deep_agent(
    model=llm,
    skills=["/skills/"],
    backend=backend,
    tools=[],
    system_prompt=main_prompt,
    checkpointer=checkpointer,
    store=store,
    subagents=[data_analyst_subagent, data_search],
    middleware=[]
)
# ==================== 核心修改：将技能注册提取到全局 ====================
def init_agent_skills()->None:
    """初始化并注册 Agent 的技能，供 FastAPI 或本地测试调用"""
    print("正在注册技能到 Agent 存储后端...")
    for skill_md in SKILL_ROOT.glob("**/SKILL.md"):
        relative_path = skill_md.relative_to(SKILL_ROOT)
        virtual_path = f"/skills/{relative_path.as_posix()}"

        with open(skill_md, "r", encoding="utf-8") as f:
            backend.write(virtual_path, f.read())
            print(f"成功加载并映射技能说明文件: {virtual_path}")

# 直接在模块加载时执行一次技能注册
init_agent_skills()
# ========================================================================


# ----------------------------------------------------------------------------------
# main() 函数现在只保留用于本地测试、数据生成和调用逻辑
# ----------------------------------------------------------------------------------
async def main():

    print('=' * 50)
    # 命令行测试输入
    # absolute_csv_path=input('输入框：')
    # 简化测试直接 hardcode，或在调用时由 Fast API 传入
    absolute_csv_path = input('输入框：')
    print('=' * 50)

    user_query = f"{absolute_csv_path}"

    print("\n" + "=" * 50)
    print(f"用户请求: {user_query}")
    print("=" * 50 + "\n")
    config = {'configurable': {'thread_id': 'algebraist'}}

    try:
        print("Agent 开始思考并执行任务...")
        # 修正：之前自我导入了 agent，这里直接使用全局的 agent
        # 注意：ainvoke 是异步的
        res = await agent.ainvoke({"messages": [("user", user_query)]}, config)

        if '__interrupt__' in res and res['__interrupt__']:
            interrupt_data = res['__interrupt__'][0].value
            action_req = interrupt_data['action_requests'][0]

            print(f"拦截到敏感操作：{action_req['name']}")
            print(f"该敏感操作对应的数据:{action_req['args']}")
            print('=' * 50)
            # 本地运行才询问，API部署时不应在这里询问 input
            user_choice = input('是否同意该操作？(y/n):').strip().lower()
            if user_choice == 'y':
                decision = Command(resume={'decisions': [{'action_name': action_req['name'], 'type': 'approve'}]})
                # 修正：ainvoke
                final_res = await agent.ainvoke(decision, config)
                print(f"智能体最终回答：{final_res['messages'][-1].content}")
            else:
                decision = Command(resume={'decisions': [{'action_name': action_req['name'], 'type': 'reject'}]})
                # 修正：ainvoke
                final_res = await agent.ainvoke(decision, config)
                print(f'智能体回复：{final_res['messages'][-1].content}')

        print("\n" + "=" * 50)
        print("Agent 最终回复:")
        # 打印大模型最后输出的文本内容
        if isinstance(res, dict) and "messages" in res:
            print(res["messages"][-1].content)
        else:
            print(res)
        print("=" * 50)
    finally:
        # 在这里调用 close_sandbox()，释放沙盒资源
        print("清理环境...")
        close_sandbox()


if __name__ == "__main__":
    # 执行前确保你已经在当前终端配置好了对应的环境变量
    asyncio.run(main())