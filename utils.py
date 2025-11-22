import re
from typing import Tuple, Optional

def detect_mode_and_date(text: str) -> Tuple[str, Optional[str]]:
    #mode = "default"
    mode = "master"
    #mode = "deep"
    date_match = re.search(r"(\d{2}\.\d{2}\.\d{4})", text)
    date_str = date_match.group(1) if date_match else None

    if "master_mode = true" in text:
        mode = "master"
    elif "deep_mode = true" in text:
        mode = "deep"

    return mode, date_str