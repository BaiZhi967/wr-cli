import time


def ts_to_date(ts):
    """Unix timestamp -> YYYY-MM-DD"""
    if not ts:
        return "-"
    return time.strftime("%Y-%m-%d", time.localtime(int(ts)))


def secs_to_hms(secs):
    """秒 -> X小时Y分钟"""
    s = int(secs or 0)
    if s <= 0:
        return "0分钟"
    h, m = divmod(s, 3600)
    m = m // 60
    if h > 0:
        return f"{h}小时{m}分钟"
    return f"{m}分钟"


def star_to_str(score):
    """评分整数 -> 星级。100=⭐⭐⭐⭐⭐"""
    if score is None or int(score) <= 0:
        return "无评分"
    stars = int(score) // 20
    return "⭐" * stars if stars else "无评分"


def rating_to_str(r):
    """评分 (0-1000) -> 文字描述。"""
    if r is None or r == 0:
        return "暂无"
    score = r / 10
    if score >= 90:
        return f"神作 {score:.0f}%"
    if score >= 80:
        return f"力荐 {score:.0f}%"
    if score >= 70:
        return f"好评 {score:.0f}%"
    return f"{score:.1f}分"


def make_deep_link(book_id, chapter_uid="", range_start="", range_end="", user_vid=""):
    """构造微信读书深度链接。"""
    if chapter_uid and range_start and range_end:
        link = f"weread://bestbookmark?bookId={book_id}&chapterUid={chapter_uid}&rangeStart={range_start}&rangeEnd={range_end}"
        if user_vid:
            link += f"&userVid={user_vid}"
        return link
    if chapter_uid:
        return f"weread://reading?bId={book_id}&chapterUid={chapter_uid}"
    return f"weread://reading?bId={book_id}"


def paginate_mark(items, page, per_page):
    """Slice items with page boundary info. Returns (page_items, total_pages, has_prev, has_next)."""
    total = len(items)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], total_pages, page > 1, page < total_pages


def truncate(text, max_len=200):
    """截断长文本。"""
    if not text or len(text) <= max_len:
        return text or ""
    return text[:max_len] + "…"


def print_nav(page, total_pages, has_prev, has_next):
    """Print page navigation hints."""
    if total_pages <= 1:
        return
    nav = []
    if has_prev:
        nav.append(f"--page {page - 1} 上一页")
    if has_next:
        nav.append(f"--page {page + 1} 下一页")
    if nav:
        print("  ".join(nav))
