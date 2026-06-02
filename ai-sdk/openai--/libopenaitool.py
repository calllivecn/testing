r"""
使用示例:

from openai import OpenAI
from openai_tools import ToolManager
from pydantic import BaseModel, Field

# ===== 1. 定义工具参数模型 =====
class WebSearchParams(BaseModel):
    query: str = Field(..., description="搜索关键词")
    max_results: int = Field(5, ge=1, le=10, description="结果数量")

# ===== 2. 用 @tool 装饰器定义工具（关键！）=====
@tool_manager.tool("通过搜索引擎获取实时网络结果")
def web_search(params: WebSearchParams) -> dict:
    '''模拟搜索实现（参数自动是 Pydantic 模型）'''
    return {"results": [f"Result {i} for {params.query}" for i in range(params.max_results)]}

@tool_manager.tool("获取网页完整内容")
def fetch_webpage(url: str) -> str:  # 注意：这里直接写 str 类型（自动包装为模型）
    return f"Full text of {url}"

# ===== 3. 像 Ollama 一样使用工具 =====
client = OpenAI()
tool_manager = ToolManager(client)

# 3.1 定义工具列表（直接放函数对象！）
tools = [
    web_search,  # ✅ 直接传递函数
    fetch_webpage
]

messages = [{"role": "user", "content": "搜索今日AI新闻"}]

# 3.2 首次调用（模型决定是否需要工具）
response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,  # ✅ 直接传递函数列表！
    tool_choice="auto"
)

# 3.3 自动处理工具调用（核心简化！）
final_response = tool_manager.auto_invoke(
    response=response,
    tools=tools,  # 传递原始函数列表
    messages=messages
)

print("最终回答:", final_response.choices[0].message.content)
"""

from openai import OpenAI
from pydantic import BaseModel, create_model

from typing import Callable, List, Any, Dict, Optional, Type

import inspect
import json

class ToolManager:
    """让 OpenAI API 像 Ollama 一样使用工具调用"""
    
    def __init__(self, client: OpenAI):
        self.client = client
        self.functions: Dict[str, Callable] = {}
    
    def tool(self, description: str, strict: bool = True) -> Callable:
        """装饰器：将函数注册为工具（自动提取Pydantic参数）"""
        def decorator(func: Callable) -> Callable:
            # 1. 提取函数签名中的参数模型
            sig = inspect.signature(func)
            params = list(sig.parameters.values())
            
            # 2. 确保第一个参数是 Pydantic 模型 (Ollama 风格)
            if not params or not inspect.isclass(params[0].annotation) or not issubclass(params[0].annotation, BaseModel):
                raise TypeError(f"工具 {func.__name__} 必须以 Pydantic 模型作为第一个参数")
            
            param_model = params[0].annotation
            
            # 3. 构造 OpenAI 兼容的工具定义
            tool_def = {
                "type": "function",
                "function": {
                    "name": func.__name__,
                    "description": description,
                    "parameters": param_model.model_json_schema(),
                    "strict": strict
                }
            }
            
            # 4. 注册函数和工具定义
            self.functions[func.__name__] = func
            return (func, tool_def)  # 返回原始函数+工具定义
        
        return decorator
    
    def auto_invoke(
        self,
        response: Any,  # openai.types.chat.ChatCompletion
        tools: List[Callable],
        messages: List[Dict[str, str]],
        max_retries: int = 2
    ) -> Any:
        """自动处理工具调用（核心魔法）"""
        for _ in range(max_retries):
            msg = response.choices[0].message
            
            # 无需工具调用 → 直接返回
            if not msg.tool_calls:
                return response
            
            # 2. 执行所有工具调用
            for tool_call in msg.tool_calls:
                # 2.1 匹配注册的函数
                if tool_call.function.name not in self.functions:
                    raise ValueError(f"未注册工具: {tool_call.function.name}")
                
                func = self.functions[tool_call.function.name]
                
                # 2.2 自动解析参数（Pydantic 验证）
                args = json.loads(tool_call.function.arguments)
                param_model = list(inspect.signature(func).parameters.values())[0].annotation
                params = param_model(**args)  # 自动类型校验
                
                # 2.3 执行工具函数
                result = func(params)
                
                # 2.4 构造工具响应
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result) if not isinstance(result, str) else result
                })
            
            # 3. 重新请求模型（带工具结果）
            response = self.client.chat.completions.create(
                model=response.model,
                messages=messages,
                tools=[t[1] for t in tools],  # 提取工具定义
                tool_choice="auto"
            )
        
        return response
