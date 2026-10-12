def static_headers(headers, path, url):
    # Public, fixed vendor modules must load in an opaque sandbox origin.
    if "/vendor/" in url:
        headers["Access-Control-Allow-Origin"] = "*"
