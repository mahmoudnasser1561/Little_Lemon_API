from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """B24: a fixed page size with no client control was the real complaint. Callers can
    now ask for a bigger (or smaller) page with ?page_size=, capped at max_page_size so
    nobody can request the whole table in one response."""
    page_size_query_param = 'page_size'
    max_page_size = 50
