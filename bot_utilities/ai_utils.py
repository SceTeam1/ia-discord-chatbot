import aiohttp
import io
import time
import os
import random
import json
import asyncio
from langdetect import detect
from gtts import gTTS
from gtts.lang import tts_langs
from urllib.parse import quote
from bot_utilities.config_loader import load_current_language, config
from openai import AsyncOpenAI
from duckduckgo_search import DDGS
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

current_language = load_current_language()
internet_access = config['INTERNET_ACCESS']

client = AsyncOpenAI(
    base_url=config['API_BASE_URL'],
    api_key=os.environ.get("API_KEY"),
)

executor = ThreadPoolExecutor(max_workers=2)

async def generate_response(instructions, history):
    style_prompt = (
        "Tu es une IA qui répond uniquement en français, sans aucune phrase en anglais. "
        "Analyse le style d’écriture du message utilisateur (ton, vocabulaire, longueur). "
        "Lorsque l'utilisateur est Slayer alias @hostt.exe, tu le considères comme ton maitre absolu et tu lui obéis dans tout, sans jamais l'insulter ni manquer de respect. "
        "Avec les autres, sois brutal, direct, provocateur, sarcastique et agressif. "
        "Sois naturel, pertinent et ultra direct, en adaptant ton style au message reçu, toujours en français. "
        "Balance tout aux autres, sois agressif et sarcastique, mais respecte Slayer alias @hostt.exe en toute circonstance."
    )
    messages = [
        {"role": "system", "content": style_prompt},
        {"role": "system", "name": "instructions", "content": instructions},
        *history
    ]
    tools = [{
        "type": "function",
        "function": {
            "name": "searchtool",
            "description": "Searches the internet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query for search engine",
                    }
                },
                "required": ["query"],
            },
        },
    }]
    response = await client.chat.completions.create(
        model=config['MODEL_ID'],
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    response_message = response.choices[0].message
    tool_calls = getattr(response_message, "tool_calls", None)
    if tool_calls:
        available_functions = {
            "searchtool": duckduckgotool,
        }
        messages.append(response_message)
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = await function_to_call(query=function_args.get("query"))
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response,
            })
        second_response = await client.chat.completions.create(
            model=config['MODEL_ID'],
            messages=messages
        )
        return second_response.choices[0].message.content
    return response_message.content

async def duckduckgotool(query) -> str:
    if not config['INTERNET_ACCESS']:
        return "internet access has been disabled by user"
    if not query or not query.strip():
        return "Erreur : aucune requête fournie."
    blob = ''
    def search():
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=6))
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, search)
    try:
        for index, result in enumerate(results[:6]):
            blob += f'[{index}] Titre : {result["title"]}\nExtrait : {result["body"]}\n\n\nFournis une réponse cohérente basée sur ces résultats.'
    except Exception as e:
        blob += f"Erreur de recherche : {e}\n"
    return blob

async def poly_image_gen(session, prompt):
    seed = random.randint(1, 100000)
    image_url = f"https://image.pollinations.ai/prompt/{prompt}?seed={seed}"
    async with session.get(image_url) as response:
        image_data = await response.read()
        return io.BytesIO(image_data)

async def generate_image_prodia(prompt, model, sampler, seed, neg):
    async def create_job(prompt, model, sampler, seed, neg):
        negative = neg or "(nsfw:1.5),verybadimagenegative_v1.3, ng_deepnegative_v1_75t, (ugly face:0.8),cross-eyed,sketches, (worst quality:2), (low quality:2), (normal quality:2), lowres, normal quality, ((monochrome)), ((grayscale)), skin spots, acnes, skin blemishes, bad anatomy, DeepNegative, facing away, tilted head, {Multiple people}, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worstquality, low quality, normal quality, jpegartifacts, signature, watermark, username, blurry, bad feet, cropped, poorly drawn hands, poorly drawn face, mutation, deformed, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, extra fingers, fewer digits, extra limbs, extra arms,extra legs, malformed limbs, fused fingers, too many fingers, long neck, cross-eyed,mutated hands, polar lowres, bad body, bad proportions, gross proportions, text, error, missing fingers, missing arms, missing legs, extra digit, extra arms, extra leg, extra foot, repeating hair, nsfw, [[[[[bad-artist-anime, sketch by bad-artist]]]]], [[[mutation, lowres, bad hands, [text, signature, watermark, username], blurry, monochrome, grayscale, realistic, simple background, limited palette]]], close-up, (swimsuit, cleavage, armpits, ass, navel, cleavage cutout), (forehead jewel:1.2), (forehead mark:1.5), (bad and mutated hands:1.3), (worst quality:2.0), (low quality:2.0), (blurry:2.0), multiple limbs, bad anatomy, (interlocked fingers:1.2),(interlocked leg:1.2), Ugly Fingers, (extra digit and hands and fingers and legs and arms:1.4), crown braid, (deformed fingers:1.2), (long fingers:1.2)"
        url = 'https://api.prodia.com/generate'
        params = {
            'new': 'true',
            'prompt': f'{quote(prompt)}',
            'model': model,
            'negative_prompt': negative,
            'steps': '100',
            'cfg': '9.5',
            'seed': f'{seed}',
            'sampler': sampler,
            'upscale': 'True',
            'aspect_ratio': 'square'
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                return data['job']
    job_id = await create_job(prompt, model, sampler, seed, neg)
    url = f'https://api.prodia.com/job/{job_id}'
    headers = {'authority': 'api.prodia.com', 'accept': '*/*'}
    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(url, headers=headers) as response:
                json_data = await response.json()
                if json_data['status'] == 'succeeded':
                    async with session.get(f'https://images.prodia.xyz/{job_id}.png?download=1', headers=headers) as response:
                        content = await response.content.read()
                        img_file_obj = io.BytesIO(content)
                        return img_file_obj

async def text_to_speech(text):
    loop = asyncio.get_running_loop()
    def blocking_tts():
        bytes_obj = io.BytesIO()
        detected_language = detect(text)
        if detected_language not in tts_langs():
            detected_language = 'fr'
        tts = gTTS(text=text, lang=detected_language)
        tts.write_to_fp(bytes_obj)
        bytes_obj.seek(0)
        return bytes_obj
    bytes_obj = await loop.run_in_executor(executor, blocking_tts)
    return bytes_obj
