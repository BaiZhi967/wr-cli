#!/usr/bin/env python3
"""weread.py 功能测试 — 覆盖所有子命令和工具函数。"""

import csv
import json
import os
import sys
import io
import tempfile
import unittest
from unittest.mock import patch, MagicMock

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
sys.path.insert(0, SCRIPTS_DIR)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import weread
from weread import WereadAPI


def _load_mock_data():
    with open(os.path.join(PROJECT_ROOT, "mock-data.json")) as f:
        return json.load(f)


def _load_mock_supplement():
    with open(os.path.join(PROJECT_ROOT, "mock-data-supplement.json")) as f:
        return json.load(f)


MOCK = _load_mock_data()
MOCK_SUP = _load_mock_supplement()


def _make_args(**kwargs):
    return type("Args", (), kwargs)()


def _make_api():
    """Create a WereadAPI with a test key (no real env needed)."""
    api = WereadAPI.__new__(WereadAPI)
    api.key = "wrk-test"
    return api


# ─── Utility Tests ────────────────────────────────────────────────

class TestUtilities(unittest.TestCase):

    def test_ts_to_date(self):
        self.assertEqual(weread.ts_to_date(1748563200), "2025-05-30")
        self.assertEqual(weread.ts_to_date(0), "-")
        self.assertEqual(weread.ts_to_date(None), "-")

    def test_ts_to_date_cst(self):
        self.assertEqual(weread.ts_to_date(1748736000), "2025-06-01")
        self.assertEqual(weread.ts_to_date(1735660800), "2025-01-01")

    def test_secs_to_hms(self):
        self.assertEqual(weread.secs_to_hms(0), "0分钟")
        self.assertEqual(weread.secs_to_hms(None), "0分钟")
        self.assertEqual(weread.secs_to_hms(60), "1分钟")
        self.assertEqual(weread.secs_to_hms(3661), "1小时1分钟")
        self.assertEqual(weread.secs_to_hms(7200), "2小时0分钟")
        self.assertEqual(weread.secs_to_hms(9000), "2小时30分钟")
        self.assertEqual(weread.secs_to_hms(482360), "133小时59分钟")

    def test_star_to_str(self):
        self.assertEqual(weread.star_to_str(100), "⭐⭐⭐⭐⭐")
        self.assertEqual(weread.star_to_str(80), "⭐⭐⭐⭐")
        self.assertEqual(weread.star_to_str(60), "⭐⭐⭐")
        self.assertEqual(weread.star_to_str(40), "⭐⭐")
        self.assertEqual(weread.star_to_str(20), "⭐")
        self.assertEqual(weread.star_to_str(-1), "无评分")
        self.assertEqual(weread.star_to_str(0), "无评分")
        self.assertEqual(weread.star_to_str(None), "无评分")

    def test_star_to_str_float(self):
        self.assertEqual(weread.star_to_str(100.0), "⭐⭐⭐⭐⭐")
        self.assertEqual(weread.star_to_str(80.0), "⭐⭐⭐⭐")

    def test_rating_to_str(self):
        self.assertEqual(weread.rating_to_str(950), "神作 95%")
        self.assertEqual(weread.rating_to_str(856), "力荐 86%")
        self.assertEqual(weread.rating_to_str(750), "好评 75%")
        self.assertEqual(weread.rating_to_str(500), "50.0分")
        self.assertEqual(weread.rating_to_str(0), "暂无")
        self.assertEqual(weread.rating_to_str(None), "暂无")

    def test_make_deep_link(self):
        self.assertEqual(weread.make_deep_link("123"), "weread://reading?bId=123")
        self.assertEqual(weread.make_deep_link("123", "456"),
                         "weread://reading?bId=123&chapterUid=456")
        self.assertEqual(weread.make_deep_link("123", "456", "100", "200"),
                         "weread://bestbookmark?bookId=123&chapterUid=456&rangeStart=100&rangeEnd=200")
        self.assertEqual(weread.make_deep_link("123", "456", "100", "200", "vid1"),
                         "weread://bestbookmark?bookId=123&chapterUid=456&rangeStart=100&rangeEnd=200&userVid=vid1")

    def test_truncate(self):
        self.assertEqual(weread.truncate("short", 200), "short")
        self.assertEqual(weread.truncate("x" * 300, 200), "x" * 200 + "…")
        self.assertEqual(weread.truncate("", 200), "")
        self.assertEqual(weread.truncate(None, 200), "")

    def test_paginate_mark(self):
        items = list(range(25))
        result, total, prev, nxt = weread.paginate_mark(items, 1, 10)
        self.assertEqual(result, list(range(10)))
        self.assertEqual(total, 3)
        self.assertFalse(prev)
        self.assertTrue(nxt)

        result, total, prev, nxt = weread.paginate_mark(items, 2, 10)
        self.assertEqual(result, list(range(10, 20)))
        self.assertTrue(prev)
        self.assertTrue(nxt)

        result, total, prev, nxt = weread.paginate_mark(items, 3, 10)
        self.assertEqual(result, list(range(20, 25)))
        self.assertTrue(prev)
        self.assertFalse(nxt)

        result, total, prev, nxt = weread.paginate_mark([], 1, 10)
        self.assertEqual(result, [])
        self.assertEqual(total, 1)


