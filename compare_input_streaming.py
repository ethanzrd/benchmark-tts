# TTS services supporting input streaming: PlayHT & ElevenLabs

import asyncio
import logging
import time
from typing import List

from eleven.benchmark_api import (
    ElevenLabsBenchmark,
    ElevenLabsMode,
    InputStreamingLatencyData,
)
from play.benchmark_sdk import (
    PlayHTSDKBenchmark,
    PlayHTMode,
    LatencyData,
)
from utils import get_average_of_field_entries

logging.basicConfig()
playht_logger = logging.getLogger("input_streaming_playht")
eleven_logger = logging.getLogger("input_streaming_11labs")

playht_logger.setLevel(logging.INFO)
eleven_logger.setLevel(logging.INFO)

TOKEN_OUTPUT_LATENCY = 0.01
words = ["Hello ", "sir, ", "what ", "can ", "I ", "do ", "for ", "you?"]


def playht_text_gen():
    for word in words:
        yield word
        time.sleep(TOKEN_OUTPUT_LATENCY)


async def eleven_text_gen():
    for word in words:
        yield word
        await asyncio.sleep(TOKEN_OUTPUT_LATENCY)


playht_latency_records: List[LatencyData] = []
eleven_latency_records: List[InputStreamingLatencyData] = []

for i in range(10):
    playht_logger.info(f"WebSocket Connection {i + 1}")
    latency_data = PlayHTSDKBenchmark.run(synthesis_input=playht_text_gen(),
                                          mode=PlayHTMode.INPUT_STREAMING,
                                          logger=playht_logger)
    playht_latency_records.append(latency_data)

play_average_response_generation_time = get_average_of_field_entries(playht_latency_records, "response_generation_time")
play_average_header_generation_time = get_average_of_field_entries(playht_latency_records, "header_generation_time")
play_average_first_chunk_generation_time = get_average_of_field_entries(playht_latency_records,
                                                                        "first_chunk_generation_time")

playht_logger.info(f"Average response generation time: {play_average_response_generation_time:.2f}")
playht_logger.info(f"Average header generation time: {play_average_header_generation_time:.2f}")
playht_logger.info(f"Average first chunk generation time: {play_average_first_chunk_generation_time:.2f}")

for i in range(10):
    eleven_logger.info(f"WebSocket Connection {i + 1}")
    latency_data = asyncio.run(ElevenLabsBenchmark.run(synthesis_input=eleven_text_gen(),
                                                       mode=ElevenLabsMode.INPUT_STREAMING,
                                                       logger=eleven_logger)
                               )
    eleven_latency_records.append(latency_data)

eleven_average_stream_generation_time = get_average_of_field_entries(eleven_latency_records, "stream_generation_time")
eleven_average_first_audio_chunk_generation_time = get_average_of_field_entries(eleven_latency_records,
                                                                                "first_audio_chunk_generation_time")

eleven_logger.info(f"Average stream generation time: {eleven_average_stream_generation_time:.2f}")
eleven_logger.info(f"Average first audio chunk generation time: {eleven_average_first_audio_chunk_generation_time:.2f}")

print("\nTesting ended")
