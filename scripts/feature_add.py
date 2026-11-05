"""从 proposal.json 的 feature_draft 草案追加 feature 到 feature_list.json。

设计目标：把「人工手写 JSON」降级为「人工执行一条命令」。

契约：
- 草案来源：proposal.json → notes[type == "feature_draft"].content（数组）
- 仅追加新条目，绝不修改既有条目的任何字段
- 默认 dry-run，只打印不落盘；加 --yes 才写入
- 写入为原子操作（临时文件 + replace），格式与 scripts/verifier.py 保持一致
- 新条目统一写入 status=not_started、testedAt=null、evidence=null、history=[]
  （status / testedAt / evidence 之后只允许 verifier.py 修改）
- 退出码：0 成功（含 dry-run）／1 校验失败或前置条件不满足
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, NoReturn

# 以脚本位置推导仓库根，避免依赖调用时的 cwd
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROPOSAL = ROOT / "proposal.json"
DEFAULT_FEATURE_LIST = ROOT / "feature_list.json"

ID_PATTERN = re.compile(r"^feat_[a-z0-9_]+$")
DEFAULT_AREA = "common"
# 新条目必须从未开始状态起步；passing/active 只由 verifier.py 写入
INITIAL_STATUS = "not_started"


def emit(payload: dict[str, Any]) -> None:
    """输出美化 JSON（2 空格缩进，中文不转义），便于人工阅读，也仍可被 jq 解析。"""
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def fail(reason: str, **extra: Any) -> NoReturn:
    emit({"ok": False, "error": reason, **extra})
    sys.exit(1)


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"无法读取{label} {path}: {exc}")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"{label} 不是合法 JSON: {exc}")

    if not isinstance(data, dict):
        fail(f"{label} 顶层必须是对象: {path}")

    return data


def collect_drafts(proposal: dict[str, Any]) -> list[dict[str, Any]]:
    """把所有 feature_draft 类型 note 的 content 拍平成一个草案列表。"""
    notes = proposal.get("notes")
    if not isinstance(notes, list):
        fail("proposal.json 缺少 notes 数组")

    drafts: list[dict[str, Any]] = []
    for note in notes:
        if not isinstance(note, dict) or note.get("type") != "feature_draft":
            continue
        content = note.get("content")
        if not isinstance(content, list):
            fail("feature_draft.content 必须是数组")
        for item in content:
            if not isinstance(item, dict):
                fail("feature_draft.content 的元素必须是对象")
            drafts.append(item)

    return drafts


def require_str(draft: dict[str, Any], key: str, where: str) -> str:
    value = draft.get(key)
    if not isinstance(value, str) or not value.strip():
        fail(f"{where} 缺少非空字符串字段 {key}", feature_id=draft.get("id"))
    return value


def build_entry(
    draft: dict[str, Any],
    seen_ids: set[str],
    used_priorities: set[int],
    next_priority: int,
) -> tuple[dict[str, Any], int]:
    """校验单个草案并返回规范化条目，以及更新后的下一个可用 priority。"""
    feature_id = draft.get("id")
    if not isinstance(feature_id, str) or not ID_PATTERN.match(feature_id):
        fail("id 非法：需匹配 ^feat_[a-z0-9_]+$", id=feature_id)
    if feature_id in seen_ids:
        fail("id 重复：草案与 feature_list 或彼此之间存在冲突", feature_id=feature_id)

    title = require_str(draft, "title", f"feature {feature_id}")
    behavior = require_str(draft, "user_visible_behavior", f"feature {feature_id}")
    verification = require_str(draft, "verification", f"feature {feature_id}")
    if "\n" in verification:
        fail("verification 必须是单行 shell 命令", feature_id=feature_id)

    if "priority" in draft:
        priority = draft["priority"]
        if not isinstance(priority, int) or isinstance(priority, bool) or priority <= 0:
            fail("priority 必须是正整数", feature_id=feature_id)
        if priority in used_priorities:
            fail(
                "priority 与既有 feature 冲突，请调整草案或省略该字段以自动分配",
                feature_id=feature_id,
                priority=priority,
                used_priorities=sorted(used_priorities),
            )
    else:
        priority = next_priority
        while priority in used_priorities:
            priority += 1

    area = draft.get("area", DEFAULT_AREA)
    if not isinstance(area, str) or not area.strip():
        fail("area 必须是非空字符串", feature_id=feature_id)

    status = draft.get("status", INITIAL_STATUS)
    if status != INITIAL_STATUS:
        fail(
            f"草案 status 只能为 {INITIAL_STATUS}；passing/active 仅由 verifier.py 写入",
            feature_id=feature_id,
            status=status,
        )

    entry: dict[str, Any] = {
        "id": feature_id,
        "priority": priority,
        "area": area,
        "title": title,
        "user_visible_behavior": behavior,
        "verification": verification,
        "status": INITIAL_STATUS,
        "testedAt": None,
        "evidence": None,
        "history": [],
    }
    return entry, max(next_priority, priority + 1)


def save_feature_list(path: Path, data: dict[str, Any]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(path)
    except OSError as exc:
        fail(f"写回 {path} 失败: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="从 proposal.json 的 feature_draft 追加 feature 到 feature_list.json")
    parser.add_argument("--proposal", type=Path, default=DEFAULT_PROPOSAL, help="提案文件路径（默认仓库根 proposal.json）")
    parser.add_argument(
        "--feature-list",
        type=Path,
        default=DEFAULT_FEATURE_LIST,
        help="feature 清单路径（默认仓库根 feature_list.json）",
    )
    parser.add_argument("--yes", action="store_true", help="真正写入；不加此参数只做 dry-run 预览")
    args = parser.parse_args()

    proposal = load_json(args.proposal, "提案文件")
    data = load_json(args.feature_list, "feature 清单")

    features = data.get("features")
    if not isinstance(features, list):
        fail("feature_list.json 结构非法：缺少 features 数组")

    existing_ids: set[str] = set()
    used_priorities: set[int] = set()
    next_priority = 1
    for item in features:
        if not isinstance(item, dict):
            fail("features 数组元素必须是对象")
        feature_id = item.get("id")
        if isinstance(feature_id, str):
            existing_ids.add(feature_id)
        priority = item.get("priority")
        if isinstance(priority, int) and not isinstance(priority, bool):
            used_priorities.add(priority)
            next_priority = max(next_priority, priority + 1)

    drafts = collect_drafts(proposal)
    if not drafts:
        fail("proposal.json 中未找到 type=feature_draft 的草案，无可导入内容")

    seen_ids = set(existing_ids)
    entries: list[dict[str, Any]] = []
    for draft in drafts:
        entry, next_priority = build_entry(draft, seen_ids, used_priorities, next_priority)
        seen_ids.add(entry["id"])
        used_priorities.add(entry["priority"])
        entries.append(entry)

    if not args.yes:
        emit(
            {
                "ok": True,
                "dry_run": True,
                "would_add": entries,
                "hint": "确认无误后加 --yes 写入；本脚本只追加，不覆盖既有条目",
            }
        )
        return 0

    features.extend(entries)
    save_feature_list(args.feature_list, data)

    emit(
        {
            "ok": True,
            "dry_run": False,
            "added": [entry["id"] for entry in entries],
            "next_step": "编码完成后用 uv run python scripts/verifier.py --feature-id <id> 验收",
        }
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
