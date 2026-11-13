"""CatalogStore singleton: the catalog in memory, with indexes and query functions.  (Person A)

PHASE 0 STUB: empty store. Person A fills it at M-1 from MySQL via catalog/loader.py.
"""


class CatalogStore:
    def __init__(self) -> None:
        self.loaded = False


_store = CatalogStore()


def get_store() -> CatalogStore:
    return _store