# ─── API Client Tests ─────────────────────────────────────────────

class TestWereadAPI(unittest.TestCase):

    def test_init_with_env(self):
        with patch.dict(os.environ, {"WEREAD_API_KEY": "wrk-test123"}):
            api = WereadAPI()
            self.assertEqual(api.key, "wrk-test123")

    def test_init_no_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.isfile", return_value=False):
                with self.assertRaises(SystemExit):
                    WereadAPI()

    @patch("weread.urllib.request.urlopen")
    def test_call_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"data": "ok"}).encode()
        mock_urlopen.return_value = mock_resp
        api = _make_api()
        result = api.call("/test/api", param1="a")
        self.assertEqual(result, {"data": "ok"})
        body = json.loads(mock_urlopen.call_args[0][0].data)
        self.assertEqual(body["skill_version"], weread.SKILL_VERSION)

    @patch("weread.urllib.request.urlopen")
    def test_call_http_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "url", 403, "Forbidden", {}, io.BytesIO(b"forbidden"))
        api = _make_api()
        with self.assertRaises(SystemExit):
            api.call("/test/api")

    @patch("weread.urllib.request.urlopen")
    def test_call_errcode(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"errcode": 1, "errmsg": "bad"}).encode()
        mock_urlopen.return_value = mock_resp
        api = _make_api()
        with self.assertRaises(SystemExit):
            api.call("/test/api")

    @patch("weread.urllib.request.urlopen")
    def test_call_upgrade_info(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            {"upgrade_info": {"message": "Please upgrade"}}).encode()
        mock_urlopen.return_value = mock_resp
        api = _make_api()
        with self.assertRaises(SystemExit):
            api.call("/test/api")


# ─── Command Tests ────────────────────────────────────────────────

class TestSearchCommand(unittest.TestCase):
    def test_search_ebook(self):
        mock_api = _make_api()
        mock_api.call = MagicMock(return_value={
            "results": [{
                "title": "电子书", "scope": 10,
                "books": [{
                    "bookInfo": {"bookId": "1", "title": "三体", "author": "刘慈欣",
                                 "category": "科幻", "soldout": 0,
                                 "newRating": 950, "newRatingCount": 5000},
                    "newRating": 950, "newRatingCount": 5000,
                    "readingCount": 12000, "searchIdx": 0,
                }]
            }]
        })
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            weread.cmd_search(mock_api, _make_args(keyword="三体", scope=None, count=None,
                                                    page=1, per_page=10))
        output = buf.getvalue()
        self.assertIn("三体", output)
        self.assertIn("刘慈欣", output)
        self.assertIn("神作", output)

    def test_search_empty(self):
        mock_api = _make_api()
        mock_api.call = MagicMock(return_value={"results": []})
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            weread.cmd_search(mock_api, _make_args(keyword="不存在的书", scope=None,
                                                    count=None, page=1, per_page=10))
        self.assertIn("未找到", buf.getvalue())


class TestShelfCommand(unittest.TestCase):
    def test_shelf_display(self):
        mock_api = _make_api()
        mock_api.call = MagicMock(return_value=MOCK_SUP["shelf_sync"])
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            weread.cmd_shelf(mock_api, _make_args(page=1, per_page=20))
        output = buf.getvalue()
        self.assertIn("23 个条目", output)
        self.assertIn("20 本电子书", output)
        self.assertIn("[置顶]", output)
        self.assertIn("[私密]", output)

    def test_shelf_public_private(self):
        mock_api = _make_api()
        mock_api.call = MagicMock(return_value=MOCK_SUP["shelf_sync"])
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            weread.cmd_shelf(mock_api, _make_args(page=1, per_page=20))
        output = buf.getvalue()
        self.assertIn("私密 3", output)
        self.assertIn("公开 20", output)


