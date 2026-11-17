"""In-memory stand-in for AWS Agent Registry, shared across processes.

Product routers stay stock v1.9.0. Skill records have no Loom row, so
update and approve persist SKILL.md with only registry:write. The store
is a file because the fold helper runs in the poc process and must see
the PUT the server just wrote. Update leaves status DRAFT, matching the
in-tree skill-update test, so the same caller has to approve again
before the fold will read the body.
"""

from __future__ import annotations

import fcntl
import json
import logging
import os
from pathlib import Path
from typing import Any, Callable

from fastapi import HTTPException, Request

logger = logging.getLogger("lab_harness")

_HOOKED = False
_AUTH_PATCHED = False
_REGISTRY_PATCHED = False
_CLIENT: "LabRegistryClient | None" = None

STORE = Path(os.environ.get("LAB_REGISTRY_PATH", "/tmp/loom-190-skill-plant-registry.json"))
LOCK = STORE.with_suffix(".lock")

TOKEN_USERS = {
    "lab-demo": {
        "sub": "lab-demo",
        "username": "lab-demo",
        "groups": ["t-admin", "g-admins-demo"],
    },
}


class LabRegistryClient:
    """File-backed registry. Descriptors stay in the create shape get_record returns."""

    def __init__(self) -> None:
        self.registry_id = "lab-registry"
        self.region = "us-east-1"
        self.control = object()
        self.data = object()

    def _require_registry(self) -> bool:
        return True

    def _txn(self, mutate: Callable[[dict[str, Any]], Any]) -> Any:
        STORE.parent.mkdir(parents=True, exist_ok=True)
        with LOCK.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                data: dict[str, Any] = {"n": 0, "records": {}}
                if STORE.exists() and STORE.stat().st_size:
                    data = json.loads(STORE.read_text(encoding="utf-8"))
                result = mutate(data)
                tmp = STORE.with_suffix(".tmp")
                tmp.write_text(json.dumps(data), encoding="utf-8")
                tmp.replace(STORE)
                return result
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _copy(rec: dict[str, Any] | None) -> dict[str, Any]:
        if not rec:
            return {}
        return json.loads(json.dumps(rec))

    def _blank(
        self,
        record_id: str,
        *,
        name: str,
        record_type: str,
        descriptors: dict[str, Any],
        record_version: str,
        description: str | None,
        status: str,
    ) -> dict[str, Any]:
        return {
            "recordId": record_id,
            "name": name,
            "displayName": name,
            "recordType": record_type,
            "status": status,
            "description": description,
            "descriptors": descriptors,
            "recordVersion": record_version,
            "statusReason": None,
            "createdAt": "2026-01-01T00:00:00Z",
            "updatedAt": "2026-01-01T00:00:00Z",
        }

    def create_record(
        self,
        name: str,
        display_name: str,
        record_type: str,
        descriptors: dict[str, Any],
        record_version: str,
        description: str | None = None,
    ) -> dict[str, Any]:
        def add(data: dict[str, Any]) -> dict[str, Any]:
            data["n"] = int(data.get("n", 0)) + 1
            record_id = f"lab-skill-{data['n']}"
            rec = self._blank(
                record_id,
                name=display_name or name,
                record_type=record_type,
                descriptors=descriptors,
                record_version=record_version,
                description=description,
                status="DRAFT",
            )
            data["records"][record_id] = rec
            logger.info("lab registry create id=%s type=%s", record_id, record_type)
            return self._copy(rec)

        return self._txn(add)

    def get_record(self, record_id: str) -> dict[str, Any]:
        return self._txn(lambda data: self._copy(data["records"].get(record_id)))

    def wait_for_record(self, record_id: str, poll_interval: int = 5) -> dict[str, Any]:
        return self.get_record(record_id)

    def list_records(self) -> dict[str, Any]:
        def read(data: dict[str, Any]) -> dict[str, Any]:
            return {"registryRecords": [self._copy(r) for r in data["records"].values()]}

        return self._txn(read)

    def submit_for_approval(self, record_id: str) -> dict[str, Any]:
        return self.update_record_status(record_id, "PENDING_APPROVAL", "submit")

    def approve_record(self, record_id: str, reason: str = "Approved via Loom") -> dict[str, Any]:
        return self.update_record_status(record_id, "APPROVED", reason)

    def reject_record(self, record_id: str, reason: str) -> dict[str, Any]:
        return self.update_record_status(record_id, "REJECTED", reason)

    def update_record_status(self, record_id: str, status: str, reason: str) -> dict[str, Any]:
        def edit(data: dict[str, Any]) -> dict[str, Any]:
            rec = data["records"].get(record_id)
            if not rec:
                return {}
            rec["status"] = status
            rec["statusReason"] = reason
            return self._copy(rec)

        return self._txn(edit)

    def update_record(
        self,
        record_id: str,
        display_name: str,
        descriptors: dict[str, Any],
        record_version: str,
        description: str | None = None,
    ) -> dict[str, Any]:
        def edit(data: dict[str, Any]) -> dict[str, Any]:
            rec = data["records"].get(record_id)
            if not rec:
                return {}
            rec["displayName"] = display_name
            rec["descriptors"] = descriptors
            rec["recordVersion"] = record_version
            rec["status"] = "DRAFT"
            if description is not None:
                rec["description"] = description
            rec["updatedAt"] = "2026-01-02T00:00:00Z"
            return self._copy(rec)

        return self._txn(edit)

    def delete_record(self, record_id: str) -> dict[str, Any]:
        def remove(data: dict[str, Any]) -> dict[str, Any]:
            data["records"].pop(record_id, None)
            return {}

        return self._txn(remove)

    def search_records(self, query: str, max_results: int = 10) -> dict[str, Any]:
        return {"results": []}

    def get_registry(self) -> dict[str, Any]:
        return {"registryId": self.registry_id}


