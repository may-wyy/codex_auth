"""回退交互流程"""
import sys
from pathlib import Path

from . import ui, storage
from .auth_data import info_from_auth_json
from .paths import codex_home_dir
from .storage import StorageError


def _fmt_duration(seconds: int) -> str:
    if seconds <= 0:
        return "已过期"
    d, s = divmod(seconds, 86400)
    h, s = divmod(s, 3600)
    m, _ = divmod(s, 60)
    if d:
        return f"{d} 天 {h} 小时"
    if h:
        return f"{h} 小时 {m} 分钟"
    return f"{m} 分钟"


def _print_info(path: Path, label: str) -> None:
    info = info_from_auth_json(path)
    if info:
        print(f"  {path}  {label}")
        print(f"    账号:    {info['email']}")
        if info["expiresAt"]:
            print(f"    过期:    {info['expiresAt']}")
            print(f"    剩余:    {_fmt_duration(info['expiresIn'])}")
    else:
        print(f"  {path}  {label}")
        print(f"    {ui.warn('内容无法解析')}")


def run(args) -> int:
    ui.init()

    print("Codex Auth 回退工具 v1.2.0")
    print(ui.divider())
    print()

    codex_home = (Path(args.codex_home).expanduser()
                  if args.codex_home else codex_home_dir())
    state = storage.inspect(codex_home)

    if not state["codex_dir"].exists():
        print(ui.err(f"{state['codex_dir']} 不存在"))
        return 1

    if not state["bak_exists"]:
        print(ui.err(f"未找到原始配置备份: {state['bak_file']}"))
        print()
        print("  首次运行 codex_auto.py 时，如果已有 auth.json 才会建立备份")
        print("  无法回退。")
        return 1

    print("读取当前状态:")
    print()
    if state["auth_exists"]:
        _print_info(state["auth_file"], "(当前生效)")
    else:
        print(f"  {state['auth_file']}  {ui.warn('(不存在)')}")
    print()
    _print_info(state["bak_file"], "(原始配置)")
    print()

    bak = info_from_auth_json(state["bak_file"])
    default_yes = True
    if bak:
        if bak["expiresIn"] <= 0:
            print(ui.warn("警告：原始配置中的账号已过期"))
            print("   恢复后 codex 仍需要重新登录 ChatGPT 获取新 session")
            default_yes = False
        elif bak["expiresIn"] < 86400:
            print(ui.warn("注意：原始配置中的账号将在 24 小时内过期"))
        print()

    if args.info:
        return 0

    if not args.yes:
        prompt = "[Y/n]" if default_yes else "[y/N]"
        try:
            ans = input(f"确认恢复？{prompt}: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n" + ui.warn("已取消"))
            return 130
        if default_yes and ans == "n":
            print(ui.warn("已取消"))
            return 0
        if not default_yes and ans != "y":
            print(ui.warn("已取消"))
            return 0

    print()
    print("正在恢复...")
    try:
        result = storage.restore(
            codex_home,
            save_current=not args.no_save_current,
        )
    except StorageError as e:
        print(ui.err(str(e)))
        return 1

    before = result["before_restore"]
    bak_file = result["bak_file"]
    auth_file = result["auth_file"]

    if before:
        print(f"  {ui.ok(f'当前 auth.json 已保存为 {before.name}')}")
    print(f"  {ui.ok(f'{bak_file.name} -> {auth_file.name}（覆盖）')}")

    print()
    print(ui.divider())
    print("完成。")
    if bak:
        print(f"现在生效的账号: {bak['email']}")
        print(f"（此 token 剩余: {_fmt_duration(bak['expiresIn'])}）")
    print()
    print("提示:")
    print("  · 原始备份 auth.json.bak 保持不变，可随时再次恢复")
    if before:
        print("  · 如需找回刚才的状态:")
        print(f"      copy {before} {auth_file}")
    print(ui.divider())
    return 0