class TestBookCommand(unittest.TestCase):
    def test_book_info(self):
        mock_api = _make_api()

        def side_effect(api_name, **kw):
            return {
                "/book/info": {
                    "title": "深入理解计算机系统", "author": "Randal E.Bryant",
                    "newRating": 960, "newRatingCount": 1200, "category": "计算机",
                    "publisher": "机械工业出版社", "wordCount": 500000,
                    "intro": "A classic CS book"},
                "/book/chapterinfo": {"chapters": [
                    {"chapterUid": 1, "title": "第一章", "level": 1, "wordCount": 30000},
                    {"chapterUid": 2, "title": "第二章", "level": 1, "wordCount": 25000}]},
                "/book/getprogress": {"book": {"progress": 72, "recordReadingTime": 78200,
                                               "updateTime": 1754092800, "isStartReading": 1}},
            }.get(api_name, {})

        mock_api.call = MagicMock(side_effect=side_effect)
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            weread.cmd_book(mock_api, _make_args(
                bookId="3300045871", chapters=True, progress=True, chapters_page=1))
        output = buf.getvalue()
        self.assertIn("深入理解计算机系统", output)
        self.assertIn("神作", output)  # 960 -> 96% -> 神作
        self.assertIn("72%", output)
        self.assertIn("第一章", output)


class TestReaddataCommand(unittest.TestCase):
    def test_monthly(self):
        mock_api = _make_api()
        mock_api.call = MagicMock(return_value=MOCK["monthly_report"]["readdata_monthly"])
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            weread.cmd_readdata(mock_api, _make_args(mode="monthly", time=0))
        output = buf.getvalue()
        self.assertIn("本月", output)
        self.assertIn("13小时21分钟", output)
        self.assertIn("24 天", output)

    def test_weekly(self):
        mock_api = _make_api()
        mock_api.call = MagicMock(return_value=MOCK["weekly_report"]["readdata_weekly"])
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            weread.cmd_readdata(mock_api, _make_args(mode="weekly", time=0))
        output = buf.getvalue()
        self.assertIn("本周", output)
        self.assertIn("7小时", output)
        self.assertIn("朋友中排第2名", output)

    def test_annually(self):
        mock_api = _make_api()
        mock_api.call = MagicMock(return_value=MOCK["yearly_report"]["readdata_annually"])
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            weread.cmd_readdata(mock_api, _make_args(mode="annually", time=0))
        output = buf.getvalue()
        self.assertIn("本年", output)
        self.assertIn("133小时59分钟", output)
        self.assertIn("287 天", output)
        self.assertIn("67本", output)
        self.assertIn("阅读马拉松", output)
        self.assertIn("刘慈欣", output)


class TestNotesCommand(unittest.TestCase):
    def test_notebooks_overview(self):
        mock_api = _make_api()
        mock_api.call = MagicMock(return_value={
            "totalBookCount": 15, "totalNoteCount": 1842, "hasMore": 0,
            "books": [
                {"bookId": "25801052",
                 "book": {"title": "百年孤独", "author": "加西亚·马尔克斯"},
                 "reviewCount": 86, "noteCount": 242, "bookmarkCount": 18,
                 "readingProgress": 100, "markedStatus": 1, "sort": 1753478400},
                {"bookId": "3300045871",
                 "book": {"title": "深入理解计算机系统", "author": "Randal E.Bryant"},
                 "reviewCount": 45, "noteCount": 312, "bookmarkCount": 25,
                 "readingProgress": 100, "markedStatus": 1, "sort": 1754092800},
            ],
        })
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            weread.cmd_notes(mock_api, _make_args(bookId=None, page=1, per_page=10, max_pages=5))
        output = buf.getvalue()
        self.assertIn("百年孤独", output)
        self.assertIn("2 本", output)

    def test_single_book_notes(self):
        mock_api = _make_api()

        def side_effect(api_name, **kw):
            return {
                "/book/bookmarklist": {
                    "updated": [{"bookmarkId": "bm001", "chapterUid": 1,
                                 "markText": "多年以后，面对行刑队…",
                                 "createTime": 1753478400, "range": "0-56"}],
                    "chapters": [{"chapterUid": 1, "title": "第一章"}],
                    "book": {"title": "百年孤独"}},
                "/review/list/mine": {"reviews": [
                    {"review": {"content": "开篇经典", "createTime": 1753400000,
                                "chapterName": "", "star": -1}}]},
            }.get(api_name, {})

        mock_api.call = MagicMock(side_effect=side_effect)
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            weread.cmd_notes(mock_api, _make_args(bookId="25801052", page=1, per_page=10, max_pages=5))
        output = buf.getvalue()
        self.assertIn("百年孤独", output)
        self.assertIn("多年以后", output)
        self.assertIn("开篇经典", output)


