import logging
import os
import time

from openai import AsyncOpenAI, OpenAI

GPT_PROMPT = "Tell me about life in 30 words."
async_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
logger = logging.getLogger("openai_gpt")
logger.setLevel(logging.DEBUG)


async def get_gpt_response_stream_async(logger=logger):
    messages = [
        {"role": "user", "content": GPT_PROMPT},
    ]
    stream = await async_client.chat.completions.create(model="gpt-3.5-turbo", messages=messages, stream=True)
    logger.debug("Received GPT response stream")
    async for chunk in stream:
        if text_chunk := chunk.choices[0].delta.content:
            yield text_chunk


def get_gpt_response_stream(logger=logger):
    messages = [
        {"role": "user", "content": GPT_PROMPT},
    ]
    start = time.time()
    stream = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages, stream=True)
    logger.debug(f"Received GPT response stream in {time.time() - start:.2f}")
    start_time = time.time()
    is_first_chunk = True
    for chunk in stream:
        if text_chunk := chunk.choices[0].delta.content:
            if is_first_chunk:
                logger.debug(f"Received first token in {time.time() - start_time:.2f}")
                is_first_chunk = False
            yield text_chunk
            start_time = time.time()


def get_gpt_response_text(logger=logger):
    messages = [
        {"role": "user", "content": GPT_PROMPT},
    ]
    start = time.time()
    response = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
    logger.debug(f"Received GPT response in {time.time() - start:.2f}")
    return response.choices[0].message.content
