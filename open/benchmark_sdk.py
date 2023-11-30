import logging
import os
import time

from openai import OpenAI


class SynthesisResult:

    def __init__(self, response, stream_generation_time, first_chunk_generation_time=None):
        self.response = response
        self.stream_generation_time = stream_generation_time
        self.first_chunk_generation_time = first_chunk_generation_time


class OpenAISDKBenchmark:
    logger = logging.getLogger("openai_sdk_benchmark")
    logger.setLevel(logging.DEBUG)
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    @staticmethod
    def _create_speech(text, logger):
        start_time = time.time()
        response = OpenAISDKBenchmark.client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
        )
        end_time = time.time()
        stream_generation_time = end_time - start_time

        logger.debug(f"Stream generation time: {stream_generation_time:.2f}")

        return SynthesisResult(response, stream_generation_time)

    @staticmethod
    def run(text, logger=None):
        if not logger:
            logger = OpenAISDKBenchmark.logger

        synthesis_result = OpenAISDKBenchmark._create_speech(text=text, logger=logger)
        with open("openai_benchmark_output.mp3", "wb") as f:
            is_first_chunk = True
            first_chunk_generation_start = time.time()
            for data in synthesis_result.response.iter_bytes():
                if is_first_chunk:
                    first_chunk_generation_end = time.time()
                    first_chunk_generation_time = first_chunk_generation_end - first_chunk_generation_start
                    synthesis_result.first_chunk_generation_time = first_chunk_generation_time
                    is_first_chunk = False
                    logger.debug(f"First chunk generation time: {first_chunk_generation_time:.2f}")
                f.write(data)

        logger.info(f"Audio chunks written to file")

        return synthesis_result