class TestReviewCommand(unittest.TestCase):
    def test_review_list(self):
        mock_api = _make_api()
        # Build review data matching the nested structure: reviews[].review.review
        mock_api.call = MagicMock(return_value={
            "reviewsCnt": 100,
            "deepVRecommendInfo": {"title": "100 资深会员", "subtitle": "90%推荐"},
            "reviews": [
                {"review": {"review": {
                    "content": "好书推荐", "star": 100, "isFinish": 1,
                    "author": {"name": "测试用户"},
                    "createTime": 1753478400}}},
                {"review": {"review": {
                    "content": "一般般", "star": 60, "isFinish": 0,
                    "author": {"name": "另一个用户"},
                    "createTime": 1753400000}}},
            ],
        })
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            weread.cmd_review(mock_api, _make_args(bookId="7190022", type=0, page=1, per_page=10))
        output = buf.getvalue()
        self.assertIn("测试用户", output)
        self.assertIn("⭐⭐⭐⭐⭐", output)
        self.assertIn("100 资深会员", output)


class TestDiscoverCommand(unittest.TestCase):
    def test_recommend(self):
        mock_api = _make_api()
        mock_api.call = MagicMock(return_value={
            "books": [{"bookId": "1", "title": "测试书", "author": "某作者",
                       "newRating": 800, "reason": "因为你读过类似的书"}]})
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            weread.cmd_discover(mock_api, _make_args(bookId=None, page=1, per_page=10))
        output = buf.getvalue()
        self.assertIn("为你推荐", output)
        self.assertIn("测试书", output)

    def test_similar(self):
        mock_api = _make_api()
        mock_api.call = MagicMock(return_value={
            "booksimilar": {"sessionId": "s1", "books": [
                {"idx": 0, "book": {"bookInfo": {
                    "bookId": "2", "title": "相似书", "author": "作者B"}}}]}})
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            weread.cmd_discover(mock_api, _make_args(bookId="3300045871", page=1, per_page=10))
        output = buf.getvalue()
        self.assertIn("相似书推荐", output)
        self.assertIn("相似书", output)

    def test_similar_empty(self):
        mock_api = _make_api()
        mock_api.call = MagicMock(return_value={"booksimilar": {"sessionId": "s1", "books": []}})
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            weread.cmd_discover(mock_api, _make_args(bookId="3300045871", page=1, per_page=10))
        self.assertIn("暂无", buf.getvalue())


class TestListApisCommand(unittest.TestCase):
    def test_list_apis(self):
        mock_api = _make_api()
        mock_api.call = MagicMock(return_value={
            "apis": [{"api_name": "/shelf/sync", "description": "书架同步",
                      "params": [{"name": "none", "type": "void", "desc": "-"}]}]})
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            weread.cmd_list_apis(mock_api, _make_args())
        output = buf.getvalue()
        self.assertIn("/shelf/sync", output)
        self.assertIn("书架同步", output)


# ─── Mock Data Integrity ──────────────────────────────────────────

class TestMockDataIntegrity(unittest.TestCase):
    def test_mock_data_structure(self):
        self.assertIn("yearly_report", MOCK)
        self.assertIn("monthly_report", MOCK)
        self.assertIn("weekly_report", MOCK)

    def test_mock_supplement_structure(self):
        for key in ["shelf_sync", "notebooks", "book_progress_samples",
                     "review_list_sample", "bookmarklist_sample", "bestbookmarks_sample"]:
            self.assertIn(key, MOCK_SUP)

    def test_shelf_books_count(self):
        s = MOCK_SUP["shelf_sync"]
        total = len(s["books"]) + len(s["albums"]) + (1 if s.get("mp") else 0)
        self.assertEqual(total, 23)

    def test_yearly_fields(self):
        data = MOCK["yearly_report"]["readdata_annually"]
        self.assertEqual(len(data["readLongest"]), 10)
        self.assertEqual(len(data["preferCategory"]), 8)

    def test_bookmarklist_chapters(self):
        bm = MOCK_SUP["bookmarklist_sample"]
        ch_uids = {c["chapterUid"] for c in bm["chapters"]}
        for item in bm["updated"]:
            self.assertIn(item["chapterUid"], ch_uids)



