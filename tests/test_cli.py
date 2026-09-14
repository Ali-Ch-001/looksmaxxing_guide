"""Unit tests for Command-Line Interface."""

import pytest
from unittest.mock import patch
import sys
from src.cli import main_async


@pytest.mark.asyncio
async def test_cli_successful_run(tmp_path):
    out_dir = str(tmp_path / "out")
    test_args = ["cli.py", "--topic", "topical tretinoin", "--output-dir", out_dir]
    with patch.object(sys, "argv", test_args):
        await main_async()
    assert (tmp_path / "out" / "topical-tretinoin.md").exists()


@pytest.mark.asyncio
async def test_cli_banned_topic_exit(tmp_path):
    out_dir = str(tmp_path / "out")
    test_args = ["cli.py", "--topic", "bone smashing jawline", "--output-dir", out_dir]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            await main_async()
        assert exc_info.value.code == 1
    assert (tmp_path / "out" / "bone-smashing-jawline.md").exists()
