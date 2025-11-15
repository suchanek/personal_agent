"""
Non-destructive integration test for user identity refactor.

This script:
- Forces isolation via temporary directories
- Sets PERSAG_HOME and PERSAG_ROOT to temp locations
- Exercises user_id_mgr single source of truth APIs
- Exercises PersagManager initialization and validation against temp dirs
- Exercises UserRegistry using temp storage paths

It does NOT modify any real ~/.persag state or project files.
"""

import os
import sys
import json
import tempfile
from pathlib import Path


def _add_src_to_syspath():
    # Ensure 'personal_agent' package is importable in src/ layout
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))


def _read_userid_file(userid_path: Path) -> str:
    if not userid_path.exists():
        return ""
    content = userid_path.read_text(encoding="utf-8").strip()
    if content.startswith("USER_ID="):
        return content.split("=", 1)[1].strip().strip("'\"")
    return ""


def main():
    print("TEST: Starting non-destructive user identity integration test")
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        persag_home = base / "persag_home"
        persag_root = base / "persag_root"
        project_root = base / "fake_project"

        # Ensure isolated roots exist
        persag_root.mkdir(parents=True, exist_ok=True)
        project_root.mkdir(parents=True, exist_ok=True)

        # Set environment for isolation BEFORE importing settings or modules that depend on it
        os.environ["PERSAG_HOME"] = str(persag_home)
        os.environ["PERSAG_ROOT"] = str(persag_root)
        os.environ["STORAGE_BACKEND"] = "agno_test"
        os.environ["SHOW_SPLASH_SCREEN"] = "false"

        _add_src_to_syspath()

        # Import centralized user identity utilities
        from personal_agent.config.user_id_mgr import (
            load_user_from_file,
            get_userid,
            get_current_user_id,
            get_user_storage_paths,
            refresh_user_dependent_settings,
        )

        # Import settings AFTER env vars are set to ensure it initializes under temp dirs
        from personal_agent.config import settings

        # 1) Load user config; creates env.userid and default dirs under PERSAG_HOME
        uid1 = load_user_from_file()
        print(f"TEST: load_user_from_file -> USER_ID={uid1!r}")

        assert uid1 == os.getenv("USER_ID"), "USER_ID env not set by load_user_from_file"
        assert Path(os.environ["PERSAG_HOME"]).exists(), "PERSAG_HOME not created"
        userid_path = Path(os.environ["PERSAG_HOME"]) / "env.userid"
        assert userid_path.exists(), "env.userid not created"
        assert _read_userid_file(userid_path) == uid1, "env.userid content mismatch"

        # 2) Verify settings bound to the same PERSAG_HOME
        assert settings.PERSAG_HOME == os.environ["PERSAG_HOME"], "settings.PERSAG_HOME mismatch"
        print(f"TEST: settings.PERSAG_HOME={settings.PERSAG_HOME}")

        # 3) Verify user storage paths for current user
        paths_1 = get_user_storage_paths()
        print("TEST: user storage paths for current user:")
        for k, v in paths_1.items():
            print(f"  - {k}: {v}")
        # Ensure they resolve under our isolated PERSAG_ROOT backend/user hierarchy
        assert os.environ["STORAGE_BACKEND"] in paths_1["AGNO_STORAGE_DIR"], "storage backend missing in paths"
        assert uid1 in paths_1["AGNO_STORAGE_DIR"], "user id missing in storage dir path"

        # 4) Exercise PersagManager initialization/migration/validation (isolated)
        from personal_agent.core.persag_manager import PersagManager

        # Prepare fake project docker directories for migration test
        (project_root / "lightrag_server").mkdir(parents=True, exist_ok=True)
        (project_root / "lightrag_memory_server").mkdir(parents=True, exist_ok=True)
        # Minimal required files referenced by validator
        (project_root / "lightrag_server" / "env.server").write_text("DUMMY=1\n", encoding="utf-8")
        (project_root / "lightrag_server" / "docker-compose.yml").write_text("version: '3'\n", encoding="utf-8")
        (project_root / "lightrag_memory_server" / "env.memory_server").write_text("DUMMY=1\n", encoding="utf-8")
        (project_root / "lightrag_memory_server" / "docker-compose.yml").write_text("version: '3'\n", encoding="utf-8")

        pm = PersagManager()
        ok, msg = pm.initialize_persag_directory(project_root=project_root)
        print(f"TEST: PersagManager.initialize_persag_directory -> {ok}, {msg}")
        assert ok, f"PersagManager initialization failed: {msg}"

        # Defer validation until a non-default USER_ID is set

        # 5) Switch user id non-destructively within temp PERSAG_HOME
        new_uid = "test_user_123"
        assert pm.set_userid(new_uid), "Failed to set new USER_ID via PersagManager"
        # get_userid() dynamically reads filesystem
        current_uid = get_userid()
        print(f"TEST: After set_userid -> get_userid()={current_uid!r}")
        assert current_uid == new_uid, "get_userid() did not reflect new id"

        # Now validate persag structure with non-default USER_ID
        valid, vmsg = pm.validate_persag_structure()
        print(f"TEST: PersagManager.validate_persag_structure -> {valid}, {vmsg}")
        assert valid, f"Persag structure invalid after user switch: {vmsg}"

        # Compute paths for new user (without mutating global settings)
        paths_2 = get_user_storage_paths()
        print("TEST: user storage paths for switched user:")
        for k, v in paths_2.items():
            print(f"  - {k}: {v}")
        assert new_uid in paths_2["AGNO_STORAGE_DIR"], "paths not recalculated for new user"

        # Optionally verify refresh_user_dependent_settings return values for new user
        refreshed = refresh_user_dependent_settings(new_uid)
        assert refreshed["USER_ID"] == new_uid, "refresh_user_dependent_settings did not echo new user id"
        assert new_uid in refreshed["AGNO_STORAGE_DIR"], "refreshed paths missing new user id"

        # 6) UserRegistry should operate entirely within isolated DATA_DIR/storage backend
        from personal_agent.core.user_registry import UserRegistry

        # Use dynamically computed data dir from user_id_mgr to avoid relying on module-level constants
        data_dir_for_registry = paths_2["DATA_DIR"]
        storage_backend = os.environ["STORAGE_BACKEND"]
        ur = UserRegistry(data_dir=data_dir_for_registry, storage_backend=storage_backend)

        ensured = ur.ensure_current_user_registered()
        print(f"TEST: UserRegistry.ensure_current_user_registered -> {ensured}")
        current_user = ur.get_current_user()
        print(f"TEST: UserRegistry.get_current_user -> {current_user}")
        assert current_user is not None, "Current user not found in registry after ensure"
        assert current_user["user_id"] == new_uid, "Registry current user id mismatch"

        # Registry file is under temp paths only
        registry_path = Path(data_dir_for_registry) / storage_backend / "users_registry.json"
        print(f"TEST: Registry path -> {registry_path}")
        assert registry_path.exists(), "Registry file not created in temp location"
        reg_json = json.loads(registry_path.read_text(encoding="utf-8"))
        assert any(u.get("user_id") == new_uid for u in reg_json.get("users", [])), \
            "Registry JSON missing new user"

        print("TEST: Completed successfully (non-destructive).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())