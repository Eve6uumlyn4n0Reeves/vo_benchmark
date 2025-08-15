#
# 功能: 实现内存存储后端。
#
from typing import Any, List, Optional
from .base import Storage


class MemoryStorage(Storage):
    def __init__(self):
        self._data = {}

    def save(self, key: str, data: Any) -> None:
        self._data[key] = data

    def load(self, key: str) -> Optional[Any]:
        return self._data.get(key)

    def exists(self, key: str) -> bool:
        return key in self._data

    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            return True
        return False

    def list_keys(self, prefix: str = "") -> List[str]:
        return [k for k in self._data if k.startswith(prefix)]
