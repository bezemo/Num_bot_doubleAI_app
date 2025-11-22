# deepseek_client.py
import logging
import requests
from typing import List
from config import settings

logger = logging.getLogger(__name__)


def generate_via_deepseek(structure: List[str], mode: str) -> str:
    """
    Генерирует расширенный эзотерический текст через локальный DeepSeek.
    API совместимо с YandexGPT: принимает структуру и режим.
    """
    mode_desc = {
        "default": "краткий эзотерический отчёт",
        "deep": "глубокий нумерологический анализ",
        "master": "полный эзотерический портрет по методике Хшановской",
    }[mode]

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

    try:
        resp = requests.post(
            settings.deepseek_url,
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
                "temperature": 0.7,
            },
            headers={"Content-Type": "application/json"},
            timeout=settings.deepseek_timeout,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        logger.warning("DeepSeek HTTP %s: %s", resp.status_code, resp.text)
    except Exception as e:
        logger.exception("DeepSeek error")
    # fallback
    return "\n".join(structure) + "\n\n(DeepSeek не ответил)"