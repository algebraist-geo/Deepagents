# import os
# import json
# from typing import Optional
# from langchain_core.tools import tool
# from e2b import Sandbox
#
#
# # 确保在模块级别获取或初始化沙箱环境
# # 注意：这会读取你在主程序中设置的环境变量
# def _get_sandbox() -> Sandbox:
#     api_key = os.environ.get('SandBoxE2B')
#     if not api_key:
#         raise ValueError("未找到环境变量 'SandBoxE2B'，请检查沙箱配置。")
#     # 如果宿主程序已经把 e2b_sandbox 挂载到了某个全局上下文，这里也可以直接复用
#     return Sandbox.create(api_key=api_key)
#
#
# @tool
# def e2b_upload_dataset(local_file_path: str, remote_file_name: str) -> str:
#     """
#     将宿主机本地的数据集（CSV, Parquet, Excel等）安全上传至远端隔离的 E2B 沙箱内部存储区。
#     在对任何本地数据进行清洗、统计建模或图表绘制前，必须【首先】调用此工具将数据资产上云。
#
#     Args:
#         local_file_path: 本地文件的绝对或相对路径（例如 './data/user_scores.csv'）
#         remote_file_name: 希望在沙箱中保存的文件名（例如 'dataset.csv'，将默认存放在 /home/user/ 下）
#
#     Returns:
#         沙箱内的绝对文件路径（如 '/home/user/dataset.csv'），后续执行 Python 代码时需填入此路径。
#     """
#     try:
#         sandbox = _get_sandbox()
#         if not os.path.exists(local_file_path):
#             return f"错误：本地路径 {local_file_path} 不存在，请核对。"
#
#         with open(local_file_path, "rb") as f:
#             file_content = f.read()
#
#         # 调用 E2B 原生 API 写入沙箱文件系统
#         sandbox.files.write(f"./{remote_file_name}", file_content)
#         return f"/home/user/{remote_file_name}"
#     except Exception as e:
#         return f"数据上传沙箱失败: {str(e)}"
#
#
# @tool
# def e2b_execute_python(code: str) -> str:
#     """
#     在隔离的 E2B 沙箱内以代码级执行任意复杂的 Python 数据处理脚本（支持 Pandas, NumPy, Scikit-learn, Matplotlib）。
#     适用于海量数据集的清洗、探索性数据分析(EDA)、统计建模、机器学习训练以及可视化图表绘制。
#     解决大模型在复杂数学计算和大规模数据处理上的局限性。
#
#     注意守则：
#     1. 必须使用 try-except 块包裹核心逻辑，防御性编程，防止进程崩溃。
#     2. 严禁使用 input()、time.sleep() 等阻塞交互指令。
#     3. 生成图表时，必须使用 plt.savefig('/home/user/xxx.png', bbox_inches='tight') 强制保存到沙箱中。
#
#     Args:
#         code: 需要执行的完整 Python 代码字符串。
#
#     Returns:
#         包含标准输出（stdout）、标准错误（stderr）的 JSON 字符串结构。
#     """
#     try:
#         sandbox = _get_sandbox()
#         # 执行沙箱代码
#         execution = sandbox.commands.run_python(code)
#
#         result = {
#             "stdout": execution.stdout,
#             "stderr": execution.stderr,
#             "error": execution.error
#         }
#
#         return json.dumps(result, ensure_ascii=False, indent=2)
#     except Exception as e:
#         return json.dumps({"error": f"沙箱代码执行器异常: {str(e)}"}, ensure_ascii=False)
#
#
# @tool
# def e2b_download_artifact(remote_path: str, local_save_path: str) -> str:
#     """
#     从远端 E2B 沙箱中将清洗好的新数据集、训练好的模型权重（.pkl）或生成的可视化图表（.png, .pdf）下载导出至本地宿主机。
#     当用户明确要求“下载”、“保存”或需要查看分析生成的图表报告时使用。
#
#     Args:
#         remote_path: 沙箱内部的文件路径（例如 '/home/user/revenue_trend.png'）
#         local_save_path: 本地宿主机的保存路径（例如 './output/trend.png'）
#
#     Returns:
#         保存成功的状态提示信息。
#     """
#     try:
#         sandbox = _get_sandbox()
#         # 读取远端文件二进制流
#         file_bytes = sandbox.files.read(remote_path)
#
#         # 确保本地目录存在
#         local_dir = os.path.dirname(local_save_path)
#         if local_dir and not os.path.exists(local_dir):
#             os.makedirs(local_dir, exist_ok=True)
#
#         with open(local_save_path, "wb") as f:
#             f.write(file_bytes)
#         return f"成功：文件已从沙箱下载并保存至本地 {local_save_path}"
#     except Exception as e:
#         return f"导出分析结果失败: {str(e)}"
#
#
# @tool
# def e2b_list_workspace(dir_path: Optional[str] = "./") -> str:
#     """
#     进行沙盒状态审计。检查当前 E2B 分析环境中的文件和文件夹结构列表。
#     当需要确认临时生成的数据位置、检查图表是否生成成功、或核对沙箱内文件分布时使用。
#
#     Args:
#         dir_path: 目标审计目录，默认为 "./" (即 /home/user/)
#
#     Returns:
#         文件列表信息。
#     """
#     try:
#         sandbox = _get_sandbox()
#         files = sandbox.files.list(dir_path)
#         file_list = [f.name for f in files]
#         return f"当前沙箱工作区 [{dir_path}] 内的文件有: {file_list}"
#     except Exception as e:
#         return f"审计沙箱工作区失败: {str(e)}"


