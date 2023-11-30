import asyncio
import base64
import json
import logging
import os
import time
from enum import Enum
from typing import Optional, AsyncGenerator

import aiohttp
import websockets
from pydantic import BaseModel

from eleven.config import (
    VOICE_ID
)


class ElevenLabsMode(Enum):
    STREAMING = "eleven_labs_streaming"
    INPUT_STREAMING = "eleven_labs_input_streaming"


class InputStreamingLatencyData(BaseModel):
    stream_generation_time: Optional[float] = None
    first_text_chunk_sent_timestamp: Optional[float] = None
    first_audio_chunk_received_timestamp: Optional[float] = None

    @property
    def first_audio_chunk_generation_time(self):
        return self.first_audio_chunk_received_timestamp - self.first_text_chunk_sent_timestamp


class StreamingLatencyData(BaseModel):
    stream_generation_time: Optional[float] = None
    first_chunk_generation_time: Optional[float] = None


class ElevenLabsBenchmark:
    logger = logging.getLogger("eleven_labs_api_benchmark")
    logger.setLevel(logging.DEBUG)
    websocket_endpoint = f"wss://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream-input"
    stream_endpoint = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"

    BOS = json.dumps(
        dict(
            text=" ",
            try_trigger_generation=True,
            generation_config=dict(
                chunk_length_schedule=[50],
            ),
        )
    )
    EOS = json.dumps(dict(text=""))

    @staticmethod
    async def _send_text_chunks(text_chunk_gen: AsyncGenerator, websocket: websockets.WebSocketClientProtocol,
                                latency_data: InputStreamingLatencyData, logger):
        logger.debug("Starting to send text chunks to websocket...")
        async for text_chunk in text_chunk_gen:
            chunk_data = dict(text=text_chunk, try_trigger_generation=True)
            await websocket.send(json.dumps(chunk_data))
            latency_data.first_text_chunk_sent_timestamp = time.time()
            logger.debug(f"Sent {text_chunk} to websocket")
        await websocket.send(ElevenLabsBenchmark.EOS)
        logger.debug("All text chunks sent to websocket, EOS message sent")

    @staticmethod
    async def _create_live_speech(text_chunk_gen, latency_data: InputStreamingLatencyData, logger):
        connection_start_time = time.time()
        async with websockets.connect(
                ElevenLabsBenchmark.websocket_endpoint,
                extra_headers={"xi-api-key": os.environ.get("ELEVEN_LABS_API_KEY")},
        ) as websocket:
            connection_end_time = time.time()
            latency_data.stream_generation_time = connection_end_time - connection_start_time
            ElevenLabsBenchmark.logger.debug("WebSocket connection established")
            await websocket.send(ElevenLabsBenchmark.BOS)
            logger.debug("BOS message sent")

            asyncio.create_task(ElevenLabsBenchmark._send_text_chunks(
                text_chunk_gen=text_chunk_gen,
                latency_data=latency_data,
                websocket=websocket,
                logger=logger,
            ))

            is_first_chunk = True
            audio_chunks = []
            while True:
                try:
                    message = json.loads(await websocket.recv())
                    if audio := message.get("audio"):
                        logger.debug("Audio data received")
                        if is_first_chunk:
                            first_audio_chunk_received_timestamp = time.time()
                            latency_data.first_audio_chunk_received_timestamp = first_audio_chunk_received_timestamp
                            time_to_first_byte = first_audio_chunk_received_timestamp - latency_data.first_text_chunk_sent_timestamp
                            logger.debug(f"Time to first audio byte: {time_to_first_byte:.2f}")
                            is_first_chunk = False
                        audio_chunks.append(base64.b64decode(audio))
                except websockets.exceptions.ConnectionClosedOK:
                    logger.debug("WebSocket connection closed")
                    break
            return audio_chunks

    @staticmethod
    async def _create_speech(text, latency_data: StreamingLatencyData, logger):
        headers = {
            "xi-api-key": os.environ.get("ELEVEN_LABS_API_KEY"),
        }
        body = {
            "text": text,
            "model_id": "eleven_turbo_v2",
        }

        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            response = await session.request(
                "POST",
                ElevenLabsBenchmark.stream_endpoint,
                json=body,
                headers=headers,
            )
            end_time = time.time()

        if not response.ok:
            raise Exception(f"ElevenLabs API returned {response.status} status code")

        stream_generation_time = end_time - start_time
        latency_data.stream_generation_time = stream_generation_time

        logger.debug(f"Stream generation time: {end_time - start_time:.2f}")
        return response.content.iter_any()

    @staticmethod
    async def run(synthesis_input, mode=ElevenLabsMode.STREAMING, logger=None):
        if not logger:
            logger = ElevenLabsBenchmark.logger

        if mode == ElevenLabsMode.INPUT_STREAMING:
            latency_data = InputStreamingLatencyData()
            audio_chunks = await ElevenLabsBenchmark._create_live_speech(text_chunk_gen=synthesis_input,
                                                                         latency_data=latency_data, logger=logger)
            with open("eleven_api_benchmark.mp3", "wb") as f:
                for audio_chunk in audio_chunks:
                    f.write(audio_chunk)

        else:
            latency_data = StreamingLatencyData()
            audio_chunks = await ElevenLabsBenchmark._create_speech(text=synthesis_input, latency_data=latency_data,
                                                                    logger=logger)
            with open("eleven_api_benchmark.mp3", "wb") as f:
                is_first_chunk = True
                first_chunk_generation_start = time.time()
                async for audio_chunk in audio_chunks:
                    print("yay")
                    if is_first_chunk:
                        first_chunk_generation_end = time.time()
                        first_chunk_generation_time = first_chunk_generation_end - first_chunk_generation_start
                        latency_data.first_chunk_generation_time = first_chunk_generation_time
                        is_first_chunk = False
                        logger.debug(f"Time to first audio byte: {first_chunk_generation_time:.2f}")
                    f.write(audio_chunk)

        logger.info("Audio chunks written to file")

        return latency_data
