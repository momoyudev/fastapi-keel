"""Bootstrap 地基冒烟测试。

仅用于证明 pytest 工具链正常可用，与业务需求无关。
bootstrap 校验只验证底座，不验证业务功能。
"""

from src.main import app


def test_bootstrap_framework_alive():
    """校验 pytest 可正常执行。"""
    assert 1 + 1 == 2


def test_bootstrap_import_skeleton():
    """校验 src 包可导入且骨架合法。

    导入失败必须直接抛错（collection error），不做 try/except 静默跳过——
    历史教训：此处曾用 `except Exception: pass` 吞掉 ModuleNotFoundError，
    导致 `uv run pytest` 实际无法导入 src.* 的问题长期未暴露。
    """
    assert app is not None
