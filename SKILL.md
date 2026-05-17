---
name: wr-cli
description: 微信读书 CLI — 搜索书籍、管理书架、查看笔记划线、浏览书评、阅读统计、发现推荐好书
---

# wr-cli — 微信读书 Python CLI

通过 `scripts/weread.py` 调用微信读书 Agent API Gateway，提供搜索、书架、笔记、书评、统计等全部能力。所有接口调用均通过 CLI 完成，不需要手动拼 curl。

CLI 已内置：鉴权、`skill_version` 版本上报、errcode/upgrade_info 检测、时长/时间戳/评分格式化、分页输出、`weread://` 深度链接。

> 需要 `WEREAD_API_KEY` 环境变量，或在项目根目录 `.env` 文件中配置。

## 命令总览

```bash
WR_CLI=scripts/weread.py

# 所有数据命令均支持 --output/-o 导出
$WR_CLI search <关键词> [--scope 10] [--page 1] [--per-page 10] [-o result.json]
$WR_CLI shelf [--page 1] [--per-page 10] [-o shelf.csv]
$WR_CLI book <bookId> [--progress] [--chapters] [--chapters-page 1] [-o book.json]
$WR_CLI notes [--book <bookId>] [--page 1] [--per-page 10] [--max-pages 5] [-o notes.tsv]
$WR_CLI readdata [--mode monthly|weekly|annually|overall] [--time 0] [-o stats.json]
$WR_CLI review <bookId> [--type 0] [--per-page 10] [-o reviews.md]
$WR_CLI discover [--book <bookId>] [--per-page 10] [-o discover.csv]
$WR_CLI list-apis
```

支持的导出格式：`.json`（默认 pretty-print）、`.csv`、`.tsv`、`.md`（Markdown 表格）、`.txt`（键值对文本）。未指定 `--output` 时按原有分页格式输出到终端。

## 子命令详解

### search — 搜索

```bash
$WR_CLI search 活着                           # 默认 scope=10 电子书
$WR_CLI search 活着 --scope 0                  # 综合
$WR_CLI search 活着 --scope 14                 # 有声书
$WR_CLI search 活着 --scope 6                  # 作者
$WR_CLI search 活着 --per-page 5 --page 2      # 分页
```

scope 取值：0=全部, 6=作者, 10=电子书, 14=有声书, 16=网文小说。详细指引见 `references/search.md`。

### shelf — 书架

```bash
$WR_CLI shelf --per-page 5 --page 1
```

输出：总条目数（books + albums + mp）、公开/私密统计、📖电子书/🎧有声书标记、置顶/读完/私密标签、最近阅读时间、`weread://` 链接。

### book — 书籍详情/目录/进度

```bash
$WR_CLI book 834464                           # 基本信息
$WR_CLI book 834464 --progress                # + 阅读进度
$WR_CLI book 834464 --chapters                # + 章节目录
$WR_CLI book 834464 --progress --chapters     # 全部
```

评分自动从 0-1000 转为百分制文字（神作/力荐/好评），字数超万自动转「万字」，时间戳转日期。

### notes — 笔记/划线/想法

```bash
$WR_CLI notes                                 # 笔记本概览（按笔记数排序）
$WR_CLI notes --max-pages 10                  # 多拉几页（默认5页=250本）
$WR_CLI notes --book 834464                   # 单本书：划线 + 个人想法
```

- 概览：书名、作者、进度、笔记总数（想法+划线+书签）
- 单本：划线按章节分组（附位置链接）、个人想法/点评

### readdata — 阅读统计

```bash
$WR_CLI readdata                              # 本月（默认）
$WR_CLI readdata --mode weekly                # 本周
$WR_CLI readdata --mode annually              # 本年
$WR_CLI readdata --mode overall               # 总计
$WR_CLI readdata --mode monthly --time 1735689600  # 历史月份
```

输出：阅读天数、总时长、日均、环比、统计摘要、读书排行 TOP5、偏好分类/时段/作者/出版社、勋章（年报）、好友排行（周报）。

### review — 公开点评

```bash
$WR_CLI review <bookId>                       # 全部
$WR_CLI review <bookId> --type 1              # 1=推荐 2=不行 3=最新 4=一般
```

输出：点评总数、资深会员推荐比例、每条点评的昵称/星级/内容摘要。

### discover — 推荐

