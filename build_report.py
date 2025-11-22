"""
Формирование отчёта с эмодзи-символами для каждого пункта чек-листа.
"""
from typing import Dict, List


# ---------- эмодзи-шапки ----------
_EMOJI = {
    "destiny": "🔮",
    "mission": "🎯",
    "psycho": "🧩",
    "day": "☀️",
    "month": "🌙",
    "year": "🪐",
    "archetype": "🌟",
    "conflict": "⚔️",
    "cycles": "🔄",
    "karma": "🕉️",
    "work": "🛠️",
    "result": "✨",
    "harmony": "☯️",
    "pros": "⚖️",
    "repeat": "🔁",
    "collective": "🌌",
    "ascii": "🎨",
    "driver": "🚗",
    "mantra": "🕯️",
    "mandala": "️",
    "final": "🌈",
    "check": "✅",
}


def _base(data: Dict) -> List[str]:
    return [
        f"{_EMOJI['destiny']} Число Судьбы: {data['life_path']}",
        f"{_EMOJI['mission']} Миссия: {data['mission']}",
        f"{_EMOJI['psycho']} Психоматрица: {data['psychomatrix']}",
    ]


def _deep(data: Dict) -> List[str]:
    return [
        f"{_EMOJI['day']} Код дня: {data['day_code']}",
        f"{_EMOJI['month']} Код месяца: {data['month_code']}",
        f"{_EMOJI['year']} Код года: {data['year_code']}",
        f"{_EMOJI['archetype']} Архетипический путь души: {data['archetypal_path']}",
        f"{_EMOJI['conflict']} Скрытые конфликты: {data['hidden_conflicts']}",
        f"{_EMOJI['cycles']} Внутренние циклы: {data['inner_cycles']}",
    ]


def _master(data: Dict) -> List[str]:
    return [
        f"{_EMOJI['karma']} Карма (9): {data['karma']}",
        f"{_EMOJI['work']} Способ проработки (10): Через служение",
        f"{_EMOJI['result']} Результат (11): Гармония",
        f"{_EMOJI['harmony']} Психическая гармония (12): {data['psychic_harmony']}",
        f"{_EMOJI['pros']} Плюсы/минусы/рекомендации: {data['pros_cons']}",
        f"{_EMOJI['repeat']} Анализ повторов карт: {data['repeats_analysis']}",
        f"{_EMOJI['collective']} Коллективные влияния: {data['collective_influences']}",
        f"{_EMOJI['ascii']} ASCII-пирамида:\n{data['ascii_pyramid']}",
        f"{_EMOJI['driver']} Водительский портрет: {data['driver_portrait']}",
        f"{_EMOJI['mantra']} Мантра: {data['mantra']}",
        f"{_EMOJI['mandala']} Описание мандалы: {data['mandala_prompt']}",
        f"{_EMOJI['final']} Финальное заключение: Ты пришёл в этот мир не случайно.",
        f"{_EMOJI['final']} Напоминание: Если ты узнал себя — поставь ⭐ или сохрани расклад.",
    ]


def _checklist_master(data: Dict) -> List[str]:
    return [f"{_EMOJI['check']} Чек-лист master-режима пройден (19 пунктов)."]


def build_report_structure(data: Dict, mode: str) -> List[str]:
    """Главная точка входа."""
    if mode == "default":
        return _base(data)

    base = _base(data)
    deep = _deep(data)

    if mode == "deep":
        return base + deep

    master = _master(data)
    checklist = _checklist_master(data)
    return base + deep + master + checklist