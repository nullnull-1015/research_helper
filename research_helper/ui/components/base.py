from typing import Optional
from uuid import uuid4
from research_helper.ui.base import Drawable

class ComponentBase(Drawable):
    def __init__(self, key: Optional[str] = None) -> None:
        super().__init__()
        
        if key is None:
            key = str(uuid4())
        self._key = key
