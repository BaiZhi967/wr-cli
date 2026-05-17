from _weread.utils import ts_to_date, make_deep_link, paginate_mark, print_nav
from _weread.export import write_output


def collect_shelf(api, args):
    """书架管理 — 返回扁平数据列表。"""
    result = api.call("/shelf/sync")
    books = result.get("books", [])
    albums = result.get("albums", [])
    mp = result.get("mp")

    all_items = []
    for b in books:
        all_items.append({
            "type": "ebook",
            "bookId": b.get("bookId", ""),
            "title": b.get("title", ""),
            "author": b.get("author", ""),
            "category": b.get("category", ""),
            "readUpdateTime": ts_to_date(b.get("readUpdateTime", 0)),
            "finishReading": b.get("finishReading", 0),
            "isTop": b.get("isTop", 0),
            "secret": b.get("secret", 0),
            "link": make_deep_link(b.get("bookId", "")),
        })
    for a in albums:
        ai = a.get("albumInfo", {})
        aie = a.get("albumInfoExtra", {})
        all_items.append({
            "type": "audiobook",
            "bookId": ai.get("albumId", ""),
            "title": ai.get("name", ""),
            "author": ai.get("authorName", ""),
            "category": "有声书",
            "readUpdateTime": ts_to_date(aie.get("lectureReadUpdateTime", 0)),
            "finishReading": 1 if ai.get("finish", 0) else 0,
            "isTop": aie.get("isTop", 0),
            "secret": aie.get("secret", 0),
            "link": "",
        })
    if mp:
        all_items.append({
            "type": "mp",
            "bookId": mp.get("book", {}).get("bookId", ""),
            "title": mp.get("book", {}).get("title", "文章收藏"),
            "author": "",
            "category": "文章收藏",
            "readUpdateTime": "-",
            "finishReading": 0,
            "isTop": 0,
            "secret": mp.get("book", {}).get("secret", 0),
            "link": "",
        })
    return all_items


def cmd_shelf(api, args):
    """书架管理"""
    all_items = collect_shelf(api, args)
    books = [x for x in all_items if x["type"] == "ebook"]
    albums_list = [x for x in all_items if x["type"] == "audiobook"]
    mp_items = [x for x in all_items if x["type"] == "mp"]
    has_mp = len(mp_items) > 0

    total = len(books) + len(albums_list) + (1 if has_mp else 0)
    secret_books = sum(1 for b in books if b["secret"] == 1)
    public_books = len(books) - secret_books
    secret_albums = sum(1 for a in albums_list if a["secret"] == 1)
    public_albums = len(albums_list) - secret_albums

    output_path = getattr(args, "output", None)
    if output_path:
        write_output(all_items, output_path)
        print(f"已导出 {len(all_items)} 条书架条目到 {output_path}")
        return

    print(f"书架共 {total} 个条目：{len(books)} 本电子书", end="")
    if albums_list:
        print(f" + {len(albums_list)} 个有声书", end="")
    if has_mp:
        print(" + 1 个文章收藏", end="")
    print()
    secret_mp = sum(1 for x in mp_items if x["secret"] == 1)
    secret_total = secret_books + secret_albums + (1 if has_mp and secret_mp else 0)
    public_total = public_books + public_albums
    print(f"公开 {public_total}  |  私密 {secret_total}")
    print()

    page = getattr(args, "page", 1)
    per_page = getattr(args, "per_page", 10)
    page_items, total_pages, has_prev, has_next = paginate_mark(all_items, page, per_page)

    for i, item in enumerate(page_items, (page - 1) * per_page + 1):
        icon = "📖" if item["type"] == "ebook" else "🎧"
        tags = []
        if item["isTop"]:
            tags.append("置顶")
        if item["finishReading"]:
            tags.append("已读完")
        if item["secret"]:
            tags.append("私密")
        tag_str = " " + " ".join(f"[{t}]" for t in tags) if tags else ""
        time_str = f"  最近: {item['readUpdateTime']}" if item["readUpdateTime"] != "-" else ""
        print(f"{i}. {icon} {item['title']}{tag_str}")
        print(f"   {item['author']}  |  {item['category']}{time_str}")
        if item["bookId"]:
            print(f"   [打开]({item['link']})")
        print()

    print_nav(page, total_pages, has_prev, has_next)
