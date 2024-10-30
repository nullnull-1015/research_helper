from abc import ABC, abstractmethod
from typing import Any

class Drawable(ABC):    
    @abstractmethod
    def draw(self) -> Any:
        pass