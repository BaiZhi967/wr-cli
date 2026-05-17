#!/usr/bin/env python3
"""微信读书 CLI — 统一命令行接口。

用法:
  weread.py search <keyword> [--scope 10] [--page 1] [--per-page 10]
  weread.py shelf [--page 1] [--per-page 10]
  weread.py book <bookId> [--progress] [--chapters] [--chapters-page 1]
  weread.py notes [--book <bookId>] [--page 1] [--per-page 10] [--max-pages 5]
  weread.py readdata [--mode monthly|weekly|annually|overall] [--time 0]
  weread.py review <bookId> [--type 0] [--per-page 10]
  weread.py discover [--book <bookId>] [--per-page 10]
  weread.py list-apis

分页输出: 每条命令默认控制输出条目数，通过 --page / --per-page 控制。
"""

import urllib.request
import urllib.error

# Re-export all public symbols for backward compatibility
from _weread.constants import API_URL, SKILL_VERSION
from _weread.utils import *
from _weread.api import WereadAPI
from _weread.export import write_output
from _weread.search import collect_search, cmd_search
from _weread.shelf import collect_shelf, cmd_shelf
from _weread.book import collect_book_info, collect_book_chapters, cmd_book
from _weread.notes import collect_notes_overview, collect_notes_book, cmd_notes
from _weread.readdata import collect_readdata, cmd_readdata
from _weread.review import collect_review, cmd_review
from _weread.discover import collect_discover, cmd_discover
from _weread.cli import cmd_list_apis, main

if __name__ == "__main__":
    main()