# ─── Export Tests ──────────────────────────────────────────────────

class TestExportHelpers(unittest.TestCase):
    """Test write_output for all supported formats."""

    def test_write_json(self):
        data = [{"name": "test", "value": 42}]
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            path = f.name
        try:
            weread.write_output(data, path)
            with open(path) as f:
                result = json.load(f)
            self.assertEqual(result, data)
        finally:
            os.unlink(path)

    def test_write_csv(self):
        data = [{"name": "alice", "score": 95}, {"name": "bob", "score": 80}]
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            path = f.name
        try:
            weread.write_output(data, path)
            with open(path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["name"], "alice")
            self.assertEqual(rows[0]["score"], "95")
            self.assertEqual(rows[1]["name"], "bob")
        finally:
            os.unlink(path)

    def test_write_tsv(self):
        data = [{"col1": "a", "col2": "b"}, {"col1": "c", "col2": "d"}]
        with tempfile.NamedTemporaryFile(suffix=".tsv", delete=False, mode="w") as f:
            path = f.name
        try:
            weread.write_output(data, path)
            with open(path) as f:
                reader = csv.DictReader(f, delimiter="\t")
                rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["col1"], "a")
            self.assertEqual(rows[0]["col2"], "b")
        finally:
            os.unlink(path)

    def test_write_markdown(self):
        data = [{"title": "三体", "author": "刘慈欣"}]
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            path = f.name
        try:
            weread.write_output(data, path)
            with open(path) as f:
                text = f.read()
            self.assertIn("| title | author |", text)
            self.assertIn("| --- | --- |", text)
            self.assertIn("| 三体 | 刘慈欣 |", text)
        finally:
            os.unlink(path)

    def test_write_txt(self):
        data = [{"key1": "val1", "key2": "val2"}]
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            path = f.name
        try:
            weread.write_output(data, path)
            with open(path) as f:
                text = f.read()
            self.assertIn("key1: val1", text)
            self.assertIn("key2: val2", text)
            self.assertIn("---", text)
        finally:
            os.unlink(path)

    def test_write_empty_csv(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            path = f.name
        try:
            weread.write_output([], path)
            with open(path) as f:
                content = f.read()
            self.assertEqual(content, "")
        finally:
            os.unlink(path)

    def test_write_empty_markdown(self):
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            path = f.name
        try:
            weread.write_output([], path)
            with open(path) as f:
                content = f.read()
            self.assertEqual(content, "")
        finally:
            os.unlink(path)

    def test_write_nested_values_csv(self):
        data = [{"name": "test", "tags": ["a", "b"], "meta": {"x": 1}}]
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            path = f.name
        try:
            weread.write_output(data, path)
            with open(path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            self.assertEqual(rows[0]["tags"], '["a", "b"]')
            self.assertEqual(rows[0]["meta"], '{"x": 1}')
        finally:
            os.unlink(path)

    def test_unsupported_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False, mode="w") as f:
            path = f.name
        try:
            with self.assertRaises(SystemExit):
                weread.write_output([{"a": 1}], path)
        finally:
            os.unlink(path)


class TestSearchExport(unittest.TestCase):
    def test_search_json_export(self):
        mock_api = _make_api()
        mock_api.call = MagicMock(return_value={
            "results": [{
                "title": "电子书", "scope": 10,
                "books": [{
                    "bookInfo": {"bookId": "1", "title": "三体", "author": "刘慈欣",
                                 "category": "科幻", "newRating": 950, "newRatingCount": 5000},
                    "readingCount": 12000}]
            }]
        })
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                weread.cmd_search(mock_api, _make_args(keyword="三体", scope=None, count=None,
                                                        page=1, per_page=10, output=path))
            with open(path) as f:
                data = json.load(f)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["title"], "三体")
            self.assertEqual(data[0]["rating"], 950)
            self.assertIn("已导出", buf.getvalue())
        finally:
            os.unlink(path)


