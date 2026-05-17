from _weread.utils import rating_to_str, make_deep_link, truncate, paginate_mark, print_nav
from _weread.export import write_output


def collect_discover(api, args):
    """发现推荐 — 返回扁平数据列表。"""
    book_id = getattr(args, "bookId", None)
    per_page = getattr(args, "per_page", 10)

    if book_id:
        result = api.call("/book/similar", bookId=book_id, count=per_page)
        books = result.get("booksimilar", {}).get("books", [])
        items = []
        for b in books:
            bi = b.get("book", {}).get("bookInfo", {})
            items.append({
                "bookId": bi.get("bookId", ""),
                "title": bi.get("title", ""),
                "author": bi.get("author", ""),
                "rating": bi.get("newRating"),
                "readingCount": bi.get("readingCount", 0),
                "reason": "",
                "intro": bi.get("intro", ""),
                "link": make_deep_link(bi.get("bookId", "")),
            })
    else:
        result = api.call("/book/recommend", count=per_page)
        books = result.get("books", [])
        items = []
        for b in books:
            items.append({
                "bookId": b.get("bookId", ""),
                "title": b.get("title", ""),
                "author": b.get("author", ""),
                "rating": b.get("newRating"),
                "readingCount": b.get("readingCount", 0),
                "reason": b.get("reason", ""),
                "intro": b.get("intro", ""),
                "link": make_deep_link(b.get("bookId", "")),
            })
    return items


def cmd_discover(api, args):
    """发现推荐"""
    output_path = getattr(args, "output", None)
    if output_path:
        data = collect_discover(api, args)
        if not data:
            print("暂无推荐。")
            return
        write_output(data, output_path)
        print(f"已导出 {len(data)} 条推荐到 {output_path}")
        return

    book_id = getattr(args, "bookId", None)
    per_page = getattr(args, "per_page", 10)
    page = getattr(args, "page", 1)

    if book_id:
        result = api.call("/book/similar", bookId=book_id, count=per_page)
        books = result.get("booksimilar", {}).get("books", [])
        print("相似书推荐:")
    else:
        result = api.call("/book/recommend", count=per_page)
        books = result.get("books", [])
        print("为你推荐:")

    if not books:
        print("暂无推荐。")
        return

    page_items, total_pages, has_prev, has_next = paginate_mark(books, page, per_page)

    for i, b in enumerate(page_items, (page - 1) * per_page + 1):
        if book_id:
            bi = b.get("book", {}).get("bookInfo", {})
            reason = ""
        else:
            bi = b
            reason = b.get("reason", "")
        title = bi.get("title", "")
        author = bi.get("author", "")
        rating = rating_to_str(bi.get("newRating"))
        reading = bi.get("readingCount", 0)
        print(f"{i}. 《{title}》 {author}  |  {rating}  |  {reading}人在读")
        if reason:
            print(f"   推荐理由: {reason}")
        if bi.get("intro"):
            print(f"   简介: {truncate(bi['intro'], 100)}")
        print(f"   [打开]({make_deep_link(bi.get('bookId', ''))})")
        print()

    print_nav(page, total_pages, has_prev, has_next)