```bash
$WR_CLI discover                              # 为你推荐
$WR_CLI discover --book <bookId>              # 相似书
```

### list-apis — 列出可用接口

```bash
$WR_CLI list-apis
```

## 数据导出

所有数据返回型命令（search / shelf / book / notes / readdata / review / discover）均支持 `--output <文件路径>` / `-o <文件路径>` 参数，将结果导出为本地文件：

```bash
$WR_CLI search 活着 -o search_results.json     # JSON（pretty-print）
$WR_CLI shelf -o shelf.csv                       # CSV（逗号分隔，全字段引号包裹）
$WR_CLI notes --book 834464 -o notes.tsv         # TSV（Tab 分隔）
$WR_CLI review 7190022 -o reviews.md             # Markdown 表格
$WR_CLI discover -o discover.txt                  # 纯文本键值对
$WR_CLI book 834464 --chapters -o chapters.csv   # 导出章节目录
```

导出行为：
- 按文件扩展名自动识别格式（.json / .csv / .tsv / .md / .txt）
- 嵌套结构（列表、字典）自动 JSON 序列化，兼容 CSV/TSV
- 指定 `--output` 后不再输出终端分页内容，只打印导出确认信息
- 不支持的扩展名会报错并退出

## CLI 覆盖不到时的逃生口

可以写临时 Python 脚本直接用 `WereadAPI` 类：

```bash
cd scripts && python3 -c "
import weread, json
api = weread.WereadAPI()
result = api.call('/shelf/sync')
print(json.dumps(result, indent=2, ensure_ascii=False))
"
```

用完即弃。如果某个功能反复用到，应该加进 CLI 子命令。

## Agent 工作流

1. **只用 CLI**：`$WR_CLI <command>` 是唯一调用方式。不写 curl，不直调 API。
2. **记 bookId**：搜索拿到 bookId 后记住，后续操作不用用户重复给书名。
3. **分页控篇幅**：默认 `--per-page 10`，数据多就 `--page N` 翻页。
4. **书名先搜**：用户给书名 → 先 `search` 拿 bookId → 再做后续。
5. **书架数量**：`books + albums + (mp非空?1:0)`，CLI 已内置。
6. **单位转换**：CLI 自动处理秒→小时分钟、时间戳→日期、评分 0-1000→百分制。
7. **报错处理**：先检查 API Key 是否有效；遇 upgrade_info 按指引升级。
8. **数据导出**：用户要保存数据时用 `--output/-o`，按所需格式选扩展名（.json/.csv/.tsv/.md/.txt）。

## 参考文档

API 字段含义和工作流细节，CLI 已实现，仅供理解参考：

| 文档 | 内容 |
|------|------|
| `references/search.md` | 搜索 scope 选择、字段说明 |
| `references/shelf.md` | 书架结构、数量口径、公开/私密规则 |
| `references/book.md` | 书籍信息、章节目录、阅读进度字段 |
| `references/notes.md` | 笔记统计口径、划线、想法、热门划线 |
| `references/review.md` | 公开点评字段与类型 |
| `references/readdata.md` | 阅读统计字段单位、周期组合 |
| `references/discover.md` | 推荐接口字段说明 |
| `references/profile.md` | 用户概况组合查询 |

## 已知 API 陷阱

| 陷阱 | 说明 | CLI 对策 |
|------|------|----------|
| `newRating` 是 0-1000 | 如 930 = 93%，不是百分制 | 自动除以 10 展示 |
| `star` 可能是 float | `100.0` 而非 `100` | `int()` 后再整除 |
| review 不传 count/maxIdx 会空 | 只返回统计摘要 | 自动传参 |
| notebooks 全量拉取可能超时 | 书架 2000+ 本时 | 默认限 5 页，`--max-pages` 调整 |
| `skill_version` 要同步 | `weread.py` 常量和 SKILL.md 版本号要一致 | 改版时一起改 |

## 文件结构

```
.
├── SKILL.md                  # 本文件
├── scripts/
│   └── weread.py             # 单文件 CLI（~1170 行）
├── references/               # API 字段参考文档
│   ├── search.md
│   ├── shelf.md
│   ├── book.md
│   ├── notes.md
│   ├── review.md
│   ├── readdata.md
│   ├── discover.md
│   └── profile.md
└── tests/
    └── test_weread.py        # 功能测试（53 个用例）
```

## 运行测试

```bash
python3 -m pytest tests/test_weread.py -v
```