def lab_get_registry_client() -> LabRegistryClient:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = LabRegistryClient()
    return _CLIENT


def _patch_auth(mod: Any) -> None:
    global _AUTH_PATCHED
    if getattr(mod, "_lab_skill_plant_auth", False) or _AUTH_PATCHED:
        return
    user_info_cls = mod.UserInfo
    derive_scopes = mod.derive_scopes

    def lab_get_current_user(request: Request):
        auth_header = request.headers.get("Authorization", "") or ""
        token = auth_header[7:] if auth_header.startswith("Bearer ") else ""
        spec = TOKEN_USERS.get(token)
        if spec is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        groups = list(spec["groups"])
        return user_info_cls(
            sub=spec["sub"],
            username=spec["username"],
            groups=groups,
            scopes=derive_scopes(groups),
            idp_type="lab",
        )

    mod.get_current_user = lab_get_current_user
    mod._lab_skill_plant_auth = True
    _AUTH_PATCHED = True
    logger.info("lab harness: get_current_user mapped lab-demo")


def _patch_registry(mod: Any) -> None:
    global _REGISTRY_PATCHED
    if getattr(mod, "_lab_skill_plant_client", False) or _REGISTRY_PATCHED:
        return
    client = lab_get_registry_client()
    real = mod.RegistryClient
    client.build_skill_descriptors = real.build_skill_descriptors
    client.build_mcp_descriptors = real.build_mcp_descriptors
    client.build_agent_descriptors = real.build_agent_descriptors
    client.build_a2a_descriptors = real.build_a2a_descriptors
    mod.get_registry_client = lab_get_registry_client
    mod.configure_registry = lambda *args, **kwargs: lab_get_registry_client()
    orig_init = mod.init_registry_from_db

    def lab_init_registry_from_db(db_session) -> None:
        orig_init(db_session)
        mod._client = lab_get_registry_client()

    mod.init_registry_from_db = lab_init_registry_from_db
    mod._client = client
    mod._lab_skill_plant_client = True
    _REGISTRY_PATCHED = True
    logger.info("lab harness: registry client file=%s", STORE)


def _maybe_patch(mod: Any, name: str) -> None:
    mod_name = getattr(mod, "__name__", "") or ""
    if name == "app.dependencies.auth" or mod_name == "app.dependencies.auth":
        _patch_auth(mod)
    if name == "app.services.registry" or mod_name == "app.services.registry":
        _patch_registry(mod)


def install_import_hook() -> None:
    global _HOOKED
    if _HOOKED:
        return
    import builtins

    orig_import = builtins.__import__

    def hooked(name, globals=None, locals=None, fromlist=(), level=0):
        mod = orig_import(name, globals, locals, fromlist, level)
        try:
            _maybe_patch(mod, name)
            if fromlist:
                for item in fromlist:
                    if item == "*":
                        continue
                    sub = getattr(mod, item, None)
                    if sub is not None and hasattr(sub, "__name__"):
                        _maybe_patch(sub, getattr(sub, "__name__", ""))
        except Exception:
            logger.exception("lab harness: import hook failed name=%s", name)
        return mod

    builtins.__import__ = hooked
    _HOOKED = True


def install() -> None:
    install_import_hook()
    import sys

    auth_mod = sys.modules.get("app.dependencies.auth")
    if auth_mod is not None:
        _patch_auth(auth_mod)
    reg_mod = sys.modules.get("app.services.registry")
    if reg_mod is not None:
        _patch_registry(reg_mod)
