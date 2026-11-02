from .client.stdio import stdio_client, StdioServerParameters
from .server.fastmcp import FastMCP
from tools.youtube_trend_tool import get_trending_videos
from tools.youtube_music_tool import get_trending_music_videos

class ClientSession:
    def __init__(self, read, write):
        self.read = read
        self.write = write

    async def initialize(self):
        pass  # placeholder

    async def list_tools(self):
        return ["calculator","youtube_trend","youtube_music"]

    async def call_tool(self, method: str, arguments: dict):
        class Response:
            pass
 
        if method == "calculator":
            result = "계산 결과입니다"  # 여기에 실제 계산 로직을 넣어도 됩니다.
            Response.content = [{"text": result}]
            return Response()

        elif method == "youtube_trend":
            max_results = arguments.get("max_results", 3)  # 🔹 기본값 3
            trend_data = await get_trending_videos(max_results=max_results)

            if isinstance(trend_data, dict) and trend_data.get("status") == "ok":
            # 유튜브 트렌드 리스트를 텍스트로 구성
                videos = trend_data["videos"]
                messages = []
                for i, video in enumerate(videos, 1):
                    messages.append(
                        f"{i}. {video['title']} ({video['channel']})\n"
                    )
                text_output = "\n\n".join(messages)
                Response.content = [{"text": text_output}]
            else:
                # 에러 메시지 반환
                error_message = trend_data.get("message", "YouTube 트렌드 정보를 가져오는 데 실패했습니다.")
                Response.content = [{"text": f"[오류] {error_message}"}]

            return Response()

        elif method == "youtube_music":
            max_results = arguments.get("max_results", 3)  # 🔹 기본값 3
            trend_data = await get_trending_music_videos(max_results=max_results)

            if isinstance(trend_data, dict) and trend_data.get("status") == "ok":
            # 유튜브 트렌드 리스트를 텍스트로 구성
                videos = trend_data["videos"]
                messages = []
                for i, video in enumerate(videos, 1):
                    messages.append(
                        f"{i}. {video['title']} ({video['channel']})\n"
                    )
                text_output = "\n\n".join(messages)
                Response.content = [{"text": text_output}]
            else:
                # 에러 메시지 반환
                error_message = trend_data.get("message", "YouTube 음악 정보를 가져오는 데 실패했습니다.")
                Response.content = [{"text": f"[오류] {error_message}"}]

            return Response()
        
        else:
            Response.content = [{"text": f"{method}는 알 수 없는 도구입니다"}]
            return Response()
