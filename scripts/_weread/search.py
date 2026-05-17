from _weread.utils import rating_to_str, make_deep_link, paginate_mark, print_nav
from _weread.export import write_output


def collect_search(api, args):
    """搜索书籍 — 返回扁平数据列表。"""
    params = {"keyword": args.keyword}
    if getattr(args, "scope", None) is not None:
        params["scope"] = args.scope
    if getattr(args, "count", None):
        params["count"] = args.count

    result = api.call("/store/search", **params)
    results = result.get("results", [])
    if not results:
        return []

    all_books = []
    for group in results:
        for b in group.get("books", []):
            bi = b.get("bookInfo", {})
            all_books.append({
                "bookId": bi.get("bookId", ""),
                "title": bi.get("title", ""),
                "author": bi.get("author", ""),
                "category": bi.get("category", ""),
                "rating": bi.get("newRating"),
                "ratingCount": bi.get("newRatingCount", 0),
                "readingCount": b.get("readingCount", 0),
                "price": bi.get("price", 0),
                "soldout": bi.get("soldout", 0),
                "link": make_deep_link(bi.get("bookId", "")),
            })
    return all_books


def cmd_search(api, args):
    """搜索书籍"""
    all_books = collect_search(api, args)
    if not all_books:
        print("未找到结果。")
        return

    output_path = getattr(args, "output", None)
    if output_path:
        write_output(all_books, output_path)
        print(f"已导出 {len(all_books)} 条结果到 {output_path}")
        return

    page = getattr(args, "page", 1)
    per_page = getattr(args, "per_page", 10)
    page_items, total_pages, has_prev, has_next = paginate_mark(all_books, page, per_page)

    print(f"搜索: {args.keyword}  共 {len(all_books)} 条结果")
    if total_pages > 1:
        print(f"(第 {page}/{total_pages} 页，每页 {per_page} 条)")
    print()

    for i, b in enumerate(page_items, (page - 1) * per_page + 1):
        rating = rating_to_str(b["rating"])
        status = " [已下架]" if b["soldout"] else ""
        print(f"{i}. {b['title']}{status}")
        print(f"   作者: {b['author']}  |  {rating}  |  {b['readingCount']}人在读")
        if b["price"] > 0:
            print(f"   价格: ¥{b['price']/100:.2f}  |  分类: {b['category']}")
        else:
            print(f"   分类: {b['category']}")
        print(f"   [打开]({b['link']})")
        print()

    print_nav(page, total_pages, has_prev, has_next)
