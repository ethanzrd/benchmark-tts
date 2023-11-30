# TTS services supporting input streaming: PlayHT, ElevenLabs & OpenAI

import asyncio
import logging
from typing import List

from eleven.benchmark_api import (
    ElevenLabsBenchmark,
    ElevenLabsMode,
    StreamingLatencyData,
)
from open.benchmark_sdk import (
    OpenAISDKBenchmark,
    SynthesisResult,
)
from play.benchmark_sdk import (
    PlayHTSDKBenchmark,
    PlayHTMode,
    LatencyData,
)
from utils import get_average_of_field_entries

logging.basicConfig()
playht_logger = logging.getLogger("streaming_playht")
eleven_logger = logging.getLogger("streaming_11labs")
openai_logger = logging.getLogger("streaming_openai")

playht_logger.setLevel(logging.DEBUG)
eleven_logger.setLevel(logging.DEBUG)
openai_logger.setLevel(logging.DEBUG)

TEXT = "Hello sir, what can I do for you?"

eleven_latency_records: List[StreamingLatencyData] = []
playht_latency_records: List[LatencyData] = []
openai_results: List[SynthesisResult] = []

for i in range(10):
    playht_logger.info(f"SDK API Call {i + 1}")
    latency_data = PlayHTSDKBenchmark.run(synthesis_input=TEXT,
                                          mode=PlayHTMode.STREAMING,
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
    eleven_logger.info(f"API Call {i + 1}")
    latency_data = asyncio.run(ElevenLabsBenchmark.run(
        synthesis_input=TEXT,
        mode=ElevenLabsMode.STREAMING,
        logger=eleven_logger,
    ))
    eleven_latency_records.append(latency_data)

eleven_average_stream_generation_time = get_average_of_field_entries(eleven_latency_records, "stream_generation_time")
eleven_average_first_chunk_generation_time = get_average_of_field_entries(eleven_latency_records,
                                                                          "first_chunk_generation_time")

eleven_logger.info(f"Average stream generation time: {eleven_average_stream_generation_time}")
eleven_logger.info(f"Average first chunk generation time: {eleven_average_first_chunk_generation_time}")

for i in range(10):
    openai_logger.info(f"SDK API Call {i + 1}")
    result = OpenAISDKBenchmark.run(text=TEXT, logger=openai_logger)
    openai_results.append(result)

openai_average_stream_generation_time = get_average_of_field_entries(openai_results, "stream_generation_time")
openai_average_first_chunk_generation_time = get_average_of_field_entries(openai_results, "first_chunk_generation_time")

openai_logger.info(f"Average stream generation time: {openai_average_stream_generation_time}")
openai_logger.info(f"Average first chunk generation time: {openai_average_first_chunk_generation_time}")
