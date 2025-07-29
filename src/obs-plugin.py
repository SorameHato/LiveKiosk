# obs_fastapi_server.py
import obspython as obs # type: ignore
import threading
import time, datetime
import uvicorn
import asyncio
import os, sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from api import db, youtube
from __init__ import __version__

app = FastAPI()
ws_clients : set[WebSocket] = set()
# 전역 참조 변수
uvicorn_loop = None
recordBtn_enable = db.get_setting('obs_record_button_enabled') == '1'

html = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>LiveKiosk v'''+__version__+'''</title>
    <link rel="stylesheet" as="style" crossorigin href="https://cdnjs.cloudflare.com/ajax/libs/pretendard/1.3.9/variable/pretendardvariable-dynamic-subset.min.css" />
    <style>
    html, body, * {
      background-color: #272A33;
      color: #ffffff !important;
      font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, "Helvetica Neue", "Segoe UI", "Apple SD Gothic Neo", "Noto Sans KR", "Malgun Gothic", "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", sans-serif !important;
      box-sizing: border-box;
    }

    /* 클래스 title인 요소 */
    .title {
    font-size: 24px;
    font-weight: 500;
    text-align: center;
    }

    /* 클래스 log인 요소 */
    .log {
    font-size: 14px;
    font-weight: 500;
    }

    /* button1 클래스가 붙은 button 요소 */
    button.record_off {
    background-color: #3C404D;
    border: 1px solid transparent;
    }

    button.record_off:hover {
    background-color: #464B59;
    border: 1px solid #5B6273;
    }

    /* button2 클래스가 붙은 button 요소 */
    button.record_on {
    background-color: #284CB8;
    border: 1px solid transparent;
    }

    button.record_on:hover {
    background-color: #476BD7;
    border: 1px solid #718CDC;
    }

    /* 모든 button 공통 속성 (width 100%) */
    button {
    width: 100%;
    box-sizing: border-box;
    width: 100%;
    cursor: pointer;
    border-radius: 5px;
    margin: 8px 0px;
    font-size: 18px;
    padding: 8px 16px;
    }
  </style>
