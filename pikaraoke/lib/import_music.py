def deep_search(bookmark, search_term):
    if isinstance(bookmark, list):
        for item in bookmark:
            result = deep_search(item, search_term)
            if result:
                return result
    elif isinstance(bookmark, dict):
        if search_term.lower() == bookmark.get("title", "").lower():
            return bookmark
        for key, value in bookmark.items():
            if isinstance(value, (list, dict)):
                result = deep_search(value, search_term)
                if result:
                    return result
    return None
