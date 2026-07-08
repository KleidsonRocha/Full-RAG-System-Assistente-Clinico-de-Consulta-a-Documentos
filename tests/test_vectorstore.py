from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VECTORSTORE_DIR = PROJECT_ROOT / "src" / "vectorstore_faiss"
FAISS_INDEX_PATH = VECTORSTORE_DIR / "index.faiss"
FAISS_METADATA_PATH = VECTORSTORE_DIR / "index.pkl"


def test_vectorstore_directory_has_persisted_files():
    assert VECTORSTORE_DIR.exists()
    assert VECTORSTORE_DIR.is_dir()
    assert any(VECTORSTORE_DIR.iterdir())
    assert FAISS_INDEX_PATH.exists()
    assert FAISS_METADATA_PATH.exists()


def test_faiss_vectorstore_files_are_not_empty():
    assert FAISS_INDEX_PATH.stat().st_size > 0
    assert FAISS_METADATA_PATH.stat().st_size > 0
