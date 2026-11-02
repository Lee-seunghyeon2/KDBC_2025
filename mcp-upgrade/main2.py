import asyncio
import json
import os
import sys
import random
# from pathlib import Path # 사용되지 않아 주석 처리
# import requests # 사용되지 않아 주석 처리

# mcp 라이브러리에서 필요한 클래스 임포트
# MCP 라이브러리가 설치되어 있거나 PYTHONPATH에 경로가 추가되어 있어야 합니다.
from mcp import ClientSession # mcp/session.py에 ClientSession이 있다면 이렇게 임포트
from mcp.client.stdio import stdio_client, StdioServerParameters

# 만약 mcp 라이브러리가 별도의 경로에 있다면 sys.path를 조정해야 할 수 있습니다.
# 예: sys.path.append('/path/to/your/mcp_library')

async def run_gemma_mcp():  ## client의 stdio.py에 있는 설정 부분에 거를 가져다가 쓰기
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"],
        env={"PYTHONPATH": "."},
        cwd=os.path.dirname(__file__)
    )

    read, write = await stdio_client(server_params)
    session = ClientSession(read, write)
    await session.initialize()

    tools = await session.list_tools()

    import random
    method = random.choice(["youtube_music", "youtube_trend"])

    gemma_response = {
        "method": method,
        "parameters": {"max_results": 10}
    }

    try:
        calls = gemma_response

        if isinstance(calls, dict):
            calls = [calls]

        all_outputs = []

        for call in calls:
            method = call["method"]
            args = call["parameters"]

            result = await session.call_tool(method, arguments=args)
            content = result.content[0] if isinstance(result.content, list) else result.content
            tool_result = json.loads(content) if isinstance(content, str) else content

            print(f"{tool_result}")

            summary = None

            if method in {"youtube_trend", "youtube_music"}:
                try:
                    videos = tool_result["videos"]
                    video_summary = "\n\n".join(
                        f"제목: {v['title']}\n채널: {v['channel']}\n링크: {v['video_url']}"
                        for v in videos
                    )
                    summary = f"🔥 {method} 결과:\n\n{video_summary}"
                except Exception as e:
                    # 오류가 나더라도 응답을 최대한 살려서 출력
                    summary = (
                        f"⚠️ {method} 결과 처리 중 오류: {e}\n"
                        f"📦 원본 응답:\n{json.dumps(tool_result, ensure_ascii=False, indent=2)}"
                    )
            else:
                summary = f"🔧 {method} 결과:\n{json.dumps(tool_result, ensure_ascii=False, indent=2)}"

    except Exception as e:
        print(e)

# 스크립트 실행 시 run_gemma_mcp 함수 호출
if __name__ == "__main__":
    # Python 3.7+에서 비동기 함수를 실행하는 표준 방법
    asyncio.run(run_gemma_mcp())
