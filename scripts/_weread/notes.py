from _weread.utils import ts_to_date, star_to_str, make_deep_link, paginate_mark, print_nav
from _weread.export import write_output


def collect_notes_overview(api, args):
    """笔记本概览 — 返回扁平数据列表。"""
    all_books = []
    count = 50
    last_sort = 0
    max_pages = getattr(args, "max_pages", 5)
    pages_fetched = 0
    while pages_fetched < max_pages:
        params = {"count": count}
        if last_sort > 0:
            params["lastSort"] = last_sort
        nb_result = api.call("/user/notebooks", **params)
        for b in nb_result.get("books", []):
            bk = b.get("book", {})
            all_books.append({
                "bookId": b.get("bookId", ""),
                "title": bk.get("title", ""),
                "author": bk.get("author", ""),
                "reviewCount": b.get("reviewCount", 0),
                "noteCount": b.get("noteCount", 0),
                "bookmarkCount": b.get("bookmarkCount", 0),
                "totalNotes": b.get("reviewCount", 0) + b.get("noteCount", 0) + b.get("bookmarkCount", 0),
                "readingProgress": b.get("readingProgress", 0),
                "finished": b.get("markedStatus", 0),
                "link": make_deep_link(b.get("bookId", "")),
            })
        pages_fetched += 1
        if nb_result.get("hasMore") != 1:
            break
        if all_books:
            last_sort = all_books[-1]["totalNotes"]
    all_books.sort(key=lambda x: x["totalNotes"], reverse=True)
    return all_books


def collect_notes_book(api, book_id):
    """单本书笔记 — 返回划线+想法合并列表。"""
    bm = api.call("/book/bookmarklist", bookId=book_id)
    updated = bm.get("updated", [])
    chapters_map = {c.get("chapterUid"): c for c in bm.get("chapters", [])}
    book_title = bm.get("book", {}).get("title", book_id)

    items = []
    for u in updated:
        ch = chapters_map.get(u.get("chapterUid"), {})
        items.append({
            "type": "bookmark",
            "bookTitle": book_title,
            "chapterTitle": ch.get("title", f"章节{u.get('chapterUid', '')}"),
            "markText": u.get("markText", ""),
            "createTime": ts_to_date(u.get("createTime", 0)),
            "chapterUid": u.get("chapterUid", ""),
        })

    try:
        rv = api.call("/review/list/mine", bookid=book_id, count=50, synckey=0)
    except SystemExit:
        rv = {}
    for r in rv.get("reviews", []):
        rev = r.get("review", {})
        items.append({
            "type": "review",
            "bookTitle": book_title,
            "chapterTitle": rev.get("chapterName", ""),
            "content": rev.get("content", ""),
            "star": rev.get("star", -1),
            "createTime": ts_to_date(rev.get("createTime", 0)),
            "chapterUid": rev.get("chapterUid", ""),
        })
    return items


