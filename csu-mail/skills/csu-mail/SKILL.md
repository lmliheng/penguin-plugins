---
name: csu-mail
description: Manage a Coremail mailbox (CSU student mail, mail.csu.edu.cn) over IMAP/SMTP with an app password instead of the unified auth portal — create the app password once, then list, search, read and send mail from the shell, with a copy kept in the Sent folder. Use whenever the task involves checking, sending or automating email on a CSU mailbox, or when a CAS login must be avoided.
short_description: Coremail mailbox over IMAP/SMTP with an app password, no CAS.
short_description_zh: Coremail 邮箱免 CAS 收发信：专用密码 + IMAP/SMTP。
version: 2026.10.02.1
---

# 中南大学邮箱管理（Coremail，绕开统一身份认证）

## 结论先行

| 事项 | 做法 |
| --- | --- |
| 收发信 | **客户端专用密码 + IMAP/SMTP**，不要为了邮件去登录统一身份认证（CAS） |
| 没有专用密码 | 只做一次 CAS 引导（`cas_login.py` → `create_apppw.mjs`），此后永久脱离 CAS |
| 为什么 | 短时间高频登录 CAS 会触发风控、甚至冻结账号（2026-10-02 真实发生过一次） |
| 留底 | 用 SMTP 发信并 `APPEND` 到「已发送」；网页接口 `mbox:compose` **不留底** |

## 一、系统事实（实测）

| 项 | 值 |
| --- | --- |
| 邮件系统 | Coremail XT5，网页入口 `https://mail.csu.edu.cn` |
| 地址 | `学号@csu.edu.cn`，另有别名 `拼音.csu@csu.edu.cn`，两者是同一邮箱 |
| 二次验证 | 已开启（短信验证），所以第三方客户端只能用**客户端专用密码** |
| IMAP | `imap.csu.edu.cn:993` SSL（`mail.csu.edu.cn:993` 同样可用） |
| POP | `pop.csu.edu.cn:995` SSL |
| SMTP | `smtp.csu.edu.cn:465` SSL；**587 关闭、25 不通** |
| IMAP 证书 | CN 与主机名不匹配，必须跳过证书校验，否则 `SSL: CERTIFICATE_VERIFY_FAILED` |

认证的边界（都实测过）：

- 统一身份认证密码**不能**登录 IMAP → `LOGIN Login error or password error`
- 网页直登 `/coremail/index.jsp?cus=1`（明文 `uid`+`password`）→ `FA_UNAUTHORIZED`，还会弹验证码
- 结论：第三方客户端只有**客户端专用密码**这一条路

## 二、首次引导：生成一条客户端专用密码

1. 网页邮箱 → `设置 → 个人信息 → 邮箱密码` →「客户端专用密码」区块 → 点**虚线方框 “+”** → 填密码名称 →「生成」。
   **不需要短信验证**，但密码串**只在生成时显示一次**；丢了就在同一页面「移除」后重建。
2. 后端接口（想自动化时用）：`user:listAppPwds`（列表）、`user:addAppPwd`（创建，响应里带明文）、
   `user:deleteAppPwds`（`{"ids":[102]}`）。请求走 `/coremail/s`，**`func` 与 `sid` 必须在 query string**。
3. 本插件的脚本：

```bash
# ① CAS 登录换 sid（只做一次）
CSU_MAIL_ADDR=学号@csu.edu.cn CSU_CAS_USER=学号 CSU_CAS_PASS=密码 \
  python scripts/cas_login.py --out mail_session.json          # 产出 600 权限的 sid + cookies

# ② 驱动网页邮箱生成专用密码（需要 Playwright）
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright-core \
CHROME_PATH=/path/to/chrome \
  node scripts/create_apppw.mjs mail_session.json agent-server --out secret.txt

# ③ 存进密钥库并删掉明文
penguin config vault set --key CSU_MAIL_AUTHCODE --value "$(cat secret.txt)" && shred -u secret.txt
penguin config vault set --key CSU_MAIL_ADDR --value "学号@csu.edu.cn"
```

> 引导用的 CAS 登录**不要重试**：失败就停下来问用户，别连续试密码。

## 三、日常收发信：`scripts/mail.py`

```bash
export CSU_MAIL_ADDR=学号@csu.edu.cn CSU_MAIL_AUTHCODE=专用密码   # 或从密钥库注入
V=python3

$V scripts/mail.py check                     # IMAP + SMTP 自检
$V scripts/mail.py list INBOX 10             # 最近 10 封
$V scripts/mail.py list "Sent Items" 5       # 含空格的文件夹要加引号
$V scripts/mail.py read 124                  # 读一封（正文）
$V scripts/mail.py search 成绩                # 按标题检索
$V scripts/mail.py send --to jcc@csu.edu.cn --subject "..." --body-file body.txt
                                             # 发信，并自动存一份到「已发送」
```

依赖：`requests`（只有 `mail.py` 的核心收发用标准库 `imaplib`/`smtplib`/`email`，无需三方包）。

## 四、踩过的坑

1. **「生成」按钮初始是 `disabled`**，弹出框里的密码名称输入框必须用**真实键盘事件**输入
   （Playwright 的 `fill()` 不行，要 `click()` + `keyboard.type()`），否则点了没反应、也不报错。
2. **专用密码只显示一次**：生成后立刻写进密钥库；密钥库变量在**会话开始**时注入，本次会话新加的变量要等下一次对话才可见。
3. **网页接口发信不留底**：`mbox:compose` 返回 `S_OK`，但「已发送」里查不到，事后无法核实送达。
   要留底就用 SMTP 发送 + `IMAP APPEND` 到 `Sent Items`（本插件的 `mail.py send` 就是这么做的）。
4. **文件夹名含空格要加引号**（`"Sent Items"`），否则 IMAP 报 `BAD Request not ending with ...`。
5. **中文 `SEARCH SUBJECT` 命中不稳定**：查不到时改用 `list` 翻页，别下结论说「没有这封邮件」。
6. 网页 API 的 `func` / `sid` 必须放在 **query string**，其余字段放 form body，否则 202/失败。
7. IMAP 证书 CN 不匹配，连接时必须 `check_hostname=False; verify_mode=CERT_NONE`。
8. **不要把账号、密码、专用密码写进代码或提交进仓库**——凭证只放密钥库/环境变量。

## 五、边界

- 本技能只覆盖**邮件**本身。Coremail 的通讯录、日程不在范围内。
- 代用户发信前先确认收件人与措辞；不要群发、不要发垃圾邮件。
- 邮箱是学校通知与个人信息的入口，读信时注意隐私，不要把邮件内容贴到无关的地方。
