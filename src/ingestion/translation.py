import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
from deep_translator import GoogleTranslator


COLUMNS_TO_TRANSLATE = {
    "dados_pessoais": ["race", "ethnicity"],
    "consultas": ["description", "reasondescription", "encounterclass"],
    "condicoes": ["description"],
    "medicamentos": ["description", "reasondescription"],
    "observacoes": ["description", "value"],
    "procedimentos": ["description", "reasondescription"],
}


def load_translation_cache(cache_file: Path) -> dict[str, str]:
    if not cache_file.exists():
        return {}

    with cache_file.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_translation_cache(cache: dict[str, str], cache_file: Path) -> None:
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    with cache_file.open("w", encoding="utf-8") as file:
        json.dump(cache, file, ensure_ascii=False, indent=2)


def should_translate(value: Any) -> bool:
    if value is None or pd.isna(value):
        return False

    if not isinstance(value, str):
        return False

    value = value.strip()

    if not value:
        return False

    # evita traduzir números, datas, UUIDs, códigos...
    if re.fullmatch(r"[\d.,/%+\-<> ]+", value):
        return False

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", value):
        return False

    if re.fullmatch(r"[a-f0-9\-]{20,}", value.lower()):
        return False

    if len(value) <= 2:
        return False

    return bool(re.search(r"[A-Za-z]", value))


def translate_text(
    value: Any,
    translator: GoogleTranslator,
    cache: dict[str, str],
) -> Any:
    
    if value is None or pd.isna(value):
        return None
    
    if not should_translate(value):
        return value

    text = str(value).strip()
    cache_key = f"en:pt:{text}"

    if cache_key in cache:
        return cache[cache_key]

    try:
        translated_text = translator.translate(text)
        cache[cache_key] = translated_text
        return translated_text

    except Exception:
        return text


def translate_dataframe_texts(
    df: pd.DataFrame,
    table_name: str,
    translator: GoogleTranslator,
    cache: dict[str, str],
) -> pd.DataFrame:
    """Cria colunas traduzidas sem sobrescrever os dados originais."""
    df = df.copy()

    for column in COLUMNS_TO_TRANSLATE.get(table_name, []):
        if column not in df.columns:
            continue

        translated_column = f"{column}_pt"

        df[translated_column] = df[column].apply(
            lambda value: translate_text(value, translator, cache)
        )

    df = df.astype(object).where(pd.notnull(df), None)

    return df