</head>
<body>
    <div class="title">LiveKiosk</div>
    <div class="log">LiveKiosk v'''+__version__+'<br>'+db.get_setting('center_name')+'<br>'+db.get_setting('device_name')+'<br><br>'+db.get_setting('obs_widget_information').replace('\n','<br>')+'</div>'
if recordBtn_enable:
    html += '''\n<button id="recordBtn" onclick="toggleRecording()">...</button>

    <script>
        let ws = new WebSocket("ws://127.0.0.1:51031/ws");

        ws.onmessage = function(event) {
            let msg = JSON.parse(event.data);
            if (msg.type === "recording_status") {
                let btn = document.getElementById("recordBtn");
                if (msg.running) {
                    btn.textContent = "녹화 종료"
                    btn.classList.add("record_on");
                    btn.classList.remove("record_off");
                } else {
                    btn.textContent = "녹화 시작"
                    btn.classList.add("record_off");
                    btn.classList.remove("record_on");
        }
            }
        };

        function toggleRecording() {
            ws.send(JSON.stringify({ type: "toggle_recording" }));
        }
    </script>'''
html += '\n</body>\n</html>'

@app.get("/")
def get_page():
    return HTMLResponse(content=html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ws_clients.add(websocket)
    try:
        # 시작 시 상태 전송
        await websocket.send_json({
            "type": "recording_status",
            "running": obs.obs_frontend_recording_active()
        })

        while True:
            data = await websocket.receive_json()
            if data["type"] == "toggle_recording":
                is_active = obs.obs_frontend_recording_active()
                if is_active:
                    obs.obs_frontend_recording_stop()
                else:
                    obs.obs_frontend_recording_start()
                # 상태 전파는 OBS 이벤트에서 처리됨
            await websocket.send_json({
                "type": "test"
            })
    except WebSocketDisconnect:
        ws_clients.discard(websocket)

# OBS -> 클라이언트: 녹화 상태 전송
def broadcast_recording_status():
    global uvicorn_loop
    running = obs.obs_frontend_recording_active()
    for ws in list(ws_clients):
        try:
            asyncio.run_coroutine_threadsafe(ws.send_json({
                "type": "recording_status",
                "running": running
            }), uvicorn_loop)
        except Exception as e:
            print("WebSocket 오류:", e)

def stream_restart():
    mode = db.get_setting('stream_autocreate_enabled')
    if mode == '0':
        return
    else:
        while True:
            if mode == '1':
                time.sleep(int(db.get_setting('stream_autorestart_dur'))*60)
            else:
                import pause
                now = datetime.datetime.now()
                now_tc = db.getTimeCode(now.hour,now.minute)
                next1, next2 = db.fetch_restart_time(now.weekday())
                if next1 is not None and next2 is not None:
                    if next1 > now_tc and next2 > now_tc:
                        next_tc = min(next1, next2)
                    elif next1 > now_tc or next2 > now_tc:
                        next_tc = next1 if next1 > now_tc else next2
                    else:
                        next_tc = min(next1, next2)
                elif next1 is not None:
                    next_tc = next1
                elif next2 is not None:
                    next_tc = next2
                else:
                    next_tc = now_tc
                hour, minute = db.getTimeStamp2(next_tc)
                next_time = now.replace(hour=hour, minute=minute,second=0,microsecond=0)
                if next_time <= now:
                    next_time += datetime.timedelta(days=1)
                pause.until(next_time)

            credential = youtube.auth()
            if obs.obs_frontend_streaming_active():
                obs.obs_frontend_streaming_stop()
                youtube.broadcast_comp(credential)
                time.sleep(3)  # 완전히 멈췄는지 대기(최소 1~2초)
            if db.get_setting('stream_autocreate_enabled') == '1':
                now = datetime.datetime.now()
                date1 = now.strftime('%Y년 %m월 %d일')
                date2 = now.strftime('%Y-%m-%d')
                date3 = now.strftime('%Y/%m/%d')
                b_title = db.get_setting('stream_title').replace('{date1}',date1).replace('{date2}',date2).replace('{date3}',date3).replace('{center}',db.get_setting('stream_center')).replace('{device}',db.get_setting('stream_device'))
                b_desc = db.get_setting('stream_desc').replace('{date1}',date1).replace('{date2}',date2).replace('{date3}',date3).replace('{center}',db.get_setting('stream_center')).replace('{device}',db.get_setting('stream_device'))
                youtube.create_broadcast(b_title, b_desc, credential)
            obs.obs_frontend_streaming_start()

def stream_complete():
    mode = db.get_setting('shutdown_enabled')
    if mode == '0':
        return
    else:
        import pause
        now = datetime.datetime.now()
        start, end = db.fetch_operation_time(now.weekday())
        hour, minute = db.getTimeStamp2(end)
        next_time = now.replace(hour=hour, minute=minute,second=0,microsecond=0)
        next_time -= datetime.timedelta(minutes=2)
        if next_time <= now:
            next_time += datetime.timedelta(days=1)
        pause.until(next_time)

        credential = youtube.auth()
        if obs.obs_frontend_recording_active():
            obs.obs_frontend_recording_stop()
        if obs.obs_frontend_streaming_active():
            obs.obs_frontend_streaming_stop()
            youtube.broadcast_comp(credential)

# OBS 이벤트 콜백
def on_event(event):
    if recordBtn_enable and event in [obs.OBS_FRONTEND_EVENT_RECORDING_STARTED, obs.OBS_FRONTEND_EVENT_RECORDING_STOPPED]:
        broadcast_recording_status()

def start_fastapi():
    global uvicorn_loop
    config = uvicorn.Config(app, host="127.0.0.1", port=51031,use_colors=False,log_level="critical")
    server = uvicorn.Server(config)
    # 서버 이벤트루프는 main thread에서 호출됨
    uvicorn_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(uvicorn_loop)
    uvicorn_loop.run_until_complete(server.serve())

def script_load(settings):
    obs.obs_frontend_add_event_callback(on_event)

    # FastAPI 서버 백그라운드로 실행
    server_thread = threading.Thread(target=start_fastapi, daemon=True)
    server_thread.start()

    threading.Thread(target=stream_restart, daemon=True).start()
    threading.Thread(target=stream_complete, daemon=True).start()

def script_unload():
    obs.obs_frontend_remove_event_callback(on_event)

def script_description():
    return "LiveKiosk OBS Studio 프론트엔드 플러그인입니다."

def script_properties():
    return None