# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**writing-skill** is a multi-platform content creation system for Claude Code. It provides modular Skills for end-to-end Chinese content creation - from research and image sourcing to writing, humanizing (removing AI traces), and platform-specific formatting for Zhihu, Xiaohongshu, and WeChat.

The system is built around:

- **Agent orchestration** via `content-creator` agent
- **8 Skills** for specialized tasks (research, image search/processing, writing, humanizing, platform conversion)
- **Python scripts** under each skill's `scripts/` directory for executable functionality
- **Platform-native output** that avoids AI detection patterns

## Environment Setup

```bash
# Using uv (recommended)
uv venv
uv pip install -r requirements.txt

# Or using standard pip
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

**Python version**: 3.10+ (see `.python-version`)

## Development Commands

### Running Skills Directly

Skills can be invoked via the `/skill` command (e.g., `/deep-research`) or their Python scripts can be run directly:

**Deep Research**

```bash
python .claude/skills/deep-research/scripts/research.py "选题" --max_results 20 --timelimit m --region zh-cn --output research.md
```

**Image Search**

```bash
python .claude/skills/image-search/scripts/image_search.py "关键词" --max_results 5 --size Large --download output/images
```

**Image Processing (add captions)**

```bash
# Frame mode (caption below image)
python .claude/skills/image-processing/scripts/image_processor.py input.jpg output.jpg --mode frame --text "配文"

# Sticker mode (caption overlay)
python .claude/skills/image-processing/scripts/image_processor.py input.jpg output.jpg --mode sticker --text "重点" --position bottom-right
```

## Architecture

### Agent Orchestration

The `content-creator` agent (`.claude/agents/content-creator.md`) orchestrates the 7-stage workflow:

1. **Requirement confirmation** - Uses `AskUserQuestion` to confirm stance, audience, style, platform targets, and **search mode**
2. **Deep research** - `deep-research` skill with dual search mode support (see below)
3. **Image sourcing** - `image-search` skill with filtering (size, color, license)
4. **Image processing** - `image-processing` skill for adding captions
5. **Content creation** - `general-writing` skill produces platform-agnostic "middle format" article
6. **AI-trace removal** - `humanizer-cn` skill eliminates 22+ AI writing patterns
7. **Platform conversion** - `zhihu-converter`, `xiaohongshu-converter`, or `wechat-converter`

### Search Modes

The `deep-research` skill automatically detects available search tools:

1. **WebSearch** - Claude's built-in search tool (native models)
2. **MCP Search Tools** - Vendor-provided search tools (e.g., `mcp__brave__web_search`, `mcp__tavily__search`)
3. **DDGS Fallback** - Uses ddgs Python library when no web search tool is available

| Search Method       | Tool                                  | Characteristics                |
| ------------------- | ------------------------------------- | ------------------------------ |
| **WebSearch**       | Claude built-in                       | High quality, most relevant    |
| **MCP Search**      | Vendor-provided (Brave, Tavily, etc.) | Custom model search capability |
| **DDGS** (fallback) | ddgs Python library                   | Free, no quota consumption     |

### Skill Structure

All Skills follow consistent conventions:

**Frontmatter** (YAML):

```yaml
---
name: skill-name
description: When to use this skill (English)
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob, AskUserQuestion]
metadata:
  author: writing-skill
  version: '1.0.0'
---
```

**Scripts** (in `scripts/` subdirectory):

- Shebang: `#!/usr/bin/env python3`
- UTF-8 encoding for Chinese content
- Graceful error handling with clear messages
- argparse for CLI interfaces

### Key Design Patterns

**Font Handling** (Windows-specific): Scripts auto-search for Chinese fonts in order:

1. `C:/Windows/Fonts/msyh.ttc` (微软雅黑)
2. `C:/Windows/Fonts/simhei.ttf` (黑体)
3. `C:/Windows/Fonts/simsun.ttc` (宋体)

**Content Pipeline**: Research → Images → Draft → Humanize → Convert → Platform

**Output Directory Structure**:

```
output/{日期}_{选题}/
├── research.md       # Research materials
├── draft.md          # Generic draft
├── humanized.md      # De-AI'd version
├── zhihu.md          # Zhihu version
├── xiaohongshu.md    # Xiaohongshu version
├── wechat.md         # WeChat version
└── images/           # Image resources
```

### Platform Conversion Styles

| Platform        | Style Characteristics                                                        |
| --------------- | ---------------------------------------------------------------------------- |
| **Zhihu**       | Professional, data-driven, logical, authority-building, structured arguments |
| **Xiaohongshu** | Casual, 1-2 emojis per section, visual-first, short-form, conversational     |
| **WeChat**      | Formal but approachable, well-formatted, depth-focused, narrative flow       |

### Dependencies

| Package              | Purpose                           |
| -------------------- | --------------------------------- |
| `ddgs` >= 9.0.0      | DuckDuckGo search API (DDGS mode) |
| `Pillow` >= 10.0.0   | Image processing                  |
| `requests` >= 2.28.0 | HTTP requests for image download  |

**Note**: WebSearch mode uses Claude's built-in WebSearch tool and requires no additional dependencies, but consumes MCP quota.

## Working with This Codebase

### Adding a New Skill

1. Create directory under `.claude/skills/skill-name/`
2. Add `SKILL.md` with proper frontmatter
3. Add `scripts/script_name.py` if executable functionality is needed
4. Register in `content-creator.md` agent's skills list if orchestration is needed
5. Add any new dependencies to `requirements.txt` and `pyproject.toml`

### Modifying Platform Conversion Rules

Platform-specific rules are in each converter's `SKILL.md`:

- `.claude/skills/zhihu-converter/SKILL.md`
- `.claude/skills/xiaohongshu-converter/SKILL.md`
- `.claude/skills/wechat-converter/SKILL.md`

These contain style guides, before/after examples, and transformation rules.

### AI Writing Pattern Detection

The `humanizer-cn` skill identifies 22+ AI-generated patterns specific to Chinese text. Patterns are documented in `.claude/skills/humanizer-cn/SKILL.md`.

## Quick Reference for Common Tasks

**"Help me write about X for Zhihu"** → Use `content-creator` agent (full pipeline)

**"Research topic X"** → Use `deep-research` skill only

**"Convert this article to Xiaohongshu format"** → Use `xiaohongshu-converter` skill

**"Remove AI traces from this text"** → Use `humanizer-cn` skill

**"Add captions to these images"** → Use `image-processing` skill
