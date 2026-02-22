import os
import re
import json
import hashlib
from collections import defaultdict
from core.mod.manifest_utils import extract_nexus_url
# =========================
#  用于扫描Mods下mod列表供sync等使用
# =========================
class ModScanner:
    def __init__(self, mods_root: str, debug: bool = True, bootstrap: bool = False):
        self.path = os.path.abspath(mods_root)
        self.debug = debug
        self.bootstrap = bootstrap

    def _is_category_folder(self, name: str) -> bool:
        return bool(re.match(r"^\d{2}_.+$", name))

    @staticmethod
    def sanitize_manifest(text: str) -> str:
        lines = text.splitlines()
        lines = [line for line in lines if not line.strip().startswith("//")]
        text = "\n".join(lines)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        text = re.sub(r',\s*([}\]])', r'\1', text)
        return text

    @staticmethod
    def fallback_uid(path: str) -> str:
        return f"broken::{hashlib.sha1(os.path.basename(path).encode()).hexdigest()[:12]}"

    def _find_manifests(self, mod_root: str):
        manifests = []
        for dirpath, _, filenames in os.walk(mod_root):
            for fn in filenames:
                if fn.lower() == "manifest.json":
                    manifests.append(os.path.join(dirpath, fn))
        return manifests

    def _load_manifest(self, manifest_path: str):
        raw = None
        for encoding in ("utf-8-sig", "utf-8", "gbk", "ansi"):
            try:
                with open(manifest_path, "r", encoding=encoding, errors="strict") as f:
                    raw = f.read()
                    fixed = self.sanitize_manifest(raw)
                    return json.loads(fixed)
            except UnicodeDecodeError:
                continue
            except Exception as e:
                if self.debug:
                    print(f"[SCANNER] manifest parse failed: {manifest_path}")
                    if raw:
                        print(f"  ➤ 原始内容:\n{raw[:300]}...")
                    print(f"  ➤ 错误信息: {e}")
                return None

        if self.debug:
            print(f"[SCANNER] manifest 编码无法识别: {manifest_path}")
        return None

    def _pick_primary_path(self, paths):
        def score(p):
            base = os.path.basename(p)
            has_copy_suffix = " (1)" in base or "（1）" in base
            return (has_copy_suffix, len(p), p.lower())
        return sorted(paths, key=score)[0]

    @staticmethod
    def get_case_insensitive(d: dict, key: str):
        for k in d:
            if k.lower() == key.lower():
                return d[k]
        return None

    def _build_record(self, uid: str, entry: str, entry_path: str, manifests, parsed):
        if not parsed:
            record = {
                "unique_id": uid,
                "name": entry,
                "version": "Unknown",
                "author": "Unknown",
                "description": "",
                "folder_path": entry_path,
                "manifest_count": len(manifests),
                "is_modpack": len(manifests) > 1,
                "status": "enabled",
                "source_url": "",
                "image_url": "",
            }
            if self.bootstrap:
                record["category"] = "默认"
                record["category_order"] = 1
                record["mod_order"] = 9999
            return record

        first_mp, first_data = parsed[0]
        uid = self.get_case_insensitive(first_data, "UniqueID") or uid

        record = {
            "unique_id": uid,
            "name": self.get_case_insensitive(first_data, "Name") or entry,
            "version": self.get_case_insensitive(first_data, "Version") or "Unknown",
            "author": self.get_case_insensitive(first_data, "Author") or "Unknown",
            "description": self.get_case_insensitive(first_data, "Description") or "",
            "folder_path": entry_path,
            "manifest_count": len(manifests),
            "is_modpack": len(manifests) > 1,
            "status": "enabled",
            "source_url": extract_nexus_url(first_data) if 'extract_nexus_url' in globals() else "",
            "image_url": "",
        }

        if self.bootstrap:
            record["category"] = "默认"
            record["category_order"] = 1
            record["mod_order"] = 9999

        return record

    def _scan_candidate_root(self, entry: str, entry_path: str, uid_to_paths, uid_to_record_candidates):
        manifests = self._find_manifests(entry_path)
        if not manifests:
            if self.debug:
                print(f"[SCANNER] skip (no manifest found): {entry_path}")
            return

        parsed = []
        for mp in manifests:
            data = self._load_manifest(mp)
            if data:
                parsed.append((mp, data))

        if parsed:
            uid = self.get_case_insensitive(parsed[0][1], "UniqueID") or self.fallback_uid(entry_path)
        else:
            uid = self.fallback_uid(entry_path)

        record = self._build_record(uid, entry, entry_path, manifests, parsed)

        uid_to_paths[record["unique_id"]].append(entry_path)
        uid_to_record_candidates[record["unique_id"]].append(record)

        if self.debug:
            print(
                f"[SCANNER] found uid={record['unique_id']} root={entry_path} "
                f"manifests={record['manifest_count']} modpack={record['is_modpack']}"
            )

    def scan(self):
        mods = {}
        uid_to_paths = defaultdict(list)
        uid_to_record_candidates = defaultdict(list)

        if not os.path.isdir(self.path):
            print(f"[SCANNER][ERROR] Mods 路径不存在: {self.path}")
            return mods, {}

        if self.debug:
            print(f"[SCANNER] root={self.path}")

        for entry in sorted(os.listdir(self.path)):
            entry_path = os.path.join(self.path, entry)
            if not os.path.isdir(entry_path):
                continue

            if self._is_category_folder(entry):
                if self.debug:
                    print(f"[SCANNER] enter category folder: {entry}")

                for child in sorted(os.listdir(entry_path)):
                    child_path = os.path.join(entry_path, child)
                    if os.path.isdir(child_path):
                        self._scan_candidate_root(child, child_path, uid_to_paths, uid_to_record_candidates)
                continue

            self._scan_candidate_root(entry, entry_path, uid_to_paths, uid_to_record_candidates)

        duplicates = {}
        for uid, paths in uid_to_paths.items():
            if len(paths) > 1:
                duplicates[uid] = sorted(paths)

            primary = self._pick_primary_path(paths)

            chosen = None
            for r in uid_to_record_candidates[uid]:
                if os.path.abspath(r["folder_path"]) == os.path.abspath(primary):
                    chosen = r
                    break

            if not chosen:
                chosen = uid_to_record_candidates[uid][0]
                chosen["folder_path"] = primary

            mods[uid] = chosen

        if self.debug and duplicates:
            print("\n[SCANNER DUPLICATES DETECTED]")
            for uid, paths in duplicates.items():
                print(f"  UID={uid}")
                for p in paths:
                    print(f"    - {p}")
            print()

        return mods, duplicates
