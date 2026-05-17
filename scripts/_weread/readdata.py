from _weread.utils import secs_to_hms, ts_to_date
from _weread.export import write_output


def collect_readdata(api, args):
    """阅读统计 — 返回扁平数据列表。"""
    mode = getattr(args, "mode", "monthly")
    base_time = getattr(args, "time", 0)
    params = {"mode": mode}
    if base_time:
        params["baseTime"] = base_time
    result = api.call("/readdata/detail", **params)

    row = {
        "mode": mode,
        "readDays": result.get("readDays", 0),
        "totalReadTime": result.get("totalReadTime", 0),
        "totalReadTimeHuman": secs_to_hms(result.get("totalReadTime", 0)),
        "dayAverageReadTime": result.get("dayAverageReadTime", 0),
        "compare": result.get("compare"),
    }

    # Flatten top books
    longest = result.get("readLongest", [])
    if longest:
        top_books = []
        for item in longest[:5]:
            bk = item.get("book", {})
            ai = item.get("albumInfo")
            top_books.append({
                "title": bk.get("title", "") if bk else (ai.get("name", "") if ai else ""),
                "author": bk.get("author", "") if bk else (ai.get("authorName", "") if ai else ""),
                "readTime": item.get("readTime", 0),
                "readTimeHuman": secs_to_hms(item.get("readTime", 0)),
                "tags": item.get("tags", []),
            })
        row["topBooks"] = top_books

    # Flatten prefer categories
    pref_cat = result.get("preferCategory")
    if pref_cat:
        cats = []
        for c in pref_cat[:5]:
            cats.append({"category": c.get("categoryTitle", ""), "count": c.get("readingCount", 0),
                         "time": secs_to_hms(c.get("readingTime", 0))})
        row["preferCategories"] = cats

    # Flatten prefer authors
    pref_author = result.get("preferAuthor")
    if pref_author:
        authors = []
        for a in pref_author[:5]:
            authors.append({"name": a.get("name", ""), "count": a.get("count", 0)})
        row["preferAuthors"] = authors

    # Read rate
    rr = result.get("readRate")
    if rr is not None:
        row["readRate"] = rr
        row["wrReadTime"] = result.get("wrReadTime", 0)
        row["wrListenTime"] = result.get("wrListenTime", 0)

    return [row]


def cmd_readdata(api, args):
    """阅读统计"""
    output_path = getattr(args, "output", None)
    if output_path:
        data = collect_readdata(api, args)
        write_output(data, output_path)
        print(f"已导出阅读统计到 {output_path}")
        return

    # Display mode (original behavior preserved exactly)
    mode = getattr(args, "mode", "monthly")
    base_time = getattr(args, "time", 0)

    params = {"mode": mode}
    if base_time:
        params["baseTime"] = base_time
    result = api.call("/readdata/detail", **params)

    read_days = result.get("readDays", 0)
    total_secs = result.get("totalReadTime", 0)
    daily_avg = result.get("dayAverageReadTime", 0)
    compare = result.get("compare")

    mode_names = {"weekly": "本周", "monthly": "本月", "annually": "本年", "overall": "总计"}
    print(f"📊 {mode_names.get(mode, mode)}阅读统计")
    print(f"   阅读 {read_days} 天  |  总时长 {secs_to_hms(total_secs)}  |  日均 {secs_to_hms(daily_avg)}")
    if compare is not None:
        direction = "↑" if compare >= 0 else "↓"
        print(f"   较上期: {direction}{abs(compare)*100:.0f}%")

    read_stat = result.get("readStat", [])
    if read_stat:
        parts = [f"{s.get('stat', '')}: {s.get('counts', '')}" for s in read_stat]
        print(f"   " + "  |  ".join(parts))
    print()

    rank = result.get("rank")
    if rank:
        print(f"🏅 {rank.get('text', '')}")
        print()

    longest = result.get("readLongest", [])
    if longest:
        print("读得最多:")
        for item in longest[:5]:
            bk = item.get("book", {})
            ai = item.get("albumInfo")
            rt = item.get("readTime", 0)
            name = bk.get("title", "") if bk else (ai.get("name", "") if ai else "未知")
            author = bk.get("author", "") if bk else (ai.get("authorName", "") if ai else "")
            tags = " ".join(f"[{t}]" for t in item.get("tags", []))
            print(f"  · {name}  {author}  {secs_to_hms(rt)}  {tags}")
        print()

    pref_cat = result.get("preferCategory")
    if pref_cat:
        print(f"偏好分类: {result.get('preferCategoryWord', '偏好阅读')}")
        for c in pref_cat[:5]:
            print(f"  · {c.get('categoryTitle', '')}  {c.get('readingCount', 0)}本  {secs_to_hms(c.get('readingTime', 0))}")
        print()

    pref_time_word = result.get("preferTimeWord")
    if pref_time_word:
        print(f"偏好时段: {pref_time_word}")

    pref_author = result.get("preferAuthor")
    if pref_author:
        print("偏好作者:")
        for a in pref_author[:5]:
            print(f"  · {a.get('name', '')}  {a.get('count', 0)}本  {a.get('readTime', '')}")
        print()

    pref_pub = result.get("preferPublisher")
    if pref_pub:
        print("偏好出版社:")
        for p in pref_pub[:5]:
            print(f"  · {p.get('name', '')}  {p.get('count', 0)}本")
        print()

    rr = result.get("readRate")
    if rr is not None:
        wr = result.get("wrReadTime", 0)
        wl = result.get("wrListenTime", 0)
        print(f"阅读/听书: 文字 {secs_to_hms(wr)} ({rr}%)  |  听书 {secs_to_hms(wl)}")
        print()

    medals = result.get("medals", [])
    if medals:
        print("勋章:")
        for m in medals:
            print(f"  🏅 {m.get('name', '')}: {m.get('desc', '')}")
        print()

    pref = result.get("preferBooks", [])
    if pref:
        print("偏好书籍:")
        for pb in pref[:5]:
            bi = pb.get("bookInfo", {})
            print(f"  [{pb.get('title', '')}] 《{bi.get('title', '')}》 {bi.get('author', '')}")
            print(f"    {pb.get('reason', '')}")
        print()

    reg = result.get("registTime")
    if reg:
        print(f"注册时间: {ts_to_date(reg)}")
