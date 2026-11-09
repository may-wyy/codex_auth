# codex-auth

> 从已登录的 ChatGPT 默认浏览器会话生成 `~/.codex/auth.json`，绕过 Codex 客户端的手机号验证环节。

---

## ⚠️ 先读这段

- **非官方工具**。仅用于把你自己账号的浏览器登录态，转换成本地 Codex 客户端可读取的 `auth.json`。
- **不包含 `refresh_token`**。生成的文件有效期跟随 `accessToken`**（自测 10 天），到期后需要重新运行本脚本。**这是 ChatGPT 网页 session 的固有限制，不是 bug。
- **请只用于自己的账号**。不要分享生成的 `auth.json`，它包含你的账户凭证。
- 使用本工具产生的任何后果由使用者自行承担。

---

## 它是怎么工作的

```
默认浏览器已登录 chatgpt.com
        │
        │  打开 /api/auth/session，复制返回的 JSON
        ▼
   本脚本解析 accessToken (JWT)
        │
        │  提取 account_id / email / plan / exp
        │  组装成 Codex 客户端可读的 auth.json
        ▼
  写入 ~/.codex/auth.json
        │
        │  重启 ChatGPT 应用
        ▼
   无需手机号验证，直接使用
```

**关键点**：浏览器 session 里的 `accessToken` 是 ChatGPT 网页端的长效令牌（不是 OAuth 流程的 1 小时令牌），Codex 客户端只校验它是否有效、`account_id` 是否匹配，**不校验 `id_token` 签名，也不校验 `refresh_token` 真伪**——所以只用 `accessToken` 就够了。

---

## 快速开始

### 环境要求

- **Python 3.7+**（仅使用标准库，无需 `pip install`）
- 一个**已登录的 ChatGPT 浏览器会话（默认浏览器）**（Chrome / Edge / Firefox 均可）

### 三步走

```bash
# 1. 下载
git clone https://github.com/may-wyy/codex_auth.git
cd codex-auth

# 2. 运行
python codex_auto.py

# 3. 按提示操作
#    - 选择平台（默认会选中你当前的系统）
#    - 浏览器会自动打开 session 页面（使用的是默认浏览器）
#    - Ctrl+A 全选 → Ctrl+C 复制 → 回终端按 Enter
#    - 确认信息 → 自动写入
```

完成后，**完全退出 ChatGPT 应用再重新打开**，即可免验证使用。

Windows 用户注意：命令是 `python`，不是 `python3`。

---

## 两个命令

### `codex_auto.py` — 生成 / 刷新 `auth.json`

```bash
python codex_auto.py
```

交互式流程，跟提示走即可。常用参数：

| 参数                                                      | 说明                                      |
| --------------------------------------------------------- | ----------------------------------------- |
| `--platform {auto-unix,windows,cpa,sub2api,cockpit,emit}` | 跳过菜单，直接指定平台                    |
| `--method {auto,clipboard,stdin}`                         | session 获取方式（默认：剪贴板）          |
| `--session-file PATH`                                     | 从文件读取 session（无交互）              |
| `--codex-home PATH`                                       | 替代默认的 `~/.codex`                     |
| `--out-dir PATH`                                          | 替代默认的 `codex-output/`                |
| `--reset-backup`                                          | 把当前 `auth.json` 更新为新的「原始备份」 |
| `--dry-run`                                               | 只打印结果，不写入任何文件                |

示例：

```bash
# 完全非交互（适合脚本化）
python codex_auto.py --platform auto-unix --session-file session.json

# 只预览，不写文件
python codex_auto.py --dry-run

# 生成 CPA 面板的账号 JSON（不写 auth.json）
python codex_auto.py --platform cpa
```

### `codex_restore.py` — 回退到原始配置

```bash
python codex_restore.py
```

把 `~/.codex/auth.json.bak`（原始配置）复制回 `auth.json`，`.bak` 本身保持不变。

| 参数                | 说明                                    |
| ------------------- | --------------------------------------- |
| `--info`            | 只显示状态，不执行恢复                  |
| `--yes`             | 跳过确认                                |
| `--no-save-current` | 不保存当前为 `auth.json.before-restore` |

---

## 备份策略

| 文件                                | 何时创建                                | 何时更新                          | 作用                       |
| ----------------------------------- | --------------------------------------- | --------------------------------- | -------------------------- |
| `~/.codex/auth.json`                | 每次运行主程序                          | 每次运行覆盖                      | 当前生效的配置             |
| `~/.codex/auth.json.bak`            | **首次运行主程序且有旧 `auth.json` 时** | **永不**（除非 `--reset-backup`） | 保留"最初原状"，随时可回退 |
| `~/.codex/auth.json.before-restore` | 每次执行回退                            | 每次覆盖                          | 回退时的临时快照           |

**核心规则**：`.bak` 一旦建立就**永不改动**。无论你中间切换了多少次账号、刷新了多少次 token，`python codex_restore.py` 都能把你带回第一次使用本工具前的状态。

---

## 输出的文件在哪

