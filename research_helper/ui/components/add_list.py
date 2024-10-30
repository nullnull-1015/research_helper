from typing import Callable, Type, Dict, List, Tuple, Any
from uuid import uuid4, UUID
from abc import ABC, abstractmethod
import streamlit as st

from research_helper.ui.components.base import ComponentBase

class RowComponent(ComponentBase):
    def __init__(self, key: str, value: Any) -> None:
        super().__init__(key)
        self._value = value
    
    def draw(self) -> Any:
        self._value = self._draw()
        return self.value
    
    @abstractmethod
    def _draw(self) -> Any:
        pass
    
    def set_value(self, value: Any) -> None:
        self._value = value
    
    @property
    def value(self) -> Any:
        return self._value

class RowComponentFactory(ABC):
    def __init__(self, row_component_cls: Type[RowComponent], *args, **kwargs) -> None:
        super().__init__()
        
        self.row_component_cls = row_component_cls
        self._args   = args
        self._kwargs = kwargs
    
    def generate(self, key: str, value: Any) -> RowComponent:
        self._kwargs.update(key=key, value=value)
        return self.row_component_cls(*self._args, **self._kwargs)

class TextInput(RowComponent):
    def __init__(self, key: str, value: Any, placeholder : str = "") -> None:
        super().__init__(key, value)
        self._placeholder = placeholder
    
    def _draw(self) -> str:
        return st.text_input(" ", key=self._key, placeholder=self._placeholder, value=self.value, label_visibility="collapsed")

class SelectiveInput(RowComponent):
    def __init__(self, key: str, value: Any, options: List[str], placeholder : str = "") -> None:
        super().__init__(key, value)
        self._options = options
        self._placeholder = placeholder
    
    def _draw(self) -> Any:
        return st.selectbox(
            label=" ", key=self._key,
            placeholder=self._placeholder,
            options=self._options,
            index=self._options.index(self.value) if self.value else 0,
            label_visibility="collapsed"
        )

class DictInput(RowComponent):
    def __init__(
        self, key: str, value: Tuple[Any, Any],
        key_component_factory: RowComponentFactory, val_component_factory: RowComponentFactory,
    ) -> None:
        super().__init__(key, value)
        self._key_component = key_component_factory.generate(key=key+"_k", value=value[0] if value else value)
        self._val_component = val_component_factory.generate(key=key+"_v", value=value[1] if value else value)
    
    def set_value(self, value: Tuple[Any, Any]) -> None:
        super().set_value(value)
        key = value[0]
        val = value[1]
        self._key_component.set_value(key)
        self._val_component.set_value(val)
    
    def _draw(self) -> Tuple:
        container = st.container(border=True)
        with container:
            k = self._key_component.draw()
            v = self._val_component.draw()
        return (k, v) if k and v else None

class AddingRow(ComponentBase):
    def __init__(self, id: UUID, row_component: RowComponent, on_delete: Callable) -> None:
        """
        Args:
            id (UUID): UUID to identify this row
            label (str): label for text_input
            callback: (Callable): callback called when the delete button clicked
        """
        
        self._id = id
        self._row_compoent = row_component
        self.on_delete = on_delete
        self.input = row_component.value
    
    def draw(self):
        widget_col, del_col = st.columns([0.9, 0.1])
        key_prefix = f"{self._id}-"
        with widget_col:
            self.input = self._row_compoent.draw()
        
        with del_col:
            self.del_button = st.button(label=":material/delete:", key=key_prefix+"d", on_click=self.on_delete)
    
    def set_value(self, value: Any):
        self._row_compoent.set_value(value)
    
    def get_input(self) -> Any:
        return self.input

class AddingList(ComponentBase):
    def __init__(self, label: str, row_factory: RowComponentFactory) -> None:
        """

        Args:
            label (str): label for input column
        """
        self.label = label
        self._row_factory = row_factory
        self._rows: Dict[UUID, AddingRow] = {}
        self._id = uuid4()
    
    def draw(self) -> List[str]:
        with st.container():
            # header
            label_col, add_col = st.columns([0.9, 0.1])
            with label_col:
                st.text(self.label)
            with add_col:
                st.button(":material/add:", key=f"{self._id}", on_click=self._create_row)
            
            # body
            for row in self._rows.values():
                row.draw()
        
        return self.get_inputs()
    
    def set_values(self, values: List[Any]):
        self._rows = {} # reset rows
        for value in values:
            self.add_row(value)
    
    def add_row(self, value: Any):
        new_row = self._create_row(value=value)
        return new_row
    
    def _create_row(self, value: Any = None):
        row_id = uuid4()
        new_row = AddingRow(
            id=row_id,
            row_component=self._row_factory.generate(key=str(row_id)+"c", value=value),
            on_delete=lambda: self._del_row(row_id)
        )
        self._rows[row_id] = new_row
        return new_row
    
    def _del_row(self, id):
        if id in self._rows:
            del self._rows[id]
    
    def get_inputs(self) -> List[Any]:
        return [row.get_input() for row in self._rows.values() if row.get_input()]