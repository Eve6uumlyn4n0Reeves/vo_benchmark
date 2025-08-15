#
# 功能: 定义存储后端的抽象接口。
#
from abc import ABC, abstractmethod
from typing import Any, List, Optional


class Storage(ABC):
    @abstractmethod
    def save(self, key: str, data: Any) -> None:
        pass

    @abstractmethod
    def load(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    def list_keys(self, prefix: str = "") -> List[str]:
        pass
