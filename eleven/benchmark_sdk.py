import logging
import time

import elevenlabs

from eleven.config import (
    ELEVEN_LABS_API_KEY
)

elevenlabs.set_api_key(ELEVEN_LABS_API_KEY)


class ElevenLabsSdkBenchmark:
    logger = logging.getLogger("eleven_labs_sdk_benchmark")
    logger.setLevel(logging.DEBUG)

    @staticmethod
    def run(text_chunk_gen, logger=None):
        if not logger:
            logger = ElevenLabsSdkBenchmark.logger
        stream = elevenlabs.generate(
            text=text_chunk_gen,
            model="eleven_turbo_v2",
            stream=True,
        )
        is_first_chunk = True
        start = time.time()
        for audio_chunk in stream:
            if is_first_chunk:
                logger.info(f"Time for first byte: {time.time() - start}")
                is_first_chunk = False
            logger.debug("Audio data received")
