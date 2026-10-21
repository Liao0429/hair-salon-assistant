import sys
import os
# Ensure project root is on sys.path so `bookinggpt` is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from bookinggpt.agent.booking_agent import BookingAgent


load_dotenv()
llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME", "u2-flash"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://maas-api.unisound.com/v1"),
    temperature=0.3,
    streaming=False,
)
agent = BookingAgent(llm)
print("=== 测试 1：询问服务清单（不触发日历工具） ===")
r1 = agent.call_agent("What services do you offer?")
print("AI:", r1)
