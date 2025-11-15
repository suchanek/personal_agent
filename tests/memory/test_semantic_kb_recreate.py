#!/usr/bin/env python3
"""
Test script to validate semantic KB recreate behavior after ingestion.

Goals:
- Verify single semantic ingestions (text/file) trigger an immediate recreate.
- Verify batch semantic ingestion triggers exactly one recreate at the end.
- Work with real CombinedKnowledgeBase when available; otherwise, fall back to a dummy KB
  so the test remains runnable without Ollama.

Notes:
- Real CombinedKnowledgeBase requires Ollama running (for embeddings).
- When Ollama is not available, we wrap a Dummy KB that counts reloads and allows us
  to validate that KnowledgeTools invokes knowledge_base.load(recreate=True) as expected.

Run:
- As a simple script:
    python tests/test_semantic_kb_recreate.py

- With pytest (optional):
    pytest -s tests/test_semantic_kb_recreate.py
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Optional

# Ensure project src is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from personal_agent.config import settings
from personal_agent.core.agno_storage import (
    create_agno_storage,
    create_combined_knowledge_base,
)
from personal_agent.core.knowledge_manager import KnowledgeManager
from personal_agent.tools.knowledge_tools import KnowledgeTools


class DummyKnowledgeBase:
    """
    Minimal knowledge base stand-in with a load(recreate=True) method,
    used when real CombinedKnowledgeBase cannot be created or loaded.
    """

    def __init__(self, name: str = "DummyKB"):
        self.name = name
        self.reload_count = 0

    def load(self, recreate: bool = False):
        # Count reloads irrespective of the flag value; the code always calls with recreate=True
        self.reload_count += 1

    # Optional: provide a no-op search stub for compatibility
    def search(self, query: str, num_documents: int = 5):
        return []


class KBProxy:
    """
    Proxy that wraps a real knowledge base to count calls to load().
    """

    def __init__(self, kb):
        self._kb = kb
        self.reload_count = 0

    def load(self, recreate: bool = False):
        self.reload_count += 1
        return self._kb.load(recreate=recreate)

    def __getattr__(self, name):
        # Delegate everything else to the wrapped KB
        return getattr(self._kb, name)


def try_create_real_kb() -> Optional[KBProxy]:
    """
    Attempt to create a real CombinedKnowledgeBase and wrap it in KBProxy.
    Returns None if creation fails.
    """
    try:
        # Ensure storage exists (create_agno_storage is side-effectful and safe)
        create_agno_storage()

        kb = create_combined_knowledge_base(
            storage_dir=settings.AGNO_STORAGE_DIR,  # Use configured paths if available
            knowledge_dir=str(Path(settings.DATA_DIR) / "knowledge"),
        )
        if kb is None:
            print("ℹ️ No local knowledge sources found; proceeding without real KB.")
            return None
        # Wrap in proxy to measure reload calls
        proxy = KBProxy(kb)
        return proxy
    except Exception as e:
        print(f"⚠️ Could not create real CombinedKnowledgeBase: {e}")
        return None


def print_env():
    print("Environment")
    print("-----------")
    print(f"USER: test_user (as requested)")
    print(f"DATA_DIR: {settings.DATA_DIR}")
    print(f"AGNO_STORAGE_DIR: {settings.AGNO_STORAGE_DIR}")
    print(f"Semantic knowledge dir: {Path(settings.AGNO_STORAGE_DIR)} / 'knowledge'")
    print(f"LightRAG URL: {settings.LIGHTRAG_URL}")
    print(f"Ollama URL: {settings.OLLAMA_URL}")
    print()


def make_temp_text_file(dir_path: Path, name: str, content: str) -> Path:
    path = dir_path / name
    path.write_text(content, encoding="utf-8")
    return path


def run_test():
    print("🧪 Semantic KB Recreate Behavior Test")
    print("====================================\n")
    print_env()

    # Prepare KnowledgeManager and KnowledgeTools
    km = KnowledgeManager(
        user_id="test_user",
        knowledge_dir=settings.AGNO_KNOWLEDGE_DIR,
        lightrag_url=settings.LIGHTRAG_URL,
    )

    # Attempt to create a real KB; fallback to dummy if not possible
    agno_kb = try_create_real_kb()
    using_real_kb = agno_kb is not None
    if not using_real_kb:
        agno_kb = DummyKnowledgeBase()
        print("🧰 Using DummyKnowledgeBase fallback (reload counting only).")
        print("   Tip: Start Ollama to test against the real KB.\n")
    else:
        print(
            "✅ Using real CombinedKnowledgeBase (reloads will be counted via proxy).\n"
        )

    tools = KnowledgeTools(km, agno_knowledge=agno_kb)

    def get_reload_count():
        return getattr(agno_kb, "reload_count", 0)

    # Baseline
    baseline_reload_count = get_reload_count()
    print(f"Baseline reload count: {baseline_reload_count}")

    # 1) Single ingestion: text -> should trigger immediate recreate
    print("\n1) Single semantic text ingestion (expect +1 reload)")
    text_result = tools.ingest_semantic_text(
        content="This is a single-ingestion test document for semantic KB recreate.",
        title="single_ingestion_test",
        file_type="txt",
        # default defer_reload=False triggers immediate recreate
    )
    print(f"   Result: {text_result}")
    after_single_reload = get_reload_count()
    print(f"   Reload count after single ingestion: {after_single_reload}")

    # 2) Batch ingestion: stage multiple files -> expect exactly +1 reload at end
    print("\n2) Batch semantic directory ingestion (expect +1 reload total for batch)")
    with tempfile.TemporaryDirectory(prefix="semantic_kb_batch_") as tmpdir:
        tmpdir_path = Path(tmpdir)
        make_temp_text_file(tmpdir_path, "batch1.txt", "Batch file 1 content.")
        make_temp_text_file(tmpdir_path, "batch2.txt", "Batch file 2 content.")

        batch_result = tools.batch_ingest_semantic_directory(
            directory_path=str(tmpdir_path),
            file_pattern="*.txt",
            recursive=False,
        )
        print(f"   Batch result:\n{batch_result}")

    after_batch_reload = get_reload_count()
    print(f"   Reload count after batch ingestion: {after_batch_reload}")

    # 3) Single ingestion: file -> should trigger immediate recreate
    print("\n3) Single semantic file ingestion (expect +1 reload)")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmpfile:
        tmpfile.write("A separate single-file ingestion to verify immediate recreate.")
        temp_file_path = tmpfile.name
    try:
        file_result = tools.ingest_semantic_file(
            file_path=temp_file_path,
            title="single_file_ingestion_test",
            # default defer_reload=False triggers immediate recreate
        )
        print(f"   Result: {file_result}")
    finally:
        try:
            os.unlink(temp_file_path)
        except OSError:
            pass

    after_file_reload = get_reload_count()
    print(f"   Reload count after single file ingestion: {after_file_reload}")

    # Summary and simple checks
    print("\nSummary")
    print("-------")
    expected_single_delta = 1
    expected_batch_delta = 1
    expected_file_delta = 1

    single_delta = after_single_reload - baseline_reload_count
    batch_delta = after_batch_reload - after_single_reload
    file_delta = after_file_reload - after_batch_reload

    print(
        f"Expected reload deltas: single={expected_single_delta}, batch={expected_batch_delta}, file={expected_file_delta}"
    )
    print(
        f"Observed reload deltas: single={single_delta}, batch={batch_delta}, file={file_delta}"
    )

    # Provide guidance if using real KB and a step failed (likely due to Ollama)
    if using_real_kb:
        any_error = (
            (isinstance(text_result, str) and text_result.startswith("❌"))
            or (isinstance(batch_result, str) and "❌" in batch_result)
            or (isinstance(file_result, str) and file_result.startswith("❌"))
        )
        if any_error:
            print("\n⚠️ One or more operations failed against the real KB.")
            print(
                "   This often indicates Ollama isn't running or the embedder/model isn't available."
            )
            print(
                "   Start Ollama and the required embedding model, then re-run this test."
            )
            print(
                "   Falling back to DummyKnowledgeBase can validate reload call logic only."
            )

    # PASS/FAIL style hints (non-fatal)
    print("\nValidation")
    print("----------")
    ok_single = single_delta == expected_single_delta
    ok_batch = batch_delta == expected_batch_delta
    ok_file = file_delta == expected_file_delta

    print(f"Single ingestion recreate: {'✅ PASS' if ok_single else '❌ FAIL'}")
    print(f"Batch ingestion single recreate: {'✅ PASS' if ok_batch else '❌ FAIL'}")
    print(f"Single file ingestion recreate: {'✅ PASS' if ok_file else '❌ FAIL'}")

    print("\n✅ Test run complete. Review the outputs above for details.")


if __name__ == "__main__":
    try:
        run_test()
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
