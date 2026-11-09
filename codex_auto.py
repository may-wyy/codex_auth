#!/usr/bin/env python3
"""Codex 免验证登录配置工具 — 主程序入口"""
import argparse
import sys

from cxauth import cli_auto


def main() -> int:
    ap = argparse.ArgumentParser(
        description="从本地浏览器抓 ChatGPT session → 写入 ~/.codex/auth.json"
    )
    ap.add_argument(
        "--platform",
        default=None,
        choices=["auto-unix", "macos", "linux", "windows",
                 "cpa", "sub2api", "cockpit", "emit"],
        help="跳过交互菜单，直接指定平台",
    )
    ap.add_argument("--out-dir", default=None, help="生成物输出目录")
    ap.add_argument("--codex-home", default=None, help="~/.codex 的替代目录")
    ap.add_argument("--method", default="auto",
                    choices=["auto", "clipboard", "stdin"],
                    help="session 获取方式")
    ap.add_argument("--session-file", default=None, help="从文件读取 session")
    ap.add_argument("--reset-backup", action="store_true",
                    help="把原始备份更新为当前 auth.json")
    ap.add_argument("--dry-run", action="store_true", help="只打印不写入")
    args = ap.parse_args()

    if args.platform in ("macos", "linux"):
        args.platform = "auto-unix"

    return cli_auto.run(args)


if __name__ == "__main__":
    sys.exit(main())