def cmd_notes(api, args):
    """笔记划线"""
    book_id = getattr(args, "bookId", None)
    output_path = getattr(args, "output", None)

    if output_path:
        if book_id:
            data = collect_notes_book(api, book_id)
        else:
            data = collect_notes_overview(api, args)
        write_output(data, output_path)
        print(f"已导出 {len(data)} 条到 {output_path}")
        return

    if book_id:
        # 单本书笔记
        print("── 划线内容 ──")
        bm = api.call("/book/bookmarklist", bookId=book_id)
        updated = bm.get("updated", [])
        chapters_map = {c.get("chapterUid"): c for c in bm.get("chapters", [])}
        book_title = bm.get("book", {}).get("title", book_id)

        page = getattr(args, "page", 1)
        per_page = getattr(args, "per_page", 10)
        page_items, total_pages, has_prev, has_next = paginate_mark(updated, page, per_page)

        if not updated:
            print(f"《{book_title}》暂无划线。")
        else:
            print(f"《{book_title}》 共 {len(updated)} 条划线")
            for i, u in enumerate(page_items, (page - 1) * per_page + 1):
                ch = chapters_map.get(u.get("chapterUid"), {})
                ch_title = ch.get("title", f"章节{u.get('chapterUid', '')}")
                print(f"{i}. [{ts_to_date(u.get('createTime', 0))}] {ch_title}")
                print(f"   > {u.get('markText', '')}")
                rng = u.get("range", "")
                if rng and "-" in rng:
                    rs, re = rng.split("-", 1)
                    print(f"   [位置]({make_deep_link(book_id, str(u.get('chapterUid', '')), rs, re)})")
                print()
            if total_pages > 1:
                print(f"(第 {page}/{total_pages} 页)")

        print("\n── 个人想法 ──")
        try:
            rv = api.call("/review/list/mine", bookid=book_id, count=50, synckey=0)
        except SystemExit:
            rv = {}
        reviews = rv.get("reviews", [])
        rv_items, rv_tp, _, _ = paginate_mark(reviews, page, per_page)

        if not reviews:
            print("暂无个人想法。")
        else:
            for i, r in enumerate(rv_items, (page - 1) * per_page + 1):
                rev = r.get("review", {})
                star = star_to_str(rev.get("star", -1))
                ch = rev.get("chapterName", "")
                loc = f" [{ch}]" if ch else ""
                print(f"{i}. {star}{loc}  {ts_to_date(rev.get('createTime', 0))}")
                print(f"   {rev.get('content', '')}")
                rng = rev.get("range", "")
                if rng and "-" in rng:
                    rs, re = rng.split("-", 1)
                    print(f"   [位置]({make_deep_link(book_id, str(rev.get('chapterUid', '')), rs, re)})")
                print()
            if rv_tp > 1:
                print(f"(第 {page}/{rv_tp} 页)")

    else:
        # 笔记本概览
        all_books = []
        count = 50
        last_sort = 0
        max_pages = getattr(args, "max_pages", 5)
        pages_fetched = 0
        while pages_fetched < max_pages:
            params = {"count": count}
            if last_sort > 0:
                params["lastSort"] = last_sort
            nb_result = api.call("/user/notebooks", **params)
            for b in nb_result.get("books", []):
                bk = b.get("book", {})
                all_books.append({
                    "bookId": b.get("bookId", ""),
                    "title": bk.get("title", ""),
                    "author": bk.get("author", ""),
                    "reviewCount": b.get("reviewCount", 0),
                    "noteCount": b.get("noteCount", 0),
                    "bookmarkCount": b.get("bookmarkCount", 0),
                    "total": b.get("reviewCount", 0) + b.get("noteCount", 0) + b.get("bookmarkCount", 0),
                    "readingProgress": b.get("readingProgress", 0),
                    "markedStatus": b.get("markedStatus", 0),
                    "sort": b.get("sort", 0),
                })
            pages_fetched += 1
            if nb_result.get("hasMore") != 1:
                break
            if all_books:
                last_sort = all_books[-1]["sort"]

        all_books.sort(key=lambda x: x["total"], reverse=True)

        if pages_fetched >= max_pages:
            print(f"有笔记的书 (已获取 {pages_fetched} 页，使用 --max-pages N 获取更多)")
        else:
            print(f"有笔记的书共 {len(all_books)} 本")
        total_notes = sum(b["total"] for b in all_books)
        print(f"笔记总数: {total_notes} (想法{sum(b['reviewCount'] for b in all_books)} + "
              f"划线{sum(b['noteCount'] for b in all_books)} + 书签{sum(b['bookmarkCount'] for b in all_books)})")
        print()

        page = getattr(args, "page", 1)
        per_page = getattr(args, "per_page", 10)
        page_items, total_pages, has_prev, has_next = paginate_mark(all_books, page, per_page)

        for i, b in enumerate(page_items, (page - 1) * per_page + 1):
            status = "✓读完" if b["markedStatus"] == 1 else f"进度{b['readingProgress']}%"
            print(f"{i}. 《{b['title']}》 {b['author']}  [{status}]")
            print(f"   笔记 {b['total']} 条 (想法{b['reviewCount']} + 划线{b['noteCount']} + 书签{b['bookmarkCount']})")
            print(f"   [查看笔记] weread.py notes --book {b['bookId']}")
            if b["bookId"]:
                print(f"   [打开]({make_deep_link(b['bookId'])})")
            print()

        print_nav(page, total_pages, has_prev, has_next)