class TestShelfExport(unittest.TestCase):
    def test_shelf_csv_export(self):
        mock_api = _make_api()
        mock_api.call = MagicMock(return_value=MOCK_SUP["shelf_sync"])
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name
        try:
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                weread.cmd_shelf(mock_api, _make_args(page=1, per_page=20, output=path))
            with open(path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            self.assertEqual(len(rows), 23)
            self.assertIn("已导出", buf.getvalue())
        finally:
            os.unlink(path)


class TestNotesExport(unittest.TestCase):
    def test_notes_overview_json_export(self):
        mock_api = _make_api()
        mock_api.call = MagicMock(return_value={
            "totalBookCount": 2, "totalNoteCount": 10, "hasMore": 0,
            "books": [
                {"bookId": "25801052",
                 "book": {"title": "百年孤独", "author": "加西亚·马尔克斯"},
                 "reviewCount": 5, "noteCount": 3, "bookmarkCount": 2,
                 "readingProgress": 100, "markedStatus": 1},
            ],
        })
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                weread.cmd_notes(mock_api, _make_args(bookId=None, page=1, per_page=10,
                                                       max_pages=5, output=path))
            with open(path) as f:
                data = json.load(f)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["title"], "百年孤独")
        finally:
            os.unlink(path)


class TestReaddataExport(unittest.TestCase):
    def test_readdata_json_export(self):
        mock_api = _make_api()
        mock_api.call = MagicMock(return_value=MOCK["monthly_report"]["readdata_monthly"])
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                weread.cmd_readdata(mock_api, _make_args(mode="monthly", time=0, output=path))
            with open(path) as f:
                data = json.load(f)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["mode"], "monthly")
            self.assertIn("已导出", buf.getvalue())
        finally:
            os.unlink(path)


class TestReviewExport(unittest.TestCase):
    def test_review_csv_export(self):
        mock_api = _make_api()
        mock_api.call = MagicMock(return_value={
            "reviewsCnt": 2,
            "reviews": [
                {"review": {"review": {
                    "content": "好书", "star": 100, "isFinish": 1,
                    "author": {"name": "用户A"}, "createTime": 1753478400}}},
                {"review": {"review": {
                    "content": "一般", "star": 60, "isFinish": 0,
                    "author": {"name": "用户B"}, "createTime": 1753400000}}},
            ],
        })
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name
        try:
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                weread.cmd_review(mock_api, _make_args(bookId="7190022", type=0,
                                                        page=1, per_page=10, output=path))
            with open(path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["author"], "用户A")
        finally:
            os.unlink(path)


class TestDiscoverExport(unittest.TestCase):
    def test_discover_json_export(self):
        mock_api = _make_api()
        mock_api.call = MagicMock(return_value={
            "books": [{"bookId": "1", "title": "测试书", "author": "某作者",
                       "newRating": 800, "reason": "推荐理由", "readingCount": 100}]})
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                weread.cmd_discover(mock_api, _make_args(bookId=None, page=1, per_page=10,
                                                          output=path))
            with open(path) as f:
                data = json.load(f)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["title"], "测试书")
            self.assertEqual(data[0]["reason"], "推荐理由")
        finally:
            os.unlink(path)

    def test_discover_empty_no_export(self):
        mock_api = _make_api()
        mock_api.call = MagicMock(return_value={"booksimilar": {"sessionId": "s1", "books": []}})
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            weread.cmd_discover(mock_api, _make_args(bookId="3300045871", page=1, per_page=10,
                                                      output=None))
        self.assertIn("暂无", buf.getvalue())


class TestBookExport(unittest.TestCase):
    def test_book_info_json_export(self):
        mock_api = _make_api()
        mock_api.call = MagicMock(return_value={
            "title": "三体", "author": "刘慈欣", "newRating": 950,
            "newRatingCount": 5000, "category": "科幻", "wordCount": 300000,
        })
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                weread.cmd_book(mock_api, _make_args(bookId="7190022", chapters=False,
                                                      progress=False, chapters_page=1,
                                                      output=path))
            with open(path) as f:
                data = json.load(f)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["title"], "三体")
            self.assertEqual(data[0]["bookId"], "7190022")
        finally:
            os.unlink(path)

    def test_book_chapters_csv_export(self):
        mock_api = _make_api()
        mock_api.call = MagicMock(return_value={
            "chapters": [
                {"chapterUid": 1, "title": "第一章", "level": 1, "wordCount": 30000,
                 "paid": 0, "isMPChapter": False},
                {"chapterUid": 2, "title": "第二章", "level": 1, "wordCount": 25000,
                 "paid": 1, "isMPChapter": False},
            ],
        })
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name
        try:
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                weread.cmd_book(mock_api, _make_args(bookId="7190022", chapters=True,
                                                      progress=False, chapters_page=1,
                                                      output=path))
            with open(path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["title"], "第一章")
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
