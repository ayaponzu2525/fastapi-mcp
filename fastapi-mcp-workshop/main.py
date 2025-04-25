from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_mcp import FastApiMCP
import httpx  # 追加


app = FastAPI()
templates = Jinja2Templates(directory="templates")

# MCPサーバー組み込み
mcp = FastApiMCP(app, name="MCP UI Test", description="チャットUIつき！")
mcp.mount()

@app.get("/", response_class=HTMLResponse)
async def form_get(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

import uuid

@app.post("/", response_class=HTMLResponse)
async def form_post(request: Request, session_id: str = Form(None), content: str = Form("")):
    if not content.strip():
        return templates.TemplateResponse("chat.html", {
            "request": request,
            "response": "⚠ 'content'が空です。メッセージを入力してください。",
            "session_id": session_id
        })

    async with httpx.AsyncClient() as client:
        try:
            # リクエストボディの準備
            request_data = {"content": content}
            
            # セッションIDの処理
            # 新規セッションの場合はUUIDを生成、既存セッションの場合はそのまま使用
            current_session_id = session_id if session_id and not session_id.strip().isdigit() else str(uuid.uuid4())
            
            # エンドポイントURL
            endpoint_url = f"http://localhost:8000/mcp/messages/?session_id={current_session_id}"
            
            # デバッグ出力
            print(f"リクエスト送信先: {endpoint_url}")
            print(f"リクエストデータ: {request_data}")
            print(f"セッションID: {current_session_id}")
            
            # リクエスト送信
            res = await client.post(endpoint_url, json=request_data)
            
            # レスポンスの処理
            if res.status_code == 200:
                response_data = res.json()
                current_session = response_data.get("session_id", current_session_id)
                response_content = response_data.get("content", "応答内容がありません")
            else:
                # エラー時のレスポンス
                return templates.TemplateResponse("chat.html", {
                    "request": request,
                    "response": f"⚠ API エラー: ステータスコード {res.status_code} - {res.text}",
                    "session_id": current_session_id
                })

            return templates.TemplateResponse("chat.html", {
                "request": request,
                "response": response_content,
                "session_id": current_session,
            })

        except Exception as e:
            return templates.TemplateResponse("chat.html", {
                "request": request,
                "response": f"⚠ 例外発生: {str(e)}",
                "session_id": current_session_id
            })