import sys
import argparse

from _weread.api import WereadAPI
from _weread.search import cmd_search
from _weread.shelf import cmd_shelf
from _weread.book import cmd_book
from _weread.notes import cmd_notes
from _weread.readdata import cmd_readdata
from _weread.review import cmd_review
from _weread.discover import cmd_discover


def cmd_list_apis(api, args):
    """列出可用接口"""
    result = api.call("/_list")
    apis = result.get("apis", [])
    if not apis:
        print("无可用接口。")
        return
    for a in apis:
        name = a.get("api_name", "")
        desc = a.get("description", "")
        params = a.get("params", [])
        print(f"{name}")
        if desc:
            print(f"  {desc}")
        if params:
            for p in params[:5]:
                print(f"    --{p.get('name', '')} ({p.get('type', '')}): {p.get('desc', '')}")
        print()


def main():
    parser = argparse.ArgumentParser(description="微信读书 CLI")
    sub = parser.add_subparsers(dest="command", help="子命令")

    # search
    p = sub.add_parser("search", help="搜索书籍")
    p.add_argument("keyword", help="搜索关键词")
    p.add_argument("--scope", type=int, help="搜索类型 (0=全部 10=电子书 16=网文 14=有声书 6=作者)")
    p.add_argument("--count", type=int, help="API 每页数量")
    p.add_argument("--page", type=int, default=1, help="页码")
    p.add_argument("--per-page", type=int, default=10, help="每页显示条数")
    p.add_argument("--output", "-o", default=None, help="导出结果到文件（.json .csv .tsv .md .txt）")
    p.set_defaults(func=cmd_search)

    # shelf
    p = sub.add_parser("shelf", help="查看书架")
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--per-page", type=int, default=10)
    p.add_argument("--output", "-o", default=None, help="导出结果到文件（.json .csv .tsv .md .txt）")
    p.set_defaults(func=cmd_shelf)

    # book
    p = sub.add_parser("book", help="书籍详情")
    p.add_argument("bookId", help="书籍 ID")
    p.add_argument("--chapters", action="store_true", help="显示章节目录")
    p.add_argument("--progress", action="store_true", help="显示阅读进度")
    p.add_argument("--chapters-page", type=int, default=1)
    p.add_argument("--output", "-o", default=None, help="导出结果到文件（.json .csv .tsv .md .txt）")
    p.set_defaults(func=cmd_book)

    # notes
    p = sub.add_parser("notes", help="笔记/划线")
    p.add_argument("--book", dest="bookId", help="单本书 bookId，不传则显示笔记本概览")
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--per-page", type=int, default=10)
    p.add_argument("--max-pages", type=int, default=5, help="笔记本概览最多拉取页数")
    p.add_argument("--output", "-o", default=None, help="导出结果到文件（.json .csv .tsv .md .txt）")
    p.set_defaults(func=cmd_notes)

    # readdata
    p = sub.add_parser("readdata", help="阅读统计")
    p.add_argument("--mode", "-m", choices=["weekly", "monthly", "annually", "overall"], default="monthly")
    p.add_argument("--time", "-t", type=int, default=0, help="基准时间戳 (0=当前)")
    p.add_argument("--output", "-o", default=None, help="导出结果到文件（.json .csv .tsv .md .txt）")
    p.set_defaults(func=cmd_readdata)

    # review
    p = sub.add_parser("review", help="书籍点评")
    p.add_argument("bookId", help="书籍 ID")
    p.add_argument("--type", type=int, default=0, help="0=全部 1=推荐 2=不行 3=最新 4=一般")
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--per-page", type=int, default=10)
    p.add_argument("--output", "-o", default=None, help="导出结果到文件（.json .csv .tsv .md .txt）")
    p.set_defaults(func=cmd_review)

    # discover
    p = sub.add_parser("discover", help="发现推荐")
    p.add_argument("--book", dest="bookId", help="基于此书推荐相似书")
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--per-page", type=int, default=10)
    p.add_argument("--output", "-o", default=None, help="导出结果到文件（.json .csv .tsv .md .txt）")
    p.set_defaults(func=cmd_discover)

    # list-apis
    p = sub.add_parser("list-apis", help="列出可用 API")
    p.set_defaults(func=cmd_list_apis)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    api_client = WereadAPI()
    args.func(api_client, args)
