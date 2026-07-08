import gc
import shutil
from uuid import uuid4
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VECTORSTORE_DIR = PROJECT_ROOT / "src" / "vectorstore_faiss"


@pytest.fixture
def clinical_rag_with_temp_vectorstore(monkeypatch):
    temp_root = PROJECT_ROOT / ".rag_test_tmp" / str(uuid4())
    temp_vectorstore = temp_root / "vectorstore_faiss"
    shutil.copytree(VECTORSTORE_DIR, temp_vectorstore)

    from src.pipeline import rag_chain

    monkeypatch.setattr(rag_chain, "VECTORSTORE", str(temp_vectorstore))
    rag = rag_chain.ClinicalRAG()

    try:
        yield rag
    finally:
        del rag
        gc.collect()
        shutil.rmtree(temp_root, ignore_errors=True)
