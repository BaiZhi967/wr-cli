from _weread.utils import ts_to_date, star_to_str, truncate, paginate_mark, print_nav
from _weread.export import write_output


def collect_review(api, args):
    """书籍点评 — 返回扁平数据列表。"""
    book_id = args.bookId
    rv_type = getattr(args, "type", 0)
    per_page = getattr(args, "per_page", 10)

    result = api.call("/review/list", bookId=book_id, reviewListType=rv_type,
                       count=per_page, maxIdx=0)

    reviews = result.get("reviews", [])
    items = []
    for r in reviews:
        rev = r.get("review", {}).get("review", {})
        author = rev.get("author", {})
        items.append({
            "reviewId": rev.get("reviewId", ""),
            "author": author.get("name", "匿名"),
            "star": rev.get("star", 0),
            "starDisplay": star_to_str(rev.get("star", 0)),
            "content": rev.get("content", ""),
            "createTime": ts_to_date(rev.get("createTime", 0)),
            "isFinish": rev.get("isFinish", False),
            "chapterName": rev.get("chapterName", ""),
        })
    return items


def cmd_review(api, args):
    """书籍点评"""
    output_path = getattr(args, "output", None)

    if output_path:
        data = collect_review(api, args)
        write_output(data, output_path)
        print(f"已导出 {len(data)} 条点评到 {output_path}")
        return

    book_id = args.bookId
    rv_type = getattr(args, "type", 0)
    per_page = getattr(args, "per_page", 10)
    page = getattr(args, "page", 1)

    result = api.call("/review/list", bookId=book_id, reviewListType=rv_type,
                       count=per_page, maxIdx=0)

    reviews_cnt = result.get("reviewsCnt", 0)
    print(f"点评共 {reviews_cnt} 条")
    if result.get("deepVRecommendInfo"):
        info = result["deepVRecommendInfo"]
        print(f"{info.get('title', '')}  {info.get('subtitle', '')}")
    print()

    reviews = result.get("reviews", [])
    page_items, total_pages, has_prev, has_next = paginate_mark(reviews, page, per_page)

    for i, r in enumerate(page_items, (page - 1) * per_page + 1):
        rev = r.get("review", {}).get("review", {})
        author = rev.get("author", {})
        name = author.get("name", "匿名")
        star = star_to_str(rev.get("star", 0))
        is_finish = " · 已读完" if rev.get("isFinish") else ""
        ch = rev.get("chapterName", "")
        ch_str = f" · {ch}" if ch else ""
        print(f"{i}. {name}  {star}{is_finish}{ch_str}")
        print(f"   {truncate(rev.get('content', ''), 200)}")
        print()

    print_nav(page, total_pages, has_prev, has_next)
