def get_page_range(total_pages, current_page, max_range=5):
    if total_pages <= max_range + 2:
        return range(1, total_pages + 1)
    pages = []
    start_page = max(1, current_page - int(max_range / 2))
    end_page = min(total_pages, current_page + int(max_range / 2))
    if start_page > 1:
        pages.append(1)
    if start_page > 2:
        pages.append(None)
    pages += range(start_page, end_page + 1)
    if end_page < total_pages - 1:
        pages.append(None)
    if end_page < total_pages:
        pages.append(total_pages)
    return pages
