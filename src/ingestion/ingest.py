import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from deep_translator import GoogleTranslator
from pypdf import PdfReader

from persistence import save_json
from translation import (
    load_translation_cache,
    save_translation_cache,
    translate_dataframe_texts,
)

# --------------
# CONFIGURAÇÕES

PATIENT_ID = "1d604da9-9a81-4ba9-80c2-de3375d59b40"

# o script está em: src/ingestion/ingest.py, então parents[2] volta para a raiz do projeto
PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "dados_paciente.json"
TRANSLATION_CACHE_FILE = PROCESSED_DIR / "translation_cache.json"


CSV_FILES = {
    "dados_pessoais": RAW_DIR / "patients.csv",
    "consultas": RAW_DIR / "encounters.csv",
    "condicoes": RAW_DIR / "conditions.csv",
    "medicamentos": RAW_DIR / "medications.csv",
    "observacoes": RAW_DIR / "observations.csv",
    "procedimentos": RAW_DIR / "procedures.csv",
}

PDF_FILES = [
    RAW_DIR / "bula_amoxicilina_clavulanato_paciente1.pdf",
]


COLUMNS_TO_REMOVE = {
    "dados_pessoais": [
        "address",
        "ssn",
        "zip",
        "lat",
        "lon",
        "healthcare_expenses",
        "healthcare_coverage",
        "drivers",
        "passport",
        "prefix",
        "suffix",
        "maiden",
        "marital",
        "birthplace",
        "deathdate",
        "marital_status"
    ],
    "consultas": [
        "organization",
        "provider",
        "payer",
        "base_encounter_cost",
        "total_claim_cost",
        "payer_coverage",
    ],
    "medicamentos": [
        "payer",
        "base_cost",
        "payer_coverage",
        "dispenses",
        "totalcost",
    ],
    "procedimentos": [
        "base_cost",
    ],
}

# --------------
# FUNÇÕES AUXILIARES

def normalize_column_name(column_name: str) -> str:
    """Padroniza o nome das colunas para letras minúsculas e snake_case."""
    column_name = column_name.strip().lower()
    column_name = re.sub(r"\s+", "_", column_name)
    column_name = re.sub(r"[^a-z0-9_]", "_", column_name)
    column_name = re.sub(r"_+", "_", column_name)
    return column_name.strip("_")


def clean_text(value: Any, remove_numbers: bool = False) -> Any:
    """Remove espaços extras e caracteres desnecessários de valores textuais dos arquivos CSV."""
    if pd.isna(value):
        return None

    if not isinstance(value, str):
        return value

    value = value.replace("\u00a0", " ")
    value = re.sub(r"\s+", " ", value).strip()

    if remove_numbers:
        value = re.sub(r"\d+", "", value).strip()

    return value or None

def clean_pdf_text(text: str) -> str:
    """Limpa o texto do PDF sem remover informações clínicas importantes."""
    text = text.replace("\x00", " ")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def validate_files() -> None:
    """Verifica se todos os arquivos esperados existem."""
    missing_files = []

    for file_path in CSV_FILES.values():
        if not file_path.exists():
            missing_files.append(str(file_path))

    for pdf_path in PDF_FILES:
        if not pdf_path.exists():
            missing_files.append(str(pdf_path))

    if missing_files:
        raise FileNotFoundError(
            "Os seguintes arquivos não foram encontrados:\n"
            + "\n".join(missing_files)
        )


def read_csv(file_path: Path) -> pd.DataFrame:
    """Lê um CSV e normaliza os nomes das colunas."""
    df = pd.read_csv(file_path)
    df.columns = [normalize_column_name(column) for column in df.columns]
    return df


