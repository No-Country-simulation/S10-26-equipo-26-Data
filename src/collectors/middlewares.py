class UserAgentMiddleware:
    def process_request(self, request, spider):
        request.headers.setdefault(
            "User-Agent", spider.settings.get("USER_AGENT", "PriceScopeBot/0.1")
        )
        request.headers.setdefault("Accept-Language", "es-AR,es;q=0.9")
