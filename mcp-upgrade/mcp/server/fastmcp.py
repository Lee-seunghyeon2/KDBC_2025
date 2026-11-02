from typing import Callable ## callable: 호풀 가능한 객체 의미
from dotenv import load_dotenv
load_dotenv()

class FastMCP:
    def __init__(self, name: str): ## 서버 이름과 툴 저장 초기화
        self.name = name
        self.tools = {}

    def tool(self, name: str): ## 함수를 MCP tool로 등록하는 역할
        def wrapper(fn: Callable):
            self.tools[name] = fn
            return fn
        return wrapper

    def run(self): ## 서버 실행 루프 
        print(f"[MCP 서버 '{self.name}'] 실행 중... (등록된 도구: {list(self.tools.keys())})")
        import time
        while True:
            time.sleep(1)