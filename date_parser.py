# date_parser.py  (natasha + цифровые regex + dateparser/dateutil)
from __future__ import annotations
import re
from datetime import datetime
from dateutil.parser import parse as du_parse, ParserError
from dateparser import parse as dparse
from natasha import DatesExtractor, MorphVocab
from typing import List, Set

morph = MorphVocab()
extractor = DatesExtractor(morph)

# ---------- цифровые паттерны ----------
NUM_RX = re.compile(
    r'\b(?:0?[1-9]|[12]\d|3[01])[./\-](?:0?[1-9]|1[0-2])[./\-](?:\d{2}|\d{4})\b|\b(?:\d{4})[./\-](?:0?[1-9]|1[0-2])[./\-](?:0?[1-9]|[12]\d|3[01])\b'
)

# ---------- словесные дни/месяцы ----------
WORD_DAY = {
    'первое': 1, 'второе': 2, 'третье': 3, 'четвёртое': 4, 'пятое': 5,
    'шестое': 6, 'седьмое': 7, 'восьмое': 8, 'девятое': 9, 'десятое': 10,
    'одиннадцатое': 11, 'двенадцатое': 12, 'тринадцатое': 13, 'четырнадцатое': 14,
    'пятнадцатое': 15, 'шестнадцатое': 16, 'семнадцатое': 17, 'восемнадцатое': 18,
    'девятнадцатое': 19, 'двадцатое': 20, 'двадцать первое': 21, 'двадцать второе': 22,
    'двадцать третье': 23, 'двадцать четвёртое': 24, 'двадцать пятое': 25,
    'двадцать шестое': 26, 'двадцать седьмое': 27, 'двадцать восьмое': 28,
    'двадцать девятое': 29, 'тридцатое': 30, 'тридцать первое': 31
}

WORD_MONTH = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
    'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
}

# ---------- строгий паттерн «день_слово месяц_слово год_цифра» ----------
STRICT_WORD_RX = re.compile(
    r'\b(' + '|'.join(WORD_DAY) + r')\s+(' + '|'.join(WORD_MONTH) + r')\s+(\d{4})\b',
    flags=re.I
)


def _strict_word(text: str) -> Set[str]:
    """Только полные словесные даты (без фантазий)."""
    dates = set()
    for m in STRICT_WORD_RX.finditer(text):
        day = WORD_DAY[m.group(1).lower()]
        month = WORD_MONTH[m.group(2).lower()]
        year = int(m.group(3))
        try:
            dt = datetime(year=year, month=month, day=day)
            dates.add(f"{dt.day:02d}.{dt.month:02d}.{dt.year}")
        except ValueError:
            continue
    return dates


def _from_natasha(text: str) -> Set[str]:
    """Natasha: первое мая двухтысячного и т.д."""
    dates = set()
    for match in extractor(text):
        d = match.fact
        if d.day and d.month and d.year:          # строго полная дата
            try:
                dt = datetime(year=d.year, month=d.month, day=d.day)
                dates.add(f"{dt.day:02d}.{dt.month:02d}.{dt.year}")
            except ValueError:
                continue
    return dates


def _numeric(text: str) -> Set[str]:
    """Цифровые паттерны через dateparser (без фантазий)."""
    dates = set()
    for m in NUM_RX.finditer(text):
        dt = dparse(m.group(0), settings={'DATE_ORDER': 'DMY', 'STRICT_PARSING': True})
        if dt:
            dates.add(f"{dt.day:02d}.{dt.month:02d}.{dt.year}")
    return dates


def find_dates(text: str) -> List[str]:
    """Итог: только полные даты (день+месяц+год)."""
    dates = set()
    dates.update(_strict_word(text))
    dates.update(_from_natasha(text))
    dates.update(_numeric(text))
    return sorted(dates)