import os
from dotenv import load_dotenv
from bookinggpt.agent.booking_agent import BookingAgent
from langchain_core.language_models.base import BaseLanguageModel
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

def main():
    # OpenAI-compatible LLM: works with OpenRouter, Zhipu, or any /v1 endpoint.
    # Config via .env:
    #   OPENAI_API_KEY=<key>
    #   OPENAI_BASE_URL=https://api.openrouter.ai/api/v1  (or provider of choice)
    #   MODEL_NAME=<model>
    llm: BaseLanguageModel = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        temperature=0.3,
    )

    booking_agent = BookingAgent(llm)

    print("Welcome to Daisy AI Booking Assistant! Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("exit", "quit", "tho\u00e1t"):
            print("Assistant: Thank you for using our service. Goodbye!")
            break
        response = booking_agent.call_agent(user_input)
        print(f"Assistant: {response}")

if __name__ == "__main__":
    main()
