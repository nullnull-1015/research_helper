import os
import io
import sys
import traceback
import json
import pandas as pd
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from abc import ABC, abstractmethod
from typing import Any, List, Set, Dict, Type, Literal, Optional, Callable
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from research_helper.schemas.csv import CSV
from research_helper.dataframe.joiner import RHDataFrame, RHDataFrameAdapter, CombinedRHDataFrameBase, ConcatedRHDataFrame, MergedRHDataFrame
from research_helper.ui.components.base import ComponentBase

# TODO: リファクタリング

class CSVNode(ComponentBase):
    def __init__(self, next: Optional['CSVElement'] = None) -> None:
        self._key = uuid4()
        self._next = next
    
    @abstractmethod
    def draw(self) -> Optional[RHDataFrame]:
        pass
    
    @abstractmethod
    def delete(self):
        pass
    
    @abstractmethod
    def up(self):
        pass
    
    @abstractmethod
    def down(self):
        pass
        
    @property
    @abstractmethod
    def rhdf(self) -> Optional[RHDataFrame]:
        pass


TYPE2CLASS: Dict[str, Type[CombinedRHDataFrameBase]] = {
    "concat": ConcatedRHDataFrame,
    "merge" : MergedRHDataFrame,
}

@dataclass
class CombiningConfig:
    type: Literal["concat", "merge"] = "concat"
    args: Dict[str, Any] = field(default_factory=dict)

class CSVHead(CSVNode):
    CONFIG_FILE = "config.json"
    
    def __init__(self, data_dir_path: str) -> None:
        super().__init__(next=None)
        
        self._config_file = data_dir_path+"/"+CSVHead.CONFIG_FILE
        self._load()
        self._save() # create config file
    
    def draw(self) -> Optional[RHDataFrame]:
        self._save()
        if self._next:
            return self._next.draw()

    
    def insert_csv(self, csv: CSV, config: Optional[CombiningConfig] = CombiningConfig()):
        tail = self.tail
        tail._next = CSVElement(csv, config=config, prev=tail)
    
    def delete(self):
        raise RuntimeError("CSVHead can't be deleted.")
    
    def up(self):
        pass # ignore it to fix the head
    
    def down(self):
        pass # ignore it to fix the head
    
    def get(self, csv_name: str) -> Optional['CSVElement']:
        node = self._next
        while node:
            csv = node._csv
            if csv.name == csv_name:
                return node
            
            node = node._next
    
    @property
    def csvs(self) -> Dict[str, CSV]:
        csvs: Dict[str, CSV] = {}
        
        node = self._next
        while node:
            csv = node._csv
            csvs[csv.name] = csv
            node = node._next
        
        return csvs
    
    def _save(self):
        node = self._next
        data = []
        while node:
            data.append(node.data.serialize())
            node = node._next
        
        with open(self._config_file, "w", encoding="utf-8") as fw:
            json.dump({
                "data": data
            }, fw)
    
    def _load(self) -> Optional['CSVElement']:
        try:
            with open(self._config_file, "r", encoding="utf-8") as fr:
                data = json.load(fr)
        except:
            return None
        
        data = data["data"]
        for d in data:
            try:
                csv_path = d["csv"]["path"]
                _, extension = os.path.splitext(csv_path)
                if extension == ".csv":
                    data = pd.read_csv(csv_path, encoding="utf-8")
                elif extension == ".jsonl":
                    data =  pd.read_json(csv_path, orient='records', lines=True)
                rhdf = RHDataFrameAdapter(data)
                csv = CSV(path=csv_path, rhdf=rhdf)
                config = CombiningConfig(**d["config"])
                self.insert_csv(csv, config)
            except:
                continue
    
    @property
    def tail(self):
        node = self
        while node._next:
            node = node._next
        return node
    
    @property
    def rhdf(self):
        return None

@dataclass
class ElementData:
    csv: CSV
    config: CombiningConfig
    
    def serialize(self) -> Dict[str, Any]:
        return {
            "csv": {
                "path": self.csv.path,
            },
            "config": {
                "type": self.config.type,
                "args": self.config.args,
            }
        }