import os
import json
from typing import Optional
from langchain_core.tools import tool
#from e2b import Sandbox
from e2b_code_interpreter import Sandbox

# ---------------------------------------------------------------------------
# 全局沙箱单例管理（防止每次工具调用都重新创建孤立的新虚拟机，导致文件系统不共享）
# ---------------------------------------------------------------------------
_GLOBAL_SANDBOX: Optional[Sandbox] = None


def get_sandbox() -> Sandbox:
    """
    获取或延迟初始化全局共享的 E2B 沙箱实例。
    保证上传数据集、代码执行、报告合成以及产物下载都在【同一个沙箱】中完成。
    """
    global _GLOBAL_SANDBOX
    if _GLOBAL_SANDBOX is None:
        api_key = os.environ.get('SandBoxE2B') or os.environ.get('E2B_API_KEY')
        if not api_key:
            raise ValueError("未找到环境变量 'SandBoxE2B'，请检查沙箱配置。")
        _GLOBAL_SANDBOX = Sandbox.create(api_key=api_key,timeout=3600)
    return _GLOBAL_SANDBOX


def close_sandbox():
    """
    显式销毁沙箱资源。建议在 Agent 完整对话/分析任务结束时调用，避免云端算力泄露。
    """
    global _GLOBAL_SANDBOX
    if _GLOBAL_SANDBOX is not None:
        try:
            _GLOBAL_SANDBOX.kill()
        finally:
            _GLOBAL_SANDBOX = None


# ---------------------------------------------------------------------------
# LangChain 工具接口定义 (Docstring 已与 skill.md 对齐)
# ---------------------------------------------------------------------------

@tool
def e2b_upload_dataset(local_file_path: str, remote_file_name: str) -> str:
    """
    将宿主机本地的数据集（CSV, Parquet, Excel 等）安全上传至远端隔离的 E2B 沙箱内部存储区。
    在进行任何数据探查、统计建模、可视化或报告合成前，必须【首先】调用此工具将数据资产上传至沙箱。

    Args:
        local_file_path: 本地文件的绝对或相对路径（例如 './data/user_scores.csv'）
        remote_file_name: 希望在沙箱中保存的文件名（例如 'dataset.csv'，将默认存放在 /home/user/ 下）

    Returns:
        沙箱内的绝对文件路径（如 '/home/user/dataset.csv'），后续执行 Python 代码时需填入此路径。
    """
    print('正在调用：e2b_upload_dataset上传数据')
    try:
        sandbox = get_sandbox()
        if not os.path.exists(local_file_path):
            return f"错误：本地路径 {local_file_path} 不存在，请核对。"

        with open(local_file_path, "rb") as f:
            file_content = f.read()

        # 调用 E2B 原生 API 写入沙箱文件系统
        sandbox.files.write(f"./{remote_file_name}", file_content)
        return f"/home/user/{remote_file_name}"
    except Exception as e:
        return f"数据上传沙箱失败: {str(e)}"



