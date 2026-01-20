# oh-my-writing-skill

<p align="center">
  <img src="demo.png" width="400" height="auto"/>

<p align="center">
  基于 Claude Agent Skills 构建的智能内容创作助手，支持自动化研究、配图、写作和多平台格式转换。
</p>

## 功能特性

- 🔍 **深度研究**：使用 ddgs + DuckDuckGo 获取背景资料，无需 API Key
- 🖼️ **智能配图**：使用 ddgs + DuckDuckGo 搜索和下载相关图片，无需 API Key
- ✍️ **内容创作**：生成高质量的 AI 创作内容
- 🤖 **AI人性化**：优化 AI 生成痕迹，使内容更自然
- 📱 **多平台适配**：一键转换为知乎、小红书、微信公众号文章风格

## 项目结构

```
.claude/
└── skills/
    ├── content-creator/            # 主协调器（Skill，用户手动调用）
    ├── deep-research/              # 网络搜索（后台 Skill）
    ├── image-search/               # 图片搜索（后台 Skill）
    ├── image-processing/           # 图片处理（后台 Skill）
    ├── general-writing/            # 通用写作（后台 Skill）
    ├── humanizer-cn/               # 中文人性化（后台 Skill）
    ├── zhihu-converter/            # 知乎转换（后台 Skill）
    ├── xiaohongshu-converter/      # 小红书转换（后台 Skill）
    └── wechat-converter/           # 微信公众号转换（后台 Skill）
```

## 安装

1. 克隆项目并进入目录

```bash
cd writing-skill
```

2. 创建、激活虚拟环境并安装依赖

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

## 使用方法

在 Claude Code 中加载此工作区，然后使用 `/content-creator` 命令：

```
/content-creator 「酱油」一词为什么正在被「生抽」和「老抽」替代？发知乎和小红书。
```

说明：

- `content-creator` 是主入口 Skill，需要手动调用（`disable-model-invocation: true`）
- 8 个子 Skills（deep-research、image-search 等）是后台能力，不会出现在菜单（`user-invocable: false`）
- Claude 会在 content-creator 内部自动协调这些子 Skills

## 工作流程

```mermaid
graph TD
    A[用户需求] --> B[需求确认]
    B --> C{需要研究?}
    C -->|是| D[深度研究<br/>deep-research]
    C -->|否| E[内容创作<br/>general-writing]
    D --> E
    E --> F{需要配图?}
    F -->|是| G[图片搜索<br/>image-search]
    F -->|否| I[人性化优化<br/>humanizer-cn]
    G --> H[图片处理<br/>image-processing]
    H --> I
    I --> J{目标平台}
    J -->|知乎| K[知乎格式转换<br/>zhihu-converter]
    J -->|小红书| L[小红书格式转换<br/>xiaohongshu-converter]
    J -->|微信| M[微信格式转换<br/>wechat-converter]
    K --> N[最终输出]
    L --> N
    M --> N

    style A fill:#e1f5ff
    style N fill:#e8f5e9
    style D fill:#fff3e0
    style G fill:#fff3e0
    style H fill:#fff3e0
    style E fill:#fff3e0
    style I fill:#f3e5f5
    style K fill:#fce4ec
    style L fill:#fce4ec
    style M fill:#fce4ec
```

## 示例展示

- ["酱油"一词为什么正在被"生抽"和"老抽"替代？](examples/酱油词汇演变)
- [把下班后的时间都用来刷手机，对人生对生活究竟有没有影响？](examples/下班后刷手机影响)

每个示例包含完整的输出文件：

- `research*.md` - 研究资料
- `draft.md` - 初始草稿
- `humanized.md` - 人性化优化版本
- `zhihu.md` / `xiaohongshu.md` / `wechat.md` - 平台适配版本
- `images/` - 配图资源

## License

MIT
