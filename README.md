# penguin-plugins

PenguinHarness 的插件集合。**一个目录 = 一个插件**，目录名就是插件名。

这个仓库不是 PenguinHarness 本体的一部分，只是插件的分发点：把插件目录放进来，别人就能在 PenguinHarness 的「插件目录」里用一条 URL 直接装走。

## 插件

| 插件 | 版本 | 说明 |
| --- | --- | --- |
| [`wechat-miniprogram`](wechat-miniprogram) | 2026.10.01.1 | 在无桌面的 Linux 服务器上把微信小程序从代码做到发布：扫码登录 mp.weixin.qq.com、从公众号后台切到小程序后台、取 AppID 与上传密钥、加 IP 白名单、用 miniprogram-ci 上传、交付校验过的预览码、填写必填的用户隐私保护指引、提交审核与发布。 |
| [`csu-mail`](csu-mail) | 2026.10.02.3 | 绕开统一身份认证管理 Coremail 邮箱（中南大学学生邮箱）：生成客户端专用密码，用 IMAP/SMTP 从命令行查信、检索、读信、发信，并在「已发送」留底；附 CAS 引导脚本与网页接口要点。 |
| [`lesson-video`](lesson-video) | 2026.10.06.1 | 把讲稿做成竖屏教学视频（1080×1920）与配套封面：HTML 课件按时间轴逐帧定格、edge-tts 逐词对齐配音、Playwright 截图、ffmpeg 合成，两侧与上部按手机 App 按钮留安全区，渲染前先自检越界/裁切/孤字标题，并给出标签不超过五个的发布文案。 |

版本号由各插件自己的 `plugin.json` 维护（`YYYY.MM.DD.N`），与仓库的提交历史无关——同一仓库里的插件各按自己的节奏发版。

## 安装

### 方式一：从仓库 URL 安装（推荐）

在 PenguinHarness 的「插件目录」页面填 GitHub 的 **tree 子目录 URL**，一个插件一条：

```
https://github.com/lmliheng/penguin-plugins/tree/main/wechat-miniprogram
https://github.com/lmliheng/penguin-plugins/tree/main/csu-mail
https://github.com/lmliheng/penguin-plugins/tree/main/lesson-video
```

**用 tree URL，不要用仓库根 URL。** 两种都能装，但插件名取法不同：

- tree URL 的插件名 = URL 最后一段目录名 → 装成 `wechat-miniprogram` ✓
- 仓库根 URL 的插件名 = 仓库名 → 会装成 `penguin-plugins` ✗（除非在界面的「插件名」输入框里手填）

下载器只取 `plugin.json` 所在的那个目录子树：tree URL 按 URL 里的子目录定位；填仓库根 URL 时取归档里最浅的那个 `plugin.json`（本仓库就是 `wechat-miniprogram/`）。整仓下载到 32MB 上限，本仓库归档只有 70KB。

### 方式二：本地上传 zip

把某个插件目录打成 zip（**顶层目录名必须是插件名**，例如 `wechat-miniprogram/`），在「插件目录」页面上传，上限 14MB。本仓库的插件都在 300KB 以内。

### 方式三：直接放目录

把插件目录拷到 `<app_data_dir>/plugins/<插件名>/` 下，刷新页面即可。适合本机开发调试。

## 仓库结构

```
penguin-plugins/
├── README.md                 # 你正在看的这个文件（在插件目录之外，不影响按 tree URL 安装单个插件）
└── wechat-miniprogram/       # 一个插件 = 一个目录，目录名即插件名
    ├── plugin.json           # 插件清单：描述、版本、preinstall
    ├── icon.svg              # 图标
    ├── package.json          # npm 元数据（仅用于包管理，不参与安装）
    └── skills/
        └── wechat-miniprogram/
            ├── SKILL.md      # 技能说明：何时用、怎么做、坑在哪
            ├── scripts/      # 可执行脚本
            └── templates/    # 模板项目
```

`plugin.json` 是插件被识别的唯一依据，字段：

```json
{
  "description": "英文描述（给模型看）",
  "description_zh": "中文描述",
  "short_description": "英文短描述",
  "short_description_zh": "中文短描述",
  "version": "2026.10.01.1",
  "preinstall": false
}
```

装插件时 PenguinHarness 会把 `skills/` 下的技能挂到目标 Agent 上。所以 **`skills/` 里的 `SKILL.md` 要自带 frontmatter 的 `name` / `description`**，`scripts/` 里的脚本用相对路径互相引用（`./stealth.mjs`），装完即用，不要依赖仓库外的绝对路径。

## 新增一个插件

在仓库根建一个目录，目录名就是插件名，把 `plugin.json`、`icon.svg`、`skills/` 放进去，提交推送。安装时用 `https://github.com/lmliheng/penguin-plugins/tree/main/<插件名>`。

**插件本身该长什么样、哪些东西不能写进去，不写在仓库里，写在产品里**：见 PenguinHarness 插件库「插件目录」界面的「插件编写规则」——一个目录一个插件、目录名即插件名、不写死账号信息、不提交密钥。规则放那儿，是因为写插件的人看着的是那个界面，而且插件会比它被发布的仓库活得久。

## 关于 npm

本仓库的插件也可以发到 npm（`package.json` 已经备好 `files` / `publishConfig`），但 **PenguinHarness 的插件安装不认 npm**：远程下载只接受 zip 直链和 GitHub 仓库 / tree 子目录 URL。所以 npm 是分发渠道的补充，不是安装方式——真要发，需要先把 `package.json` 里的 scope 从上游的 `@penguinharness` 改成本账号。

## License

Apache-2.0
