#!/usr/bin/env python3
"""Codex Auth 回退工具 — 独立入口"""
import argparse
import sys

from cxauth import cli_restore


def main() -> int:
    ap = argparse.ArgumentParser(
        description="将 auth.json.bak 恢复为 auth.json（保留 .bak）"
    )
    ap.add_argument("--codex-home", default=None, help="~/.codex 的替代目录")
    ap.add_argument("--yes", action="store_true", help="跳过确认")
    ap.add_argument("--info", action="store_true", help="只显示状态，不恢复")
    ap.add_argument("--no-save-current", action="store_true",
                    help="不保存当前为 auth.json.before-restore")
    args = ap.parse_args()
    return cli_restore.run(args)


if __name__ == "__main__":
    sys.exit(main())