class CSVElement(CSVNode):
    def __init__(self, csv: CSV, config: CombiningConfig, prev: Optional[CSVNode], next: Optional['CSVElement'] = None) -> None:
        super().__init__(next=next)
        self._csv = csv
        self._prev = prev
        
        self._config = config
    
    def draw(self) -> RHDataFrame:
        if isinstance(self._prev, CSVElement):
            self._draw()
        
        name_col, up_col, down_col, add_col = st.columns([0.7, 0.1, 0.1, 0.1])
        with name_col:
            st.text(self._csv.name)
        with up_col:
            key = f"csv-elm-up_{self._key}"
            st.button(":material/arrow_upward:", key=key, on_click=lambda: self.up())
        with down_col:
            key = f"csv-elm-down_{self._key}"
            st.button(":material/arrow_downward:", key=key, on_click=lambda: self.down())
        with add_col:
            key = f"csv-elm-delete_{self._key}"
            st.button(":material/delete:", key=key, on_click=lambda: self.delete())
        
        if self._next:
            self._next.draw()
        
        return self.rhdf
    
    def _draw(self) -> None:
        type_col, _, how_col, _, left_on_col, _, right_on_col = st.columns([0.2, 0.1, 0.2, 0.05, 0.2, 0.05, 0.2])
        options = list(TYPE2CLASS.keys()) if self._is_mergeable() else ["concat"]
        with type_col:
            type_key = f"{self._key}_type"
            st.selectbox(
                " ",
                options=options,
                index=options.index(self._config.type),
                key=type_key, on_change=lambda: self._set_type(st.session_state[type_key]), 
                label_visibility="collapsed"
            )
        
        if self._config.type == "concat":
            """ 縦につなげるだけに concat を使用するため、他の引数を無視 """
        elif self._config.type == "merge":
            with how_col:
                how_key = f"{self._key}_how"
                st.selectbox(
                    " ",
                    options=["inner", "left", "right", "outer"],
                    key=how_key, on_change=lambda: self._update_args({"how": st.session_state[how_key]}),
                    label_visibility="collapsed"
                )
            
            shared_col = self._shared_columns()
            with left_on_col:
                left_on_key = f"{self._key}_left_on"
                value = shared_col[0] if shared_col else self._prev.rhdf.df.columns[0]
                columns = list(self._prev.rhdf.df.columns)
                st.selectbox(
                    " ",
                    help="left on",
                    options=columns,
                    index=columns.index(value),
                    key=left_on_key,
                    on_change=lambda: self._update_args({"left_on": st.session_state[left_on_key]}),
                    label_visibility="collapsed"
                )
            
            with right_on_col:
                right_on_key = f"{self._key}_right_on"
                value = shared_col[0] if shared_col else self._csv.rhdf.df.columns[0]
                columns = list(self._csv.rhdf.df.columns)
                st.selectbox(
                    " ",
                    help="right on",
                    options=columns,
                    index=columns.index(value),
                    key=right_on_key,
                    on_change=lambda: self._update_args({"right_on": st.session_state[right_on_key]}),
                    label_visibility="collapsed"
                )
    
    def _shared_columns(self) -> List:
        if self._prev.rhdf is None: return []
        return list(set(self._csv.rhdf.df.columns) & set(self._prev.rhdf.df.columns))
    
    def _is_mergeable(self) -> bool:
        return self._prev.rhdf and not self._prev.rhdf.df.empty and not self._csv.rhdf.df.empty
    
    def _set_type(self, type: str):
        self._config.type = type
        if self._config.type == "merge" and self._is_mergeable():
            shared_col = self._shared_columns()
            self._config.args = {
                "how": "inner",
                "left_on" : shared_col[0] if shared_col else self._prev.rhdf.df.columns[0],
                "right_on": shared_col[0] if shared_col else self._csv.rhdf.df.columns[0],
            }
        elif self._config.type == "concat":
            self._config.args = {}
    
    def _update_args(self, update: Dict[str, Any]):
        self._config.args.update(update)
    
    def delete(self):
        self._prev._next = self._next
        if self._next:
            self._next._prev = self._prev
        self._csv.delete()
        self._set_type("concat") # reset config
    
    def up(self):
        self._prev.down()
        # reset config
        self._set_type("concat")
        if self._next:
            self._next._set_type("concat")
    
    def down(self):
        if self._next:
            prev = self._prev
            next = self._next
            
            prev._next = next
            next._prev = prev
            
            self._next = next._next
            if next._next:
                next._next._prev = self
            
            next._next = self
            self._prev = next
            
            self._set_type("concat") # reset config
    
    def print(self):
        print(self._csv.name+"->", end="")
        if self._next:
            self._next.print()
    
    def update(self, csv: Optional[CSV]=None, config: Optional[CombiningConfig]=None):
        if csv:
            self._csv = csv
        if config:
            self._config = config
    
    @property
    def rhdf(self):
        if self._prev.rhdf:
            cls = TYPE2CLASS[self._config.type]
            return cls(left=self._prev.rhdf, right=self._csv.rhdf, **self._config.args)
        else:
            return self._csv.rhdf
    
    @property
    def data(self) -> ElementData:
        return ElementData(csv=self._csv, config=self._config)


