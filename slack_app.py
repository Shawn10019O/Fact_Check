from fastapi import FastAPI, Request
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from slack_sdk.web.async_client import AsyncWebClient
from pyngrok import ngrok 
import os
import tempfile
import aiohttp
import atexit
from pathlib import Path
import uvicorn
import nest_asyncio
import threading
from dotenv import load_dotenv
import time
from core.models import results_to_markdown
from core.models import SlideResult
from core.process import process_file

load_dotenv()
# ngrok起動
ngrok.set_auth_token(os.getenv("NGROK_AUTH_TOKEN"))
tunnel = ngrok.connect(8000, bind_tls=True)           
public_url = tunnel.public_url                        
print(f"🌐  Slack Request URL → {public_url}/slack/events") 
atexit.register(lambda: ngrok.disconnect(tunnel.public_url))


bolt_app = AsyncApp(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
)
handler = AsyncSlackRequestHandler(bolt_app)

# ファイル共有イベント
@bolt_app.event("file_shared")
async def on_file_shared(body, client: AsyncWebClient, logger):
    file_id  = body["event"]["file_id"]
    channel  = body["event"]["channel_id"]
    info     = await client.files_info(file=file_id)
    url      = info["file"]["url_private_download"]
    filename = info["file"]["name"]

    headers = {"Authorization": f"Bearer {os.environ['SLACK_BOT_TOKEN']}"}
    async with aiohttp.ClientSession() as sess:
      async with sess.get(url, headers=headers) as resp:
        data = await resp.read()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1])
    tmp.write(data)
    tmp.close()

    results: list[SlideResult] = await process_file(Path(tmp.name), llm_model="gpt-4o")
    blocks = build_blocks(results)

    await client.chat_postMessage(channel=channel, blocks=blocks, text="Fact-check report")


def build_blocks(results: list[SlideResult]) -> list[dict]:
    md = results_to_markdown(results)
    return [{
        "type": "section",
        "text": {"type": "mrkdwn", "text": md}
    }]


app = FastAPI()
# Slack Events APIからのリクエストを受け付けるエンドポイント
@app.post("/slack/events")
async def slack_events(request: Request):
    return await handler.handle(request)


if __name__ == "__main__":
    nest_asyncio.apply()

    def _run():
        uvicorn.run("slack_app:app", host="0.0.0.0", port=8000,
                    log_level="info", access_log=False)

    threading.Thread(target=_run, daemon=True).start()
    while True:
        time.sleep(3600)