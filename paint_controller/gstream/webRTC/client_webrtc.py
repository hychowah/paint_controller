import asyncio
import json
import websockets
import cv2
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaStreamTrack

async def run():
    pc = RTCPeerConnection()

    @pc.on("track")
    def on_track(track):
        if track.kind == "video":
            print("Receiving video track")

            async def display_track():
                while True:
                    frame = await track.recv()
                    img = frame.to_ndarray(format="bgr24")
                    cv2.imshow("WebRTC Video", img)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                cv2.destroyAllWindows()

            asyncio.ensure_future(display_track())

    async with websockets.connect("ws://localhost:8080") as websocket:
        @pc.on("icecandidate")
        async def on_icecandidate(candidate):
            if candidate:
                await websocket.send(json.dumps({
                    "type": "candidate",
                    "candidate": candidate.sdp,
                    "sdpMid": candidate.sdpMid,
                    "sdpMLineIndex": candidate.sdpMLineIndex,
                }))

        async def consume_signaling():
            async for message in websocket:
                data = json.loads(message)
                if data["type"] == "offer":
                    await pc.setRemoteDescription(RTCSessionDescription(sdp=data["sdp"], type=data["type"]))
                    await pc.setLocalDescription(await pc.createAnswer())
                    await websocket.send(json.dumps({
                        "type": "answer",
                        "sdp": pc.localDescription.sdp
                    }))
                elif data["type"] == "candidate":
                    candidate = {
                        "sdpMid": data["sdpMid"],
                        "sdpMLineIndex": data["sdpMLineIndex"],
                        "candidate": data["candidate"]
                    }
                    await pc.addIceCandidate(candidate)

        await consume_signaling()

asyncio.run(run())