class CSVFormatError(Exception):
    pass

class MultiCSVUploader(ComponentBase):
    DATA_DIR_NAME = "data"
    
    def __init__(self, dir_path: str) -> None:
        self.dir_path = dir_path if not dir_path.endswith("/") else dir_path[:-1]
        self._data_dir_path = self.dir_path+ "/" + MultiCSVUploader.DATA_DIR_NAME
        if not os.path.isdir(self._data_dir_path):
            os.makedirs(self._data_dir_path)
        
        self._id = uuid4()
        self._key = f"multi-file-uploader_{self._id}"
        
        self._csv_head = CSVHead(data_dir_path=self._data_dir_path)
        self._error = ""
    
    def _on_update_files(self, file: Optional[UploadedFile]):
        if file is None: return
        
        csv = self._upload_file(file)
        if csv is None: return # failed to load csv
        
        if node:=self._csv_head.get(file.name):
            node.update(csv=csv)
        else:
            self._csv_head.insert_csv(csv)

    def _upload_file(self, file: UploadedFile) -> Optional[CSV]:
        try:
            csv_path, csv_df = self.load_file(file)
            csv = CSV(path=csv_path, rhdf=RHDataFrameAdapter(csv_df))
            self._error = ""
            return csv
        except:
            etype, value, tb = sys.exc_info()
            error_msg = "".join(traceback.format_exception_only(etype, value))
            self._error = error_msg
    
    def load_file(self, file: Optional[UploadedFile]) -> Optional[pd.DataFrame]:
        if file is None: return None
        
        _, extension = os.path.splitext(file.name)
        if extension == ".csv":
            return self.load_csv(file)
        elif extension == ".jsonl":
            return self.load_jsonl(file)
        
        raise Exception(f"Invalid File: {file.name}, {extension}")
        
    
    def load_csv(self, file: Optional[UploadedFile]) -> Optional[pd.DataFrame]:
        new_csv = pd.read_csv(io.BytesIO(file.read()))
        csv_path = self._data_dir_path+"/"+file.name
        new_csv.to_csv(csv_path, mode="w", encoding="utf-8", index=False)
        return csv_path, new_csv
        
    
    def load_jsonl(self, file: Optional[UploadedFile]) -> Optional[pd.DataFrame]:
        new_csv = pd.read_json(io.BytesIO(file.read()), orient='records', lines=True)
        csv_path = self._data_dir_path+"/"+file.name
        new_csv.to_json(csv_path, orient='records', lines=True, force_ascii=False)
        return csv_path, new_csv
    
    def draw(self) -> Optional[RHDataFrame]:
        try:
            if rhdf:=self._csv_head.tail.rhdf:
                st.dataframe(rhdf.df)
        except:
            # failed to combine
            etype, value, tb = sys.exc_info()
            error_msg = traceback.format_exception_only(etype, value)
            st.error(error_msg)
        if self._error:
            st.error(self._error)
        
        self._csv_head.draw()
        
        st.file_uploader(
            "Upload CSV file",
            type=["csv", "jsonl"],
            key=self._key,
            on_change=lambda: self._on_update_files(st.session_state[self._key]),
        )
        
        return self.rhdf
    
    def get_rhdf(self) -> Optional[RHDataFrame]:
        try:
            return self.rhdf
        except:
            # failed to combine
            return None
    
    @property
    def rhdf(self):
        return self._csv_head.tail.rhdf