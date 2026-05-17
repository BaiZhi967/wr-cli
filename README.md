<div align="center">

# 📚 wr-cli

**微信读书命令行工具**

将微信读书官方 Skill 提供的 API 封装为开箱即用的 CLI 命令

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-53%20cases-brightgreen.svg)](tests/)

[English](#english) · [功能](#-功能简介) · [快速开始](#-快速开始) · [命令详解](#-命令总览) · [参考文档](#-参考文档)

</div>

---

> **API Key 获取**：前往 [微信读书 Skills 官方页面](https://weread.qq.com/r/weread-skills) 申请。

## 🤔 为什么需要 wr-cli

微信读书 Agent API 是面向 AI agent 设计的接口，调用时需要遵循一系列规范（每次请求携带 `skill_version`、参数扁平化、检查 `errcode` 和 `upgrade_info` 等）。agent 直接调用 API 存在几个问题：

- **调用成本高**：每次请求数据，agent 都要重新阅读 API 文档、构造请求体、处理鉴权和错误码，消耗大量上下文和 token
- **规则容易遗漏**：API 要求每次请求必须携带 `skill_version`、参数必须扁平化、必须检查 `errcode` 和 `upgrade_info`，agent 手动操作时容易遗漏
- **数据需要二次处理**：API 返回的是原始数据（Unix 时间戳、秒数、星级数字），agent 每次都要编写格式化逻辑（时间转换、进度条生成、深链拼接）
- **结果不可复用**：agent 通过 curl 获取的数据仅存在于对话中，无法导出为文件供后续流程使用

wr-cli 将这些逻辑固化到代码中，agent 只需执行一行命令即可完成「调用 → 处理 → 格式化 → 导出」的全流程。

## ✨ 功能简介

8 个子命令，覆盖微信读书主要数据接口：

| 命令 | 说明 | 示例 |
|------|------|------|
| `search` | 搜索书籍/有声书 | `search "深度学习"` |
| `shelf` | 获取书架 | `shelf --per-page 10` |
| `book` | 查看书籍详情、目录、阅读进度 | `book 834464 --chapters` |
| `notes` | 查看笔记本、书签、划线、书评 | `notes --book 834464` |
| `readdata` | 获取阅读数据（周/月/年/总计） | `readdata --mode weekly` |
| `review` | 获取公开书评 | `review 7190022` |
| `discover` | 获取推荐书单和相似书籍 | `discover --book 834464` |
| `list-apis` | 列出所有可用 API 及参数 | `list-apis` |

所有数据命令均支持 `--output/-o` 导出，格式支持 JSON / CSV / TSV / Markdown / 纯文本。

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/BaiZhi967/wr-cli.git
cd wr-cli
```

### 配置

```bash
# 方式一：设置环境变量
export WEREAD_API_KEY="wrk-xxxxxxxx"

# 方式二：在项目根目录创建 .env 文件
echo 'WEREAD_API_KEY="wrk-xxxxxxxx"' > .env
```

### 使用

```bash
# 搜索书籍
python scripts/weread.py search "深度学习"

# 获取本周阅读数据并导出为 JSON
python scripts/weread.py readdata --mode weekly -o weekly.json

# 查看书架并导出为 CSV
python scripts/weread.py shelf -o shelf.csv

# 查看某本书的笔记和划线
python scripts/weread.py notes --book 834464 -o notes.md
```

## 📖 命令总览

```bash
WR_CLI=scripts/weread.py

# 搜索：支持电子书、有声书、作者等 scope
$WR_CLI search <关键词> [--scope 10] [--count 20] [--page 1] [--per-page 10] [-o result.json]

# 书架：含书籍、有声书、公众号分组计数
$WR_CLI shelf [--page 1] [--per-page 10] [-o shelf.csv]

# 书籍：详情 + 目录 + 阅读进度
$WR_CLI book <bookId> [--progress] [--chapters] [--chapters-page 1] [-o book.json]

# 笔记：划线 + 想法 + 书签
$WR_CLI notes [--book <bookId>] [--page 1] [--per-page 10] [--max-pages 5] [-o notes.tsv]

# 阅读统计：周报/月报/年报/总计
$WR_CLI readdata [-m monthly|weekly|annually|overall] [-t 0] [-o stats.json]

# 公开点评
$WR_CLI review <bookId> [--type 0] [--page 1] [--per-page 10] [-o reviews.md]

# 推荐 / 相似书籍
$WR_CLI discover [--book <bookId>] [--page 1] [--per-page 10] [-o discover.csv]

# 列出可用接口
$WR_CLI list-apis
```

导出格式按文件扩展名自动识别：

| 扩展名 | 格式 | 说明 |
|--------|------|------|
| `.json` | JSON | Pretty-print，嵌套结构完整保留 |
| `.csv` | CSV | 逗号分隔，全字段引号包裹 |
| `.tsv` | TSV | Tab 分隔 |
| `.md` | Markdown | Markdown 表格 |
| `.txt` | 纯文本 | 键值对文本 |

## 🧪 运行测试

```bash
python3 -m pytest tests/test_weread.py -v
```

## 📁 项目结构

```
wr-cli/
├── SKILL.md              # CLI skill 定义（给 AI agent 的使用说明）
├── README.md             # 本文件
├── references/           # API 字段参考文档
├── scripts/
│   ├── weread.py         # 入口
│   └── _weread/
│       ├── api.py        # API 客户端（鉴权、版本上报、错误处理）
│       ├── cli.py        # 命令行参数解析
│       ├── constants.py  # API 地址与版本号
│       ├── utils.py      # 工具函数（时间格式化、深链生成等）
│       ├── export.py     # 多格式导出
│       ├── search.py     # 搜索
│       ├── shelf.py      # 书架
│       ├── book.py       # 书籍
│       ├── notes.py      # 笔记
│       ├── readdata.py   # 阅读数据
│       ├── review.py     # 书评
│       └── discover.py   # 发现/推荐
└── tests/
    └── test_weread.py    # 53 个测试用例
```

## ⚠️ 已知 API 陷阱

| 陷阱 | 说明 | CLI 对策 |
|------|------|----------|
| `newRating` 是 0-1000 | 如 930 = 93%，不是百分制 | 自动除以 10 展示 |
| `star` 可能是 float | `100.0` 而非 `100` | `int()` 后再整除 |
| review 不传 count/maxIdx 会空 | 只返回统计摘要 | 自动传参 |
| notebooks 全量拉取可能超时 | 书架 2000+ 本时 | 默认限 5 页，`--max-pages` 调整 |
| `skill_version` 要同步 | 常量和 SKILL.md 版本号要一致 | 改版时一起改 |

## 📄 参考文档

API 字段含义和工作流细节，CLI 已实现，仅供理解参考：

| 文档 | 内容 |
|------|------|
| [references/search.md](references/search.md) | 搜索 scope 选择、字段说明 |
| [references/shelf.md](references/shelf.md) | 书架结构、数量口径、公开/私密规则 |
| [references/book.md](references/book.md) | 书籍信息、章节目录、阅读进度字段 |
| [references/notes.md](references/notes.md) | 笔记统计口径、划线、想法、热门划线 |
| [references/review.md](references/review.md) | 公开点评字段与类型 |
| [references/readdata.md](references/readdata.md) | 阅读统计字段单位、周期组合 |
| [references/discover.md](references/discover.md) | 推荐接口字段说明 |
| [references/profile.md](references/profile.md) | 用户概况组合查询 |

## 🛠 逃生口

CLI 覆盖不到的场景，可以直接用 `WereadAPI` 类：

```bash
cd scripts && python3 -c "
import weread, json
api = weread.WereadAPI()
result = api.call('/shelf/sync')
print(json.dumps(result, indent=2, ensure_ascii=False))
"
```

用完即弃。如果某个功能反复用到，应该加进 CLI 子命令。

## 📜 License

[MIT](LICENSE)

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐️ Star 支持一下！**

</div>
