import logging
import os
import time
from enum import Enum
from typing import Optional, Iterable

from pydantic import BaseModel
from pyht import Client, TTSOptions
from pyht.protos import api_pb2


class PlayHTMode(Enum):
    STREAMING = "play_ht_streaming"
    INPUT_STREAMING = "play_ht_input_streaming"


class LatencyData(BaseModel):
    mode: PlayHTMode
    response_generation_time: Optional[float] = None
    header_generation_time: Optional[float] = None
    first_chunk_generation_time: Optional[float] = None


class PlayHTSDKBenchmark:
    logger = logging.getLogger("playht_sdk_benchmark")
    logger.setLevel(logging.DEBUG)
    client = Client(
        user_id=os.environ.get("PLAY_HT_USER_ID"),
        api_key=os.environ.get("PLAY_HT_API_KEY"),
    )
    options = TTSOptions(
        format=api_pb2.FORMAT_MP3,
        quality="faster",
        voice="s3://voice-cloning-zero-shot/801a663f-efd0-4254-98d0-5c175514c3e8/jennifer/manifest.json",
    )

    @staticmethod
    def _write_audio_chunks_to_file(stream: Iterable, latency_data: LatencyData, logger):
        with open("playht_sdk_benchmark.mp3", "wb") as f:
            is_first_chunk = True
            start_time = time.time()
            for audio_chunk in stream:
                if is_first_chunk:
                    first_chunk_generation_time = time.time() - start_time
                    logger.debug(f"First chunk generation time: {time.time() - start_time:.2f}")
                    latency_data.first_chunk_generation_time = first_chunk_generation_time
                    is_first_chunk = False
                f.write(audio_chunk)
        logger.info("Audio chunks written to file")

    @staticmethod
    def _create_speech(text: str, latency_data: LatencyData, logger):
        response_start_time = time.time()
        response = PlayHTSDKBenchmark.client.tts(text=text, options=PlayHTSDKBenchmark.options)
        response_end_time = time.time()
        response_generation_time = response_end_time - response_start_time
        logger.debug(f"Response generation time: {response_generation_time:.2f}")
        latency_data.response_generation_time = response_generation_time

        header_start_time = time.time()
        header = next(response)
        header_end_time = time.time()
        header_generation_time = header_end_time - header_start_time
        logger.debug(f"Header generation time: {header_generation_time:.2f}")
        latency_data.header_generation_time = header_generation_time

        PlayHTSDKBenchmark._write_audio_chunks_to_file(stream=response, latency_data=latency_data, logger=logger)

    @staticmethod
    def _create_live_speech(text_stream: Iterable, latency_data: LatencyData, logger):
        response_start_time = time.time()
        response = PlayHTSDKBenchmark.client.stream_tts_input(text_stream=text_stream,
                                                              options=PlayHTSDKBenchmark.options)
        response_end_time = time.time()
        response_generation_time = response_end_time - response_start_time
        logger.debug(f"Response generation time: {response_generation_time:.2f}")
        latency_data.response_generation_time = response_generation_time

        header_start_time = time.time()
        header = next(response)
        header_end_time = time.time()
        header_generation_time = header_end_time - header_start_time
        logger.debug(f"Header generation time: {header_generation_time:.2f}")
        latency_data.header_generation_time = header_generation_time

        PlayHTSDKBenchmark._write_audio_chunks_to_file(stream=response, latency_data=latency_data, logger=logger)

    @staticmethod
    def run(synthesis_input, mode=PlayHTMode.STREAMING, logger=None):
        if not logger:
            logger = PlayHTSDKBenchmark.logger
        latency_data = LatencyData(mode=mode)
        if mode == PlayHTMode.STREAMING:
            PlayHTSDKBenchmark._create_speech(text=synthesis_input, latency_data=latency_data, logger=logger)
        else:
            PlayHTSDKBenchmark._create_live_speech(text_stream=synthesis_input, latency_data=latency_data,
                                                   logger=logger)
        return latency_data