| 平台选择            | 产物位置                                                    |
| ------------------- | ----------------------------------------------------------- |
| `[1] macOS / Linux` | `~/.codex/auth.json`（即 `/home/<你>/.codex/auth.json`）    |
| `[2] Windows`       | `~/.codex/auth.json`（即 `C:\Users\<你>\.codex\auth.json`） |
| `[3] CPA`           | `codex-output/cpa_account.json`                             |
| `[4] Sub2API`       | `codex-output/sub2api_export.json`                          |
| `[5] Cockpit`       | `codex-output/cockpit_account.json`                         |
| `[6] 仅输出脚本`    | `codex-output/setup_codex.sh`                               |

`codex-output/` 默认在工程根目录下，不可写时降级到 `~/codex-output/`。传 `--out-dir` 可自定义。

如果设置了 `CODEX_HOME` 环境变量，`~/.codex` 会变成 `$CODEX_HOME`——**请确保 ChatGPT 客户端也设置了同样的环境变量，否则它读不到你写的文件**。

---

## 支持的平台

| 平台    | 读 session                      | 写 auth.json | 其他产物    |
| ------- | ------------------------------- | ------------ | ----------- |
| Windows | ✅ PowerShell 剪贴板             | ✅            | `.bat` 脚本 |
| macOS   | ✅ `pbpaste`                     | ✅            | `.sh` 脚本  |
| Linux   | ✅ `xclip` / `wl-paste` / `xsel` | ✅            | `.sh` 脚本  |

Linux 上如果三种剪贴板工具都没装，会自动降级到手动粘贴（`--method stdin`）。

---

## 常见问题

### Q: 为什么 `refresh_token` 是 `rt_mock_token`？

因为**浏览器 session 里根本没有真正的 `refresh_token`**。它是 OAuth 授权流程的产物，网页 session 接口不提供。所以 `auth.json` 里的 `refresh_token` 只是占位符——**它不能让 Codex 自动续期**。

### Q: 过期了怎么办？

重新运行一次 `python codex_auto.py`。浏览器里你通常仍是登录状态，所以整个过程是 3 个按键（`Ctrl+A`、`Ctrl+C`、`Enter`），大约 15 秒。

### Q: 能拿到真正可自动续期的 `refresh_token` 吗？

理论上可以，但**必须走 OAuth 授权流程**（`offline_access` scope），而且 Codex 的 OAuth 通道会要求手机验证——这正是本工具想绕开的那一步。**本工具不提供这条路径**。如果对自动续期有强烈需求，请自行研究 OAuth 流程。

### Q: 我是免费账号，能用吗？

**能生成 `auth.json`**，但 Codex 的部分功能可能对免费账号有限制，即使文件写对了也可能无法完整使用。这是 OpenAI 侧的策略，与本工具无关。

### Q: 写入失败了怎么办？

脚本会自动降级到 `codex-output/auth.json`，并打印 `copy`/`cp` 命令供你手动替换。最常见的失败原因是：

- **Windows**：ChatGPT 应用正在运行，锁着 `auth.json` → 先完全退出应用
- **Unix**：`~/.codex` 权限不对 → `mkdir -p ~/.codex && chmod 700 ~/.codex`
- **任意平台**：磁盘满 → 清理空间

### Q: 支持修改 `~/.codex` 的位置吗？

```bash
# 通过环境变量
export CODEX_HOME=/opt/codex   # Unix
set CODEX_HOME=D:\codex        # Windows CMD
$env:CODEX_HOME="D:\codex"     # Windows PowerShell

# 或通过参数
python codex_auto.py --codex-home /opt/codex
```

**两边要一致**（脚本和 ChatGPT 客户端），否则客户端读不到。

### Q: 会修改 `~/.codex` 里的其他文件吗？

**不会**。脚本只碰 `auth.json` 和 `auth.json.bak`。Codex 的 `config.toml`、`sessions/`、`log/` 等一概不动。

### Q: 会不会有安全风险？

- `auth.json` 包含你的 `accessToken`，**等同于你的登录凭证**，请勿分享
- 脚本**不联网**（除了打开浏览器），**不上传任何数据**
- 生成的 `auth.json` 权限设置为 `600`（Unix），仅当前用户可读
- `codex-output/` 会自动生成 `.gitignore`（内容 `*`），避免误提交到仓库

---

## 目录结构

```
codex-auth/
├── README.md
├── .gitignore
├── codex_auto.py            # 主程序入口
├── codex_restore.py         # 回退入口
└── cxauth/                  # 核心包
    ├── __init__.py
    ├── paths.py             # 路径解析（~/.codex、codex-output）
    ├── ui.py                # 终端颜色与样式
    ├── token.py             # JWT 解码
    ├── session.py           # session 解析
    ├── auth_data.py         # 身份提取
    ├── builders.py          # 各平台输出生成器
    ├── storage.py           # 写入 + 备份 + 恢复
    ├── clipboard.py         # 跨平台剪贴板
    ├── env.py               # 环境检查
    ├── cli_auto.py          # 主程序交互
    └── cli_restore.py       # 回退交互
```

---

## 免责声明

本项目仅供学习与个人使用。

- 不保证与 OpenAI 未来的接口变更保持兼容
- 不鼓励、不支持任何违反 OpenAI 服务条款的行为
- 使用本工具即表示你了解并接受上述风险，作者不对任何直接或间接损失负责
- 如果你的账号因使用本工具出现问题，作者不承担任何责任

## License

[MIT](./LICENSE) © 2026 may-wyy