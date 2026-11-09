"""主程序交互流程"""
import os
import sys
import webbrowser
from pathlib import Path

from . import ui, session, auth_data, builders, storage, env, clipboard
from .auth_data import AuthDataError, info_from_auth_json
from .paths import output_dir, ensure_gitignore, codex_home_dir
from .storage import StorageError

SESSION_URL = "https://chatgpt.com/api/auth/session"


def _platform_menu() -> str:
    if sys.platform == "darwin":
        default = "1"
    elif sys.platform == "win32":
        default = "2"
    else:
        default = "1"

    print()
    print("请选择目标平台:")
    print()
    m1 = "← 直接回车" if default == "1" else ""
    m2 = "← 直接回车" if default == "2" else ""
    print(f"  [1] macOS / Linux    写入 ~/.codex/auth.json  {m1}")
    print(f"  [2] Windows          写入 ~/.codex/auth.json  {m2}")
    print("  [3] CPA 面板         输出账号 JSON，供面板导入")
    print("  [4] Sub2API          输出导出 JSON")
    print("  [5] Cockpit          输出账号 JSON")
    print("  [6] 仅输出脚本       不写文件，打印 shell 脚本便于拷贝")
    print()

    mapping = {"1": "auto-unix", "2": "windows", "3": "cpa",
               "4": "sub2api", "5": "cockpit", "6": "emit"}

    while True:
        try:
            ans = input(f"选择 [1-6, 默认 {default}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n" + ui.warn("已取消"))
            sys.exit(130)
        if not ans:
            return mapping[default]
        if ans in mapping:
            return mapping[ans]
        print(ui.err("请输入 1-6 之间的数字"))


def _get_session(method: str, session_file: str = None) -> str:
    if session_file:
        return Path(session_file).read_text(encoding="utf-8")

    if method == "stdin":
        print()
        print("请粘贴 session JSON（完成后按 Ctrl+D，Windows 上按 Ctrl+Z 再回车）:")
        try:
            return sys.stdin.read().strip()
        except KeyboardInterrupt:
            sys.exit(130)

    try:
        webbrowser.open(SESSION_URL)
        print(ui.ok(f"已在浏览器中打开: {SESSION_URL}"))
    except Exception:
        print(ui.warn(f"无法自动打开浏览器，请手动访问: {SESSION_URL}"))

    print()
    print("请在浏览器页面里完成以下操作:")
    print()
    print("  1. 按 Ctrl+A 全选页面内容")
    print("  2. 按 Ctrl+C 复制")
    print("  3. 回到这个终端窗口")
    print()

    try:
        input("复制完成后按 Enter 继续（或 Ctrl+C 取消）: ")
    except (EOFError, KeyboardInterrupt):
        print("\n" + ui.warn("已取消"))
        sys.exit(130)

    text = clipboard.read().strip()
    if text and ('"accessToken"' in text or text.startswith("eyJ")):
        print(ui.ok("已从剪贴板读取到 session"))
        return text

    print(ui.warn("剪贴板内容为空或不是合法 session"))
    print(ui.info("切换到手动粘贴模式..."))
    print()
    print("请粘贴 session JSON（完成后按 Ctrl+D，Windows 上按 Ctrl+Z 再回车）:")
    return sys.stdin.read().strip()


def _print_session_preview(data: dict) -> None:
    print()
    print(ui.divider())
    print("Session 解析结果:")
    print()
    print(f"  账号:    {data['email'] or data['accountId']}")
    print(f"  套餐:    {data['planType'] or '未知'}")
    print(f"  账户 ID: {data['accountId']}")
    if data["issuedAt"]:
        print(f"  签发于:  {data['issuedAt']}")
    if data["expiresAt"]:
        print(f"  有效期至: {data['expiresAt']}")
        h = data["expiresIn"] // 3600
        if h > 48:
            print(f"  剩余:    {h // 24} 天 {h % 24} 小时")
        else:
            print(f"  剩余:    {h} 小时")
    rt = "真实（可自动续期）" if data["refreshToken"] else "占位（一次性）"
    print(f"  refresh_token: {rt}")
    print(ui.divider())
    print()


