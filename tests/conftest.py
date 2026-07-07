"""Pytest 共享 fixtures。"""
import pytest

from shared.utils.sandbox import reset_sandbox


@pytest.fixture(autouse=True)
def _reset_sandbox_each_test():
    """每个测试前清空 sandbox，保证隔离。"""
    reset_sandbox()
    yield