def filter_patient(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """Filtra os registros mantendo apenas o paciente alvo."""
    id_column = "id" if table_name == "dados_pessoais" else "patient"

    if id_column not in df.columns:
        return df

    return df[df[id_column].astype(str) == PATIENT_ID].copy()


def clean_dataframe(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """Remove colunas desnecessárias e limpa campos textuais."""
    df = df.copy()

    df = df.drop(
        columns=COLUMNS_TO_REMOVE.get(table_name, []),
        errors="ignore",
    )

    text_columns = df.select_dtypes(include="object").columns

    for column in text_columns:
        remove_numbers = column in {"first", "last"}

        df[column] = df[column].apply(
            lambda value: clean_text(value, remove_numbers=remove_numbers)
        )

    df = df.astype(object).where(pd.notnull(df), None)

    return df


def dataframe_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Converte um DataFrame para uma lista de dicionários."""
    df = df.astype(object).where(pd.notnull(df), None)
    return df.to_dict(orient="records")


def extract_pdf_text(pdf_path: Path) -> dict[str, Any]:
    """Extrai o texto da bula em PDF, mantendo separação por página."""
    reader = PdfReader(str(pdf_path))
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        text = clean_pdf_text(raw_text)

        if text:
            pages.append({
                "pagina": page_number,
                "texto": text,
            })

    full_text = "\n\n".join(page["texto"] for page in pages)

    return {
        "arquivo_origem": pdf_path.name,
        "tipo_documento": "bula_medicamento",
        "medicamento": "amoxicilina + clavulanato de potássio",
        "texto_completo": full_text,
        "paginas": pages,
    }

# --------------
# PIPELINE DE INGESTÃO

def load_patient_data() -> dict[str, list[dict[str, Any]]]:
    """Lê, filtra, limpa e traduz campos textuais dos CSVs do paciente."""
    patient_data = {}

    translation_cache = load_translation_cache(TRANSLATION_CACHE_FILE)
    translator = GoogleTranslator(source="en", target="pt")

    for table_name, file_path in CSV_FILES.items():
        df = read_csv(file_path)
        df = filter_patient(df, table_name)
        df = clean_dataframe(df, table_name)

        df = translate_dataframe_texts(
            df=df,
            table_name=table_name,
            translator=translator,
            cache=translation_cache,
        )

        patient_data[table_name] = dataframe_to_records(df)

    save_translation_cache(translation_cache, TRANSLATION_CACHE_FILE)

    return patient_data


def load_bulas() -> list[dict[str, Any]]:
    """Lê apenas a bula relacionada ao paciente alvo."""
    bulas = []

    for pdf_path in PDF_FILES:
        bula = extract_pdf_text(pdf_path)
        bulas.append(bula)

    return bulas


def build_final_json(
    patient_data: dict[str, list[dict[str, Any]]],
    bulas: list[dict[str, Any]],
) -> dict[str, Any]:
    """Monta a estrutura final que será salva em JSON."""
    dados_pessoais = {}

    if patient_data["dados_pessoais"]:
        dados_pessoais = patient_data["dados_pessoais"][0]

        first_name = dados_pessoais.get("first")
        last_name = dados_pessoais.get("last")

        names = []

        if first_name:
            names.append(first_name)

        if last_name:
            names.append(last_name)

        dados_pessoais["nome_completo"] = " ".join(names)

    return {
        "metadata": {
            "patient_id": PATIENT_ID,
            "data_geracao": datetime.now(timezone.utc).isoformat(),
            "fontes": {
                "csv": [file.name for file in CSV_FILES.values()],
                "pdf": [bula["arquivo_origem"] for bula in bulas],
            },
        },
        "dados_pessoais": dados_pessoais,
        "consultas": patient_data["consultas"],
        "condicoes": patient_data["condicoes"],
        "medicamentos": patient_data["medicamentos"],
        "observacoes": patient_data["observacoes"],
        "procedimentos": patient_data["procedimentos"],
        "bulas": bulas,
    }

def main() -> None:
    """Executa a ingestão e salva o JSON final."""
    validate_files()

    patient_data = load_patient_data()
    bulas = load_bulas()

    final_data = build_final_json(patient_data, bulas)

    save_json(final_data, OUTPUT_FILE)

    print(f"Arquivo gerado em: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()