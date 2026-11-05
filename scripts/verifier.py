#!/usr/bin/env python3
"""Feature 验收脚本（verifier）。

契约：
- feature_list.json 中 status / testedAt / evidence 仅由本脚本写入；
- 退出码：0 = 验收通过；1 = 验收失败或前置条件不满足（便于 CI / 自动化判断）；
- verification 为字符串时按 shell 执行，执行超时受 --timeout 限制（默认 60s）；
- 人工设置的状态（不在 ALLOWED_STATUSES 内）默认拒绝覆盖，确认覆盖需加 --force；
- 被覆盖前的 testedAt / status / evidence 归档到 history（保留最近 3 条）。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NoReturn

# 以脚本位置推导仓库根，避免依赖调用时的 cwd
ROOT = Path(__file__).resolve().parent.parent
FEATURE_LIST_PATH = ROOT / "feature_list.json"

DEFAULT_TIMEOUT = 60
HISTORY_LIMIT = 3
# 本脚本可自行覆盖的状态；其余（如 blocked / waived）需人工 --force
ALLOWED_STATUSES = {"not_started", "active", "passing"}


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def fail(reason: str, **extra: Any) -> NoReturn:
    emit({"ok": False, "error": reason, **extra})
    sys.exit(1)


def utc_now_iso() -> str:
    """统一输出 6 位微秒 + Z，避免 isoformat 在微秒为 0 时省略小数部分。"""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def load_feature_list() -> dict[str, Any]:
    try:
        raw = FEATURE_LIST_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"无法读取 {FEATURE_LIST_PATH}: {exc}")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"feature_list.json 不是合法 JSON: {exc}")

    if not isinstance(data, dict) or not isinstance(data.get("features"), list):
        fail("feature_list.json 结构非法：缺少 features 数组")

    return data


def save_feature_list(data: dict[str, Any]) -> None:
    """原子写入，避免中途失败留下半截文件。"""
    tmp = FEATURE_LIST_PATH.with_name(FEATURE_LIST_PATH.name + ".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(FEATURE_LIST_PATH)
    except OSError as exc:
        fail(f"写回 {FEATURE_LIST_PATH} 失败: {exc}")


def run_verification(command: str, timeout: int) -> tuple[int, str, str, bool]:
    """返回 (returncode, stdout, stderr, timed_out)。超时不抛出，交由调用方落盘。"""
    try:
        # verification 契约为 shell 字符串，此处保留 shell 语义
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        err = exc.stderr or ""
        if isinstance(out, bytes):
            out = out.decode("utf-8", errors="replace")
        if isinstance(err, bytes):
            err = err.decode("utf-8", errors="replace")
        return -1, out, f"{err}\nverification 超时（>{timeout}s）: {command}".strip(), True

    return proc.returncode, proc.stdout, proc.stderr, False


def archive_previous(item: dict[str, Any]) -> None:
    """把本次覆盖前的验收结果归档，保留最近 HISTORY_LIMIT 条。"""
    previous_tested_at = item.get("testedAt")
    if not previous_tested_at:
        return

    history = item.get("history")
    if not isinstance(history, list):
        history = []

    history.append(
        {
            "testedAt": previous_tested_at,
            "status": item.get("status"),
            "evidence": item.get("evidence"),
        }
    )
    item["history"] = history[-HISTORY_LIMIT:]


def main() -> int:
    parser = argparse.ArgumentParser(description="按 feature_list.json 的 verification 验收单个 feature")
    parser.add_argument("--feature-id", required=True)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"verification 执行超时秒数（默认 {DEFAULT_TIMEOUT}）")
    parser.add_argument("--force", action="store_true", help="允许覆盖人工设置的非默认状态")
    args = parser.parse_args()

    data = load_feature_list()

    item = next(
        (f for f in data["features"] if isinstance(f, dict) and f.get("id") == args.feature_id),
        None,
    )
    if item is None:
        fail("feature not found", feature_id=args.feature_id)

    verification = item.get("verification")
    if isinstance(verification, list):
        fail(
            "verification 为断言数组，尚未固化为可执行 shell，请人工确认并更新 feature_list.json",
            mode="assertion",
            feature_id=args.feature_id,
        )
    if not isinstance(verification, str) or not verification.strip():
        fail("verification 为空或格式非法", feature_id=args.feature_id)

    current_status = item.get("status")
    if current_status not in ALLOWED_STATUSES and not args.force:
        fail(
            f"当前状态 {current_status!r} 不在可覆盖范围 {sorted(ALLOWED_STATUSES)} 内；"
            "如确认覆盖请加 --force",
            feature_id=args.feature_id,
            status=current_status,
        )

    returncode, stdout, stderr, timed_out = run_verification(verification, args.timeout)
    passed = (not timed_out) and returncode == 0

    archive_previous(item)
    item["status"] = "passing" if passed else "active"
    item["testedAt"] = utc_now_iso()
    item["evidence"] = {
        "returncode": returncode,
        "stdout": stdout[-2000:],
        "stderr": stderr[-2000:],
        "timeout": timed_out,
    }

    save_feature_list(data)
    emit(
        {
            "ok": passed,
            "feature_id": args.feature_id,
            "returncode": returncode,
            "status": item["status"],
            "timeout": timed_out,
        }
    )
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
