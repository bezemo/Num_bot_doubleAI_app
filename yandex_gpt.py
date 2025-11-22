"""
Модуль генерации текста через Yandex GPT API.
Автоматически переключается между yandexgpt и YandexGPT Lite,
добавляет ретраи с экспоненциальной выдержкой и логирует все
неуспешные попытки.
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import List, Optional

import requests

from config import settings

logger = logging.getLogger(__name__)

# ---------- Константы ----------
DEFAULT_TEMPERATURE = 0.6
DEFAULT_MAX_TOKENS = 2_000
MAX_RETRIES = 4  # 1 основной + 3 ретрая
BACKOFF_FACTOR = 1.5  # множитель экспоненциальной выдержки
TIMEOUT = 30  # секунды на один запрос

# Два варианта uri (приоритет – полный, если Lite не указан)
MODELS = {
    "full": f"gpt://{settings.yandex_folder_id}/yandexgpt/latest",
    "lite": f"gpt://{settings.yandex_folder_id}/yandexgpt-lite/latest",
}

# ---------- Служебные функции ----------
def _sleep_attempt(attempt: int) -> None:
    """Экспоненциальная выдержка между ретраями."""
    delay = BACKOFF_FACTOR**attempt
    logger.info("Retry %s/%s after %.1f sec", attempt + 1, MAX_RETRIES, delay)
    time.sleep(delay)


def _make_payload(
    prompt: str, model_uri: str, temperature: float, max_tokens: int
) -> dict:
    """Формирует тело запроса к Yandex GPT."""
    return {
        "modelUri": model_uri,
        "completionOptions": {
            "stream": False,
            "temperature": temperature,
            "maxTokens": max_tokens,
        },
        "messages": [{"role": "user", "text": prompt}],
    }


def _post(
    url: str, headers: dict, payload: dict, timeout: int
) -> Optional[requests.Response]:
    """Выполняет POST-запрос с базовой обработкой исключений."""
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        logger.debug("Yandex GPT HTTP %s", resp.status_code)
        return resp
    except requests.RequestException as exc:
        logger.warning("Request failed: %s", exc)
        return None


def _extract_text(resp: requests.Response) -> Optional[str]:
    """Достаёт текст из успешного ответа."""
    try:
        data = resp.json()
        return data["result"]["alternatives"][0]["message"]["text"]
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        logger.error("Cannot parse response: %s", exc)
        return None


# ---------- Публичная функция ----------
def generate_via_yandex(
    structure: List[str],
    mode: str,
    *,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """
    Генерирует эзотерический отчёт на основе списка строк-фрагментов.
    При неуспехе пробует yandexgpt-lite, затем отдаёт «сырой» текст.
    """
    mode_desc = {
        "default": "краткий эзотерический отчёт",
        "deep": "глубокий нумерологический анализ",
        "master": "полный эзотерический портрет по методике Хшановской",
    }[mode]

    #prompt = (
    #    f"Ты — эзотерический нумеролог. Напиши {mode_desc} на основе данных ниже. "
    #    "Говори мягко, вдохновляюще, наставнически. Не задавай вопросов, "
    #    "не ссылайся на источники, не философствуй. "
    #    "Заверши текст: «Если почувствуешь, что это о тебе — это не совпадение. "
    #    "Всё записано в дате.» "
    #    "«Если ты узнал себя — поставь ⭐ или сохрани расклад.»\n\n"
    #    "Данные:\n" + "\n".join(structure)
    #)

    #prompt = (
    #"Ты — эзотерический нумеролог. Пользователь уже получил структурированный список (см. ниже). "
    #"Напиши **развернутый, вдохновляющий текст-расширение** к каждому пункту, "
    #"не удаляя эмодзи-иконки и не меняя заголовки. "
    #"Добавь по 1-3 предложения под каждым пунктом, сохрани формат «эмодзи + заголовок».\n\n"
    #"Данные:\n" + "\n".join(structure)
    #)

    prompt = (
        f"Ты — эзотерический нумеролог. Напиши {mode_desc} на основе данных ниже. "
        "Говори мягко, вдохновляюще, наставнически. Не задавай вопросов, "
        "не ссылайся на источники, не философствуй. "
        "не удаляя эмодзи-иконки и не меняя заголовки. "
        "Добавь по 1-3 предложения под каждым пунктом, сохрани формат «эмодзи + заголовок».\n\n"
        "Заверши текст: «Если почувствуешь, что это о тебе — это не совпадение. "
        "Всё записано в дате.» "
        "«Если ты узнал себя — поставь ⭐ или сохрани расклад.»\n\n"
        "Данные:\n" + "\n".join(structure)
    )

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {"Authorization": f"Api-Key {settings.yandex_api_key}"}

    # Пробуем модели по порядку
    for model_key, model_uri in MODELS.items():
        logger.info("Trying model %s (%s)", model_key, model_uri)

        for attempt in range(MAX_RETRIES):
            payload = _make_payload(prompt, model_uri, temperature, max_tokens)
            resp = _post(url, headers, payload, TIMEOUT)

            if resp is None:
                _sleep_attempt(attempt)
                continue

            if resp.status_code == 200:
                text = _extract_text(resp)
                if text:
                    logger.info("Successfully generated with %s", model_key)
                    return text
                logger.warning("Empty text in response")
            else:
                logger.warning(
                    "Yandex API error (%s): %s", resp.status_code, resp.text
                )
                _sleep_attempt(attempt)

    # Всё равно не удалось — возвращаем «сырой» текст
    raw = "\n".join(structure)
    logger.error("All Yandex GPT attempts failed, returning raw text")
    return raw + "\n\n(Текст не сгенерирован)"

def generate_fallback_via_yandex(user_text: str) -> str:
    prompt = (
        f"Пользователь написал: '{user_text}'. "
        "Он не ввёл дату рождения в формате ДД.ММ.ГГГГ. "
        "Ответь в стиле дружелюбного собеседника, слегка пошути, мягко подтолкни к тому, "
        "чтобы он ввёл дату рождения. А затем ненавязчиво предложи личную консультацию по созданию таких ботов — "
        "дай контакт: @viv1313r. Не повторяйся, не говори, что ты бот."
    )

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {"Authorization": f"Api-Key {settings.yandex_api_key}"}
    model_uri = f"gpt://{settings.yandex_folder_id}/yandexgpt-lite/latest"

    payload = _make_payload(prompt, model_uri, temperature=0.7, max_tokens=300)
    resp = _post(url, headers, payload, timeout=10)

    if resp and resp.status_code == 200:
        text = _extract_text(resp)
        if text:
            return text

    return "Я пока не понял, давай просто дату рождения в формате ДД.ММ.ГГГГ — и я создам твой портрет. А если хочешь такого же бота — пиши @viv1313r"