from typing import Dict

def reduce_to_single(n: int) -> int:
    while n > 9 and n not in {11, 22, 33}:
        n = sum(int(d) for d in str(n))
    return n

def calculate(date_str: str) -> Dict:
    d, m, y = map(int, date_str.split('.'))
    total = d + m + y
    life_path_a = reduce_to_single(total)
    life_path_b = reduce_to_single(d + reduce_to_single(m) + reduce_to_single(y))
    life_path = life_path_a if life_path_a == life_path_b else reduce_to_single((life_path_a + life_path_b) // 2)

    return {
        "life_path": life_path,
        "mission": f"Реализация потенциала числа {life_path}",
        "psychomatrix": {"1": d % 10, "2": m % 10, "3": y % 10},
        "day_code": reduce_to_single(d),
        "month_code": reduce_to_single(m),
        "year_code": reduce_to_single(y),
        "karma": reduce_to_single(life_path * 2),
        "archetypal_path": f"Путь {life_path}: Проводник света",
        "hidden_conflicts": f"Конфликт между {life_path} и {10 - life_path % 9 or 9}",
        "inner_cycles": [life_path, reduce_to_single(life_path + 3), reduce_to_single(life_path * 2)],
        "collective_influences": f"Эпоха числа {reduce_to_single(y)}",
        "ascii_pyramid": " 1\n 2 2\n 3 3 3",
        "mantra": f"Я --- {life_path}. Я в потоке.",
        "mandala_prompt": f"mandala with {life_path} petals, golden light, cosmic symbols",
        "driver_portrait": f"Водитель: {life_path}-й тип. Интуиция + действие.",
        "repeats_analysis": f"Число {life_path} повторяется 3 раза в расчёте.",
        "psychic_harmony": "Да",
        "pros_cons": "Плюсы: интуиция. Минусы: импульсивность. Рекомендации: медитация.",
    }