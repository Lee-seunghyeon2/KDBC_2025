import asyncio
import os # os.devnull 사용을 위해 import 합니다.

class StdioServerParameters: # 어떻게 mcp server을 실행할 지 결정
    def __init__(self, command, args=None, env=None, cwd=None):
        self.command = command # 실행할 명령어
        self.args = args or [] # 인자 리스트
        self.env = env or {} # 실행 시 환경변수 설정
        self.cwd = cwd or "." # 작업 디렉토리 설정

async def stdio_client(params: StdioServerParameters):
    proc = await asyncio.create_subprocess_exec(
        params.command,
        *params.args,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        # 핵심 수정: stderr를 DEVNULL로 리디렉션하여 fileno() 오류 방지
        stderr=asyncio.subprocess.DEVNULL,
        env=params.env,
        cwd=params.cwd
    )
    return proc.stdout, proc.stdin