def _preview_existing(codex_home: Path) -> None:
    state = storage.inspect(codex_home)

    if not state["auth_exists"] and not state["bak_exists"]:
        print(ui.info("未检测到已有 auth.json（首次配置，不会建立备份）"))
        return

    if state["auth_exists"]:
        cur = info_from_auth_json(state["auth_file"])
        if cur:
            print("  已存在 auth.json:")
            print(f"    账号: {cur['email']}")
            print(f"    过期: {cur['expiresAt']}")
        else:
            print(ui.warn("已存在 auth.json（内容无法解析）"))

    if state["bak_exists"]:
        bak = info_from_auth_json(state["bak_file"])
        if bak:
            print(ui.info("原始配置备份已存在: auth.json.bak"))
            print(f"    （{bak['email']}，后续不再改动）")
    elif state["auth_exists"]:
        print(ui.info("首次运行，将现有 auth.json 保存为「原始配置备份」"))


def _run_env_check(codex_home: Path) -> None:
    while True:
        checks, has_fatal = env.run_all()
        print()
        print("环境检查:")
        print()
        for c in checks:
            if c.ok:
                suffix = f" ({c.message})" if c.message else ""
                print(f"  {ui.ok(c.name)}{suffix}")
            else:
                m = ui.err if c.level == "fatal" else ui.warn
                suffix = f" - {c.message}" if c.message else ""
                print(f"  {m(c.name)}{suffix}")
                if c.hint:
                    print(f"      修复建议: {c.hint}")

        print()
        _preview_existing(codex_home)
        print()

        if not has_fatal:
            return

        print(ui.err("存在致命错误，无法继续"))
        try:
            input("修复后按 Enter 重新检查，或 Ctrl+C 退出...")
        except (EOFError, KeyboardInterrupt):
            sys.exit(130)


def _write_with_fallback(auth_str: str, codex_home: Path,
                          reset_backup: bool, out_dir_override) -> int:
    """
    尝试写入 ~/.codex/auth.json；
    失败则降级生成到 codex-output/auth.json，并打印手动替换指引。
    返回 0 表示完整成功，1 表示降级/失败。
    """
    try:
        result = storage.write_auth(auth_str, codex_home, reset_backup)
    except StorageError as e:
        # ===== 降级：生成到 codex-output/ =====
        print(ui.err(str(e)))
        print()
        print(ui.warn("写入 ~/.codex/auth.json 失败，改为生成到 codex-output/"))
        print(ui.info("你可以手动复制到目标位置"))
        print()

        try:
            od = output_dir(out_dir_override)
            ensure_gitignore(od)
            fallback = od / "auth.json"
            fallback.write_text(auth_str, encoding="utf-8")
            if os.name == "posix":
                try:
                    os.chmod(fallback, 0o600)
                except OSError:
                    pass
            print(f"  {ui.ok(f'已生成: {fallback}')}")
        except Exception as e2:
            print(ui.err(f"生成到 codex-output/ 也失败: {e2}"))
            print()
            print("  请在可写目录下手动运行:")
            print(f'    python codex_auto.py --dry-run > auth.json')
            return 1

        target = codex_home / "auth.json"
        print()
        print(ui.divider())
        print("手动替换方法:")
        print()
        if sys.platform == "win32":
            print(f'  copy "{fallback}" "{target}"')
        else:
            print(f'  cp "{fallback}" "{target}"')
        print()
        print("  如果目标文件被占用（如 ChatGPT 应用正在运行），")
        print("  请先完全退出应用，再执行上面的命令。")
        print()
        print("  如果目标目录不存在或不可写:")
        print()
        if sys.platform == "win32":
            print(f'  mkdir "{codex_home}"')
        else:
            print(f'  mkdir -p "{codex_home}" && chmod 700 "{codex_home}"')
        print()
        print("  替换成功后，打开 ChatGPT 应用即可使用。")
        print(ui.divider())
        return 1

    # ===== 正常成功路径 =====
    af = result["auth_file"]
    print(f"  {ui.ok(f'已写入 {af}')}")
    if result["backup_created"]:
        print(f"  {ui.ok('原始配置备份已建立（后续不再改动）: auth.json.bak')}")
    elif result["backup_updated"]:
        print(f"  {ui.ok('备份已按 --reset-backup 更新')}")
    elif result["backup_existed"]:
        print(f"  {ui.ok('原始配置备份保持不变: auth.json.bak')}")
    return 0


