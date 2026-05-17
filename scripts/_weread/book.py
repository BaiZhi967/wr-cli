from _weread.utils import ts_to_date, secs_to_hms, rating_to_str, make_deep_link, paginate_mark
from _weread.export import write_output


def collect_book_info(api, book_id):
    """书籍信息 — 返回扁平单条数据。"""
    info = api.call("/book/info", bookId=book_id)
    return {
        "bookId": book_id,
        "title": info.get("title", ""),
        "author": info.get("author", ""),
        "translator": info.get("translator", ""),
        "rating": info.get("newRating"),
        "ratingCount": info.get("newRatingCount", 0),
        "category": info.get("category", ""),
        "publisher": info.get("publisher", ""),
        "publishTime": info.get("publishTime", ""),
        "isbn": info.get("isbn", ""),
        "wordCount": info.get("wordCount", 0),
        "intro": info.get("intro", ""),
        "link": make_deep_link(book_id),
    }


def collect_book_chapters(api, book_id):
    """书籍章节 — 返回扁平数据列表。"""
    ch_info = api.call("/book/chapterinfo", bookId=book_id)
    chapters = []
    for idx, ch in enumerate(ch_info.get("chapters", []), 1):
        chapters.append({
            "chapterIdx": idx,
            "chapterUid": ch.get("chapterUid", ""),
            "title": ch.get("title", ""),
            "level": ch.get("level", 1),
            "wordCount": ch.get("wordCount", 0),
            "paid": ch.get("paid", 0),
            "isMPChapter": ch.get("isMPChapter", False),
        })
    return chapters


def cmd_book(api, args):
    """书籍信息"""
    book_id = args.bookId
    output_path = getattr(args, "output", None)

    if output_path:
        # Export mode: export chapters if --chapters, otherwise book info
        if getattr(args, "chapters", False):
            data = collect_book_chapters(api, book_id)
        else:
            info = collect_book_info(api, book_id)
            data = [info]
        write_output(data, output_path)
        print(f"已导出到 {output_path}")
        return

    # Display mode (original behavior)
    info = api.call("/book/info", bookId=book_id)

    print(f"《{info.get('title', '')}》")
    print(f"作者: {info.get('author', '')}")
    if info.get("translator"):
        print(f"译者: {info.get('translator', '')}")
    print(f"评分: {rating_to_str(info.get('newRating'))}  ({info.get('newRatingCount', 0)}人评)")
    print(f"分类: {info.get('category', '')}")
    print(f"出版社: {info.get('publisher', '')}")
    if info.get("publishTime"):
        print(f"出版: {info.get('publishTime', '')}")
    if info.get("isbn"):
        print(f"ISBN: {info.get('isbn', '')}")
    if info.get("wordCount"):
        wc = info["wordCount"]
        print(f"字数: {wc/10000:.1f}万字" if wc >= 10000 else f"字数: {wc}字")
    if info.get("intro"):
        print(f"\n简介: {info['intro']}")
    print(f"\n[打开阅读]({make_deep_link(book_id)})")

    if getattr(args, "chapters", False):
        print("\n── 章节目录 ──")
        ch_info = api.call("/book/chapterinfo", bookId=book_id)
        chs = ch_info.get("chapters", [])
        ch_page = getattr(args, "chapters_page", 1)
        ch_per_page = 20
        page_items, total_pages, has_prev, has_next = paginate_mark(chs, ch_page, ch_per_page)
        for ch in page_items:
            indent = "  " * max(0, ch.get("level", 1) - 1)
            paid = "🔒" if ch.get("paid") == 1 and ch.get("price", 0) > 0 else ""
            mp_ch = " [公众号]" if ch.get("isMPChapter") else ""
            title = ch.get("title", "")
            print(f"{indent}{title}{paid}{mp_ch}")
        if total_pages > 1:
            print(f"\n(第 {ch_page}/{total_pages} 页，--chapters-page N 翻页)")

    if getattr(args, "progress", False):
        print("\n── 阅读进度 ──")
        prog = api.call("/book/getprogress", bookId=book_id)
        book = prog.get("book", {})
        pct = book.get("progress", 0)
        rec = book.get("recordReadingTime", 0)
        print(f"进度: {pct}%")
        print(f"累计阅读: {secs_to_hms(rec)}")
        if book.get("updateTime"):
            print(f"最后阅读: {ts_to_date(book['updateTime'])}")
        if book.get("finishTime"):
            print(f"读完: {ts_to_date(book['finishTime'])}")