@tool
def e2b_execute_python(code: str) -> str:
    """
    在隔离的 E2B 沙箱内以代码级执行任意复杂的 Python 数据处理脚本（支持 Pandas, NumPy, Scikit-learn, Matplotlib）。
    适用于数据探查(EDA)、统计建模、图表绘制以及【生成结构化 Markdown/PDF 分析报告】。

    执行守则：
    1. 必须使用 try-except 块包裹核心逻辑，防御性编程，防止进程崩溃。
    2. 严禁使用 input()、time.sleep() 等阻塞交互指令。
    3. 生成图表时，必须使用 plt.savefig('/home/user/xxx.png', bbox_inches='tight') 保存。
    4. 分析完成后，必须使用 Python 将结论写成完整的 Markdown 报告文件（如 /home/user/final_analysis_report.md）。

    Args:
        code: 需要执行的完整 Python 代码字符串。

    Returns:
        包含标准输出（stdout）、标准错误（stderr）及错误的 JSON 格式字符串。
    """
    print('正在调用：e2b_execute_python运行脚本')
    try:
        sandbox = get_sandbox()
        # 执行沙箱代码
        execution = sandbox.run_code(code,timeout=1800)

        result = {
            "stdout": execution.logs.stdout,
            "stderr": execution.logs.stderr,
            "error": execution.error
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": f"沙箱代码执行器异常: {str(e)}"}, ensure_ascii=False)


@tool
def e2b_download_artifact(remote_path: str, local_save_path: str) -> str:
    """
    从远端 E2B 沙箱中将分析产物下载导出至本地宿主机。
    支持下载的文件类型包含：
    1. 生成的完整数据分析报告（如 '/home/user/final_analysis_report.md' 或 '.pdf'）
    2. 可视化图表（.png, .svg）
    3. 清洗后的新数据集（.csv, .parquet）或模型权重（.pkl）

    当完成了数据分析、图表生成与报告编写后，必须调用此工具将生成的分析报告和图表导出给用户。

    Args:
        remote_path: 沙箱内部的文件路径（例如 '/home/user/final_analysis_report.md' 或 '/home/user/revenue_trend.png'）
        local_save_path: 本地宿主机的保存路径（例如 './output/final_analysis_report.md'）

    Returns:
        保存成功的状态提示信息。
    """
    print('正在调用：e2b_download_artifact下载文件')
    try:
        sandbox = get_sandbox()
        # 读取远端文件二进制流
        file_bytes = sandbox.files.read(remote_path,format="bytes")

        # 确保本地目标目录存在
        local_dir = os.path.dirname(local_save_path)
        if local_dir and not os.path.exists(local_dir):
            os.makedirs(local_dir, exist_ok=True)

        with open(local_save_path, "wb") as f:
            f.write(file_bytes)
            print('-'*100)
            print(f"成功：分析产物已从沙箱下载并保存至本地 {local_save_path}")
        return f"成功：分析产物已从沙箱下载并保存至本地 {local_save_path}"

    except Exception as e:
        print(f"导出分析结果失败: {str(e)}")
        return f"导出分析结果失败: {str(e)}"


@tool
def e2b_list_workspace(dir_path: Optional[str] = "./") -> str:
    """
    进行沙箱状态审计。检查当前 E2B 分析环境中的文件和文件夹结构列表。
    当需要确认分析报告是否已生成（如 final_analysis_report.md）、确认图表路径或核对数据文件位置时使用。

    Args:
        dir_path: 目标审计目录，默认为 "./" (即 /home/user/)

    Returns:
        文件列表信息。
    """
    try:
        sandbox = get_sandbox()
        files = sandbox.files.list(dir_path)
        file_list = [f.name for f in files]
        return f"当前沙箱工作区 [{dir_path}] 内的文件有: {file_list}"
    except Exception as e:
        return f"审计沙箱工作区失败: {str(e)}"