def run(args) -> int:
    ui.init()

    print("Codex 免验证登录配置工具 v1.2.0")
    print(ui.divider())
    print("从本地已登录的 ChatGPT 抓取 session，写入 ~/.codex/auth.json")
    print("无需手机号验证，全程本地执行。")
    print()

    codex_home = (Path(args.codex_home).expanduser()
                  if args.codex_home else codex_home_dir())

    _run_env_check(codex_home)

    platform = args.platform or _platform_menu()
    print(ui.ok(f"已选择: {platform}"))

    raw = _get_session(args.method, args.session_file)
    if not raw:
        print(ui.err("未获取到内容"))
        return 1

    sess = session.parse(raw)
    if not sess:
        print(ui.err("无法解析 session"))
        return 1

    try:
        data = auth_data.build(sess)
    except AuthDataError as e:
        print(ui.err(str(e)))
        return 1

    _print_session_preview(data)

    try:
        ans = input("继续？[Y/n]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n" + ui.warn("已取消"))
        return 130
    if ans == "n":
        print(ui.warn("已取消"))
        return 0

    # ===== 平台 1/2：直接写 ~/.codex/auth.json（失败时降级） =====
    if platform in ("auto-unix", "windows"):
        auth_str = builders.auth_json(data)

        if args.dry_run:
            print(auth_str)
            return 0

        print()
        print("正在写入...")
        rc = _write_with_fallback(auth_str, codex_home,
                                   args.reset_backup, args.out_dir)

        print()
        print(ui.divider())
        if rc == 0:
            print("下一步:")
            print()
            print("  打开 ChatGPT 应用（如已打开，请完全退出后重新启动）")
            print()
            print("  无需手机号验证，直接开始使用。")
            print()
            print("提示:")
            if data["expiresAt"]:
                print(f"  · auth.json 有效期至 {data['expiresAt']}")
            print("  · 过期后重新运行本脚本即可刷新")
            print("  · 回退到原始配置: python codex_restore.py")
        else:
            print(ui.warn("写入未完成，已生成可手动替换的文件（见上方指引）"))
        print(ui.divider())
        return rc

    # ===== 平台 3-6：输出到 codex-output/ =====
    content_map = {
        "emit": lambda d: builders.unix_script(builders.auth_json(d)),
        "cpa": builders.cpa,
        "sub2api": builders.sub2api,
        "cockpit": builders.cockpit,
    }
    content = content_map[platform](data)

    if args.dry_run:
        print(content)
        return 0

    od = output_dir(args.out_dir)
    ensure_gitignore(od)
    fname = {
        "emit": "setup_codex.sh",
        "cpa": "cpa_account.json",
        "sub2api": "sub2api_export.json",
        "cockpit": "cockpit_account.json",
    }[platform]
    out_file = od / fname
    out_file.write_text(content, encoding="utf-8")
    print(f"  {ui.ok(f'已生成: {out_file}')}")

    print()
    print(ui.divider())
    print("下一步:")
    print()
    print("  按该平台的使用说明导入生成的文件")
    print(ui.divider())
    return 0