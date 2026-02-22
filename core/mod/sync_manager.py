import os
import shutil
import re
from core.config.constants import ModStatus
from pathlib import Path

# =========================
# 负责保持database,Mods,storage三方同步
# =========================

class SyncManager:

    def __init__(self, game_scanner, storage_scanner, db, storage_path):
        self.game_scanner = game_scanner
        self.storage_scanner = storage_scanner
        self.db = db
        self.storage_path = os.path.abspath(storage_path)

    # =========================
    # 安全路径校验
    # =========================
    def _safe_under_root(self, path, root):
        path = os.path.abspath(path)
        root = os.path.abspath(root)
        return os.path.commonpath([path, root]) == root

    # =========================
    # 规范化分类顺序（防止重复）
    # =========================
    def _normalize_category_order(self):
        rows = self.db.conn.execute("""
            SELECT category, MIN(category_order) AS ord
            FROM mods
            GROUP BY category
            ORDER BY ord, category
        """).fetchall()

        # 如果某分类的 category_order 是 None，MIN(ord) 会是 None
        # 我们需要把 None 的分类排到最后
        rows_sorted = sorted(
            rows,
            key=lambda r: (999999 if r["ord"] is None else r["ord"])
        )

        for idx, r in enumerate(rows_sorted, start=1):
            self.db.conn.execute(
                "UPDATE mods SET category_order=? WHERE category=?",
                (idx, r["category"])
            )

        self.db.conn.commit()

    # =========================
    # 目标路径获取
    # =========================

    def _build_target_path(self, mod):
        if mod["status"] == ModStatus.ENABLED.value:
            root = self.game_mods_path
        else:
            root = self.profile_storage_path

        category = mod.get("category", "默认")
        category_order = int(mod.get("category_order", 1) or 1)
        category_dir = f"{category_order:02d}_{category}"

        return os.path.join(
            root,
            category_dir,
            os.path.basename(mod["folder_path"])
        )

    # =========================
    # 按 DB 重命名分类目录
    # =========================
    def _rename_category_folders(self):
        import os

        roots = [
            ("GAME", self.game_scanner.path),
            ("STORAGE", self.storage_path),
        ]

        # DB 中的分类顺序（权威）
        rows = self.db.conn.execute("""
            SELECT DISTINCT category, category_order
            FROM mods
            ORDER BY category_order
        """).fetchall()

        db_categories = {
            r["category"]: int(r["category_order"])
            for r in rows
        }

        for label, root in roots:
            print(f"\n[RENAME_CAT] root ({label}) =", root)

            if not root or not os.path.isdir(root):
                print(f"[RENAME_CAT] root ({label}) invalid, skip")
                continue

            # 扫描磁盘现有分类目录
            disk_dirs = {}
            for name in os.listdir(root):
                path = os.path.join(root, name)
                if not os.path.isdir(path):
                    continue
                if "_" not in name:
                    continue
                prefix, cat = name.split("_", 1)
                if prefix.isdigit():
                    disk_dirs[cat] = (int(prefix), path)

            print(f"[RENAME_CAT] disk dirs ({label}):")
            for cat, (order, path) in disk_dirs.items():
                print(f"   * {order:02d}_{cat}")

            # 对每个 DB 分类，执行 rename / create
            for cat, new_order in db_categories.items():
                expected_name = f"{new_order:02d}_{cat}"
                expected_path = os.path.join(root, expected_name)

                if cat in disk_dirs:
                    old_order, old_path = disk_dirs[cat]
                    old_name = os.path.basename(old_path)

                    if old_name != expected_name:
                        print(f"[RENAME_CAT] ({label}) rename {old_name} -> {expected_name}")

                        if os.path.exists(expected_path):
                            print("  -> target exists, skip rename")
                        else:
                            os.rename(old_path, expected_path)
                    else:
                        print(f"[RENAME_CAT] ({label}) {expected_name} already correct")
                else:
                    print(f"[RENAME_CAT] ({label}) create missing category dir: {expected_name}")
                    os.makedirs(expected_path, exist_ok=True)

    # =========================
    # 隔离重复副本（不删除，移动到 99_重复）
    # =========================
    def _isolate_duplicates(self, duplicates, root):
        if not duplicates:
            return

        dup_folder = os.path.join(root, "99_重复")
        os.makedirs(dup_folder, exist_ok=True)
        #
        # print("\n==============================")
        # print("START _isolate_duplicates")
        # print("==============================\n")

        for uid, paths in duplicates.items():
            # paths 包含主目录在内：我们只移动“非主目录”
            # 主目录 = paths[0]（scanner 已经按规则排序/挑选过主目录时，也可能不是第一个）
            # 为了稳：以 db/scan 返回的 folder_path 为主目录更可靠，但这里先用“第一个不动”的策略
            primary = paths[0]
            for p in paths[1:]:
                src = os.path.abspath(p)
                if not os.path.exists(src):
                    print(f"[DUP SKIP] not exists: UID={uid} PATH={src}")
                    continue

                # 只处理在 root 下的重复（避免误动外部路径）
                if not self._safe_under_root(src, root):
                    print(f"[DUP SKIP] outside root: UID={uid} PATH={src}")
                    continue

                dst = os.path.join(dup_folder, os.path.basename(src))
                if os.path.exists(dst):
                    print(f"[DUP SKIP] target exists: UID={uid} DST={dst}")
                    continue

                print(f"[DUP MOVE] UID={uid}")
                print(f"  PRIMARY={primary}")
                print(f"  SRC={src}")
                print(f"  DST={dst}")
                shutil.move(src, dst)

    # =========================
    # 扫描并合并（UID 去重）
    # =========================
    def _scan_all(self):
        #
        # print("\n==============================")
        # print("START _scan_all")
        # print("==============================\n")

        first_build = not self.db.get_all_mods()

        if first_build:
            print("[SCAN_ALL] First-time build: enable bootstrap")
            self.game_scanner.bootstrap = True
            self.storage_scanner.bootstrap = True
        else:
            self.game_scanner.bootstrap = False
            self.storage_scanner.bootstrap = False

        # 第一次扫描
        raw_game, dup_game = self.game_scanner.scan()
        raw_storage, dup_storage = self.storage_scanner.scan()

        # 首次建库不隔离重复项
        if not first_build:
            self._isolate_duplicates(dup_game, self.game_scanner.path)
            self._isolate_duplicates(dup_storage, self.storage_path)

            # 隔离后重新扫描
            raw_game, _ = self.game_scanner.scan()
            raw_storage, _ = self.storage_scanner.scan()

        print("---- RAW GAME ----")
        for uid, mod in raw_game.items():
            print(
                f"[GAME] UID={uid} PATH={mod['folder_path']} PACK={mod['is_modpack']} MANIFESTS={mod['manifest_count']}")
        print("------------------\n")

        print("---- RAW STORAGE ----")
        for uid, mod in raw_storage.items():
            print(
                f"[STORAGE] UID={uid} PATH={mod['folder_path']} PACK={mod['is_modpack']} MANIFESTS={mod['manifest_count']}")
        print("---------------------\n")

        uid_map = {}

        def register(source_dict, status, label):
            for uid, mod in source_dict.items():
                root = os.path.abspath(mod["folder_path"])
                print(f"[REGISTER {label}] UID={uid} PATH={root} STATUS={status}")

                mod_copy = dict(mod)
                mod_copy["status"] = status
                mod_copy["folder_path"] = root

                if uid not in uid_map:
                    print(f"  -> NEW UID {uid}")
                    uid_map[uid] = mod_copy
                else:
                    old = uid_map[uid]
                    print(f"  -> UID CONFLICT {uid}")
                    print(f"     OLD PATH={old['folder_path']} STATUS={old['status']}")
                    print(f"     NEW PATH={root} STATUS={status}")

                    # 优先级：game > storage
                    if (
                            status == ModStatus.ENABLED.value
                            and old["status"] != ModStatus.ENABLED.value
                    ):
                        print("     -> REPLACED WITH GAME VERSION")
                        uid_map[uid] = mod_copy
                    else:
                        print("     -> KEEP OLD")

        register(raw_storage, ModStatus.DISABLED.value, "STORAGE")
        register(raw_game, ModStatus.ENABLED.value, "GAME")

        print("\n---- AFTER UID MERGE ----")
        for uid, mod in uid_map.items():
            print(f"[MERGED] UID={uid} PATH={mod['folder_path']} STATUS={mod['status']}")
        print("--------------------------\n")

        fs_index = {
            uid: os.path.abspath(mod["folder_path"])
            for uid, mod in uid_map.items()
        }

        return uid_map, fs_index
    # =========================
    # 写数据库（新增 + 更新）
    # =========================
    def _update_db(self, scanned_mods):

        # print("\n==============================")
        # print("START _update_db")
        # print("==============================\n")

        db_mods = self.db.get_all_mods()

        for uid, mod in scanned_mods.items():

            print(f"\n[UPDATE_DB] UID={uid}")
            print(f"  SCANNED PATH={mod['folder_path']}")

            old = db_mods.get(uid)

            if old:
                print(f"  DB PATH={old['folder_path']} DB CAT={old['category']} DB ORDER={old['mod_order']}")

                # =========================
                # 系统字段：以 DB 为准
                # =========================
                mod["category"] = old["category"]
                mod["category_order"] = old["category_order"]
                mod["mod_order"] = old["mod_order"]

                # =========================
                # 用户字段保护
                # Scanner 不允许覆盖这些字段
                # =========================
                if not mod.get("image_url"):
                    mod["image_url"] = old.get("image_url", "")
                if not mod.get("source_url"):
                    mod["source_url"] = old.get("source_url", "")
                if not mod.get("description"):
                    mod["description"] = old.get("description", "")
                if not mod.get("author"):
                    mod["author"] = old.get("author", "")
                if not mod.get("version"):
                    mod["version"] = old.get("version", "")

                if old["folder_path"] != mod["folder_path"]:
                    print("  -> PATH CHANGED")
                else:
                    print("  -> PATH SAME")

            else:
                print("  -> NEW MOD")

                # =========================
                # 新 Mod：初始化分类与顺序
                # =========================
                mod["category"] = "默认"

                row = self.db.conn.execute(
                    "SELECT category_order FROM mods WHERE category = ? LIMIT 1",
                    (mod["category"],)
                ).fetchone()
                mod["category_order"] = int(row["category_order"]) if row else 1

                mods_in_cat = self.db.get_mods_by_category(mod["category"])
                new_order = (max([m["mod_order"] for m in mods_in_cat]) + 1) if mods_in_cat else 1
                mod["mod_order"] = new_order

                print(f"  -> ASSIGN MOD ORDER={new_order} CAT_ORDER={mod['category_order']}")

            print(f"  FINAL CAT={mod['category']} FINAL ORDER={mod['mod_order']}")
            self.db.upsert_mod(mod)

        return self.db.get_all_mods()

    # =========================
    # missing 标记
    # =========================
    def _mark_missing(self, db_mods, fs_index):
        print("\n---- CHECK MISSING ----")
        for uid in db_mods:
            if uid not in fs_index:
                print(f"[MISSING] UID={uid}")
                self.db.mark_missing(uid)
        print("------------------------\n")

    # =========================
    # 分类目录创建
    # =========================
    def _ensure_category_folder(self, root, category, order):
        safe = f"{int(order):02d}_{category}"
        path = os.path.join(root, safe)
        os.makedirs(path, exist_ok=True)
        return path

    # =========================
    # 分类整理（安全移动）
    # =========================
    def _apply_category_layout(self, scanned_mods):

        print("\n==============================")
        print("START _apply_category_layout")
        print("==============================\n")

        all_mods = self.db.get_all_mods()

        # =========================================================
        # Phase A: 状态驱动移动（UI 启用 / 禁用的唯一裁决）
        # =========================================================
        print(">>> PHASE A: STATUS-DRIVEN RELOCATION")

        for uid, mod in all_mods.items():

            real_path = os.path.abspath(mod["folder_path"])

            if not os.path.exists(real_path):
                print(f"[A] SKIP {uid} (PATH NOT EXISTS)")
                continue

            # root 完全由 DB status 决定
            if mod.get("status") == ModStatus.ENABLED.value:
                target_root = self.game_scanner.path
            else:
                target_root = self.storage_path

            category = mod.get("category", "默认")
            category_order = int(mod.get("category_order", 1) or 1)
            category_dir = f"{category_order:02d}_{category}"
            target_category = os.path.join(target_root, category_dir)
            os.makedirs(target_category, exist_ok=True)

            target_path = os.path.join(
                target_category,
                os.path.basename(real_path)
            )

            print(f"[A] UID={uid}")
            print(f"    REAL={real_path}")
            print(f"    TARGET={target_path}")

            if os.path.abspath(real_path) == os.path.abspath(target_path):
                print("    -> OK (ALREADY CORRECT)")
                continue

            if os.path.exists(target_path):
                dup_dir = os.path.join(target_root, "99_重复")
                os.makedirs(dup_dir, exist_ok=True)
                fallback = os.path.join(dup_dir, os.path.basename(real_path))

                print(f"    -> CONFLICT, MOVE TO {fallback}")
                shutil.move(real_path, fallback)
                self.db.update_mod_path(uid, fallback)
            else:
                print("    -> MOVE EXECUTE")
                shutil.move(real_path, target_path)
                self.db.update_mod_path(uid, target_path)

        # =========================================================
        # Phase B: 结构修复（分类 / 顺序 / 命名）
        # =========================================================
        print("\n>>> PHASE B: STRUCTURE REPAIR")

        for uid, mod in all_mods.items():

            real_path = os.path.abspath(mod["folder_path"])
            if not os.path.exists(real_path):
                continue

            # root 仍然由 DB status 决定
            if mod.get("status") == ModStatus.ENABLED.value:
                root = self.game_scanner.path
            else:
                root = self.storage_path

            category = mod.get("category", "默认")
            category_order = int(mod.get("category_order", 1) or 1)
            category_dir = f"{category_order:02d}_{category}"
            target_category = os.path.join(root, category_dir)
            os.makedirs(target_category, exist_ok=True)

            target_path = os.path.join(
                target_category,
                os.path.basename(real_path)
            )

            if os.path.abspath(real_path) == os.path.abspath(target_path):
                continue

            if os.path.exists(target_path):
                dup_dir = os.path.join(root, "99_重复")
                os.makedirs(dup_dir, exist_ok=True)
                fallback = os.path.join(dup_dir, os.path.basename(real_path))
                shutil.move(real_path, fallback)
                self.db.update_mod_path(uid, fallback)
            else:
                shutil.move(real_path, target_path)
                self.db.update_mod_path(uid, target_path)

    # =========================
    # 文件夹名安全化
    # =========================
    def _sanitize_folder_name(self, name: str) -> str:
        name = name.strip()
        name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", name)  # Windows illegal
        name = re.sub(r"\s+", " ", name)
        name = name.rstrip(". ")
        if not name:
            name = "Unnamed"
        return name

    # =========================
    # 解析已命名的前缀 order（用于避免重复重命名）
    # 允许格式：0001_uid_name 或 1_uid_name
    # =========================
    def _parse_prefixed_order(self, folder_name: str):
        m = re.match(r"^(\d+)_", folder_name)
        if not m:
            return None
        try:
            return int(m.group(1))
        except Exception:
            return None
    # =========================
    # 压缩每个分类内的 mod_order（保证连续）
    # =========================
    def _normalize_mod_order_per_category(self):
        """
        对每个分类内的 mod_order 进行全量压缩：
        1, 2, 3, ... N
        """
        mods = self.db.get_all_mods()

        # category -> list[mod]
        by_category = {}
        for mod in mods.values():
            cat = mod.get("category", "默认")
            by_category.setdefault(cat, []).append(mod)

        for cat, mod_list in by_category.items():
            # 排序规则：优先原 mod_order，其次 name / uid 保证稳定
            mod_list.sort(
                key=lambda m: (
                    int(m.get("mod_order") or 9999),
                    m.get("name", ""),
                    m.get("unique_id", "")
                )
            )

            # 重新写回连续顺序
            for idx, mod in enumerate(mod_list, start=1):
                if mod.get("mod_order") != idx:
                    self.db.update_mod_order(mod["unique_id"], idx)

    # =========================
    # 按 DB 重命名分类文件夹内的 Mod 文件夹
    # 目标格式：mod_order_uid_modname
    # =========================
    def _rename_mod_folders_by_db(self):

        print("\n==============================")
        print("START _rename_mod_folders_by_db")
        print("==============================\n")

        all_mods = self.db.get_all_mods()

        for uid, mod in all_mods.items():
            db_root = os.path.abspath(mod["folder_path"])
            real_path = db_root

            print(f"\n[RENAME CHECK] UID={uid}")
            print(f"  DB ROOT={db_root}")

            if not os.path.exists(db_root):
                print("  -> SKIP (NOT EXISTS)")
                continue

            parent = os.path.dirname(db_root)
            parent_name = os.path.basename(parent)

            # 只允许在分类目录内 rename
            if not self._is_category_dir_name(parent_name):
                print(f"  -> SKIP (NOT IN CATEGORY FOLDER) PARENT={parent_name}")
                continue

            mod_order = int(mod.get("mod_order", 9999))
            mod_name = self._sanitize_folder_name(mod.get("name") or os.path.basename(db_root))
            uid_safe = self._sanitize_folder_name(uid)

            target_name = f"{mod_order:04d}_{uid_safe}_{mod_name}"
            target_path = os.path.join(parent, target_name)

            current_name = os.path.basename(db_root)
            expected_prefix = f"{mod_order:04d}_"

            if current_name.startswith(expected_prefix):
                print("  -> SKIP (PREFIX MATCH)")
                continue

            if os.path.exists(target_path):
                print(f"  -> SKIP (TARGET EXISTS) TARGET={target_path}")
                continue

            # 根目录安全检查
            if self._safe_under_root(db_root, self.game_scanner.path):
                root = self.game_scanner.path
            elif self._safe_under_root(db_root, self.storage_path):
                root = self.storage_path
            else:
                print("  -> SKIP (OUTSIDE ROOT)")
                continue

            if not self._safe_under_root(target_path, root):
                print("  -> SKIP (TARGET OUTSIDE ROOT)")
                continue

            print("  -> RENAME EXECUTE")
            print(f"  FROM={db_root}")
            print(f"  TO  ={target_path}")

            os.rename(db_root, target_path)
            self.db.update_mod_path(uid, target_path)

    # =========================
    # 两阶段重命名（解决压缩编号时 TARGET EXISTS 冲突）
    # =========================
    def _rename_mod_folders_by_db_two_phase(self):
        print("\n==============================")
        print("START _rename_mod_folders_by_db_two_phase")
        print("==============================\n")

        all_mods = self.db.get_all_mods()
        temp_map = {}

        # ===== Phase 1：只对 DB root 做临时改名 =====
        for uid, mod in all_mods.items():
            db_root = os.path.abspath(mod["folder_path"])

            print(f"\n[PHASE1 CHECK] UID={uid}")
            print(f"  DB ROOT={db_root}")

            if not os.path.exists(db_root):
                print("  -> SKIP (NOT EXISTS)")
                continue

            parent = os.path.dirname(db_root)
            parent_name = os.path.basename(parent)

            if not self._is_category_dir_name(parent_name):
                print(f"  -> SKIP (NOT IN CATEGORY FOLDER) PARENT={parent_name}")
                continue

            mod_order = int(mod.get("mod_order", 9999))
            mod_name = self._sanitize_folder_name(mod.get("name") or os.path.basename(db_root))
            uid_safe = self._sanitize_folder_name(uid)

            target_name = f"{mod_order:04d}_{uid_safe}_{mod_name}"
            target_path = os.path.join(parent, target_name)

            if os.path.abspath(db_root) == os.path.abspath(target_path):
                print("  -> SKIP (ALREADY NAMED)")
                continue

            temp_name = f"__tmp__{uid_safe}__{os.path.basename(db_root)}"
            temp_path = os.path.join(parent, temp_name)

            if os.path.exists(temp_path):
                print(f"  -> SKIP (TEMP EXISTS) TEMP={temp_path}")
                continue

            print("  -> TEMP RENAME EXECUTE")
            print(f"  FROM={db_root}")
            print(f"  TO  ={temp_path}")

            os.rename(db_root, temp_path)
            self.db.update_mod_path(uid, temp_path)
            temp_map[uid] = temp_path

        # ===== Phase 2：从临时名改到最终名 =====
        all_mods = self.db.get_all_mods()
        for uid, mod in all_mods.items():
            if uid not in temp_map:
                continue

            real_path = os.path.abspath(mod["folder_path"])

            print(f"\n[PHASE2 CHECK] UID={uid}")
            print(f"  REAL PATH={real_path}")

            if not os.path.exists(real_path):
                print("  -> SKIP (NOT EXISTS)")
                continue

            parent = os.path.dirname(real_path)

            mod_order = int(mod.get("mod_order", 9999))
            mod_name = self._sanitize_folder_name(mod.get("name") or os.path.basename(real_path))
            uid_safe = self._sanitize_folder_name(uid)

            target_name = f"{mod_order:04d}_{uid_safe}_{mod_name}"
            target_path = os.path.join(parent, target_name)

            if os.path.exists(target_path):
                print(f"  -> SKIP (TARGET EXISTS) TARGET={target_path}")
                print(f"     ⚠️  可能导致临时目录未清理，请检查是否有冲突或残留")
                continue

            print("  -> FINAL RENAME EXECUTE")
            print(f"  FROM={real_path}")
            print(f"  TO  ={target_path}")

            os.rename(real_path, target_path)
            self.db.update_mod_path(uid, target_path)

        # ===== Phase 3：清理残留的 __tmp__ 目录（仅清理未被数据库引用的）=====
        print("\n[PHASE3] 清理残留的临时目录")
        for uid, temp_path in temp_map.items():
            current_path = self.db.get_mod(uid)["folder_path"]
            if os.path.abspath(current_path) != os.path.abspath(temp_path):
                if os.path.exists(temp_path):
                    print(f"  -> 清理未完成的临时目录: {temp_path}")
                    try:
                        shutil.rmtree(temp_path)
                    except Exception as e:
                        print(f"     ❌ 删除失败: {e}")
            else:
                print(f"  -> 保留仍在使用的临时目录: {temp_path}")

        print("\n==============================")
        print("END _rename_mod_folders_by_db_two_phase")
        print("==============================\n")

    # =========================
    # 判断是否为分类目录名（与 scanner 规则一致）
    # =========================
    def _is_category_dir_name(self, name: str) -> bool:
        if "_" not in name:
            return False
        prefix, _ = name.split("_", 1)
        return prefix.isdigit()

    def _cleanup_empty_category_dirs(self):
        root = Path(self.game_scanner.path)
        db_categories = set(self.db.get_all_categories())  # 只拿 category 名

        for p in root.iterdir():
            if not p.is_dir():
                continue
            if "_" not in p.name:
                continue

            prefix, cat = p.name.split("_", 1)
            if not prefix.isdigit():
                continue

            # 不在 DB 中 + 目录为空 → 删除
            if cat not in db_categories and not any(p.iterdir()):
                p.rmdir()

    # =========================
    # 外部入口
    # =========================
    def sync(self):

        print("\n========================================")
        print("============== START SYNC ==============")
        print("========================================\n")
        print("🔥 DB PATH IN SYNC =", os.path.abspath(self.db.conn.execute("PRAGMA database_list").fetchone()[2]))

        scanned_mods, fs_index = self._scan_all()
        db_mods = self._update_db(scanned_mods)

        self._normalize_category_order()
        self._rename_category_folders()
        scanned_mods, fs_index = self._scan_all()
        self._last_scan = scanned_mods
        self._apply_category_layout(scanned_mods)

        self._normalize_mod_order_per_category()
        self._rename_mod_folders_by_db_two_phase()
        self._mark_missing(self.db.get_all_mods(), fs_index)
        self._cleanup_empty_category_dirs()

        print("\n========================================")
        print("=============== END SYNC ===============")
        print("========================================\n")
