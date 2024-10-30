import streamlit as st
import pandas as pd
import os
import io
import sys
import traceback
from typing import Any, List, Dict, Optional
from uuid import uuid4
from dataclasses import dataclass
from pandas._typing import Renamer

from streamlit.runtime.uploaded_file_manager import UploadedFile

from research_helper.schemas.csv import CSV
from research_helper.dataframe.joiner import RHDataFrameAdapter
from research_helper.ui.components.base import ComponentBase


class CSVFormatError(Exception):
    pass

class CSVTmpUploader(ComponentBase):
    """ manage uploaded file on memory, not file """
    SELECT_COLUMN: str = "__selected"
    
    def __init__(self, columns: List[str]=[], strict: bool=True) -> None:
        super().__init__(key=f"csv-tmp-uploader_{uuid4()}")
        
        self._columns = columns
        self.strict = strict
        
        self._df: Optional[pd.DataFrame] = None
        self._error: str = ""
    
    def draw(self) -> Optional[pd.DataFrame]:
        with st.container():
            file = st.file_uploader(
                " ",
                type=["csv"],
                key=self._key,
                on_change=lambda: self._upload_csv(st.session_state[self._key]),
                label_visibility="collapsed",
            )
            
            with st.expander("FILE", expanded=(file is not None)):
                if self._df is not None:
                    st.text("COLUMN name editor")
                    columns = {column: [column] for column in self._df.columns if column != CSVTmpUploader.SELECT_COLUMN}
                    column_editor_key = "columns-editor"
                    st.data_editor(
                        columns,
                        key=column_editor_key,
                        # edited_rows are like 'edited_rows': {0: {'__selected': 'select'}}
                        on_change=lambda: self._rename_column(st.session_state[column_editor_key]["edited_rows"][0])
                    )
                    
                    st.text("DATA")
                    data_editor_key = "data-editor"
                    st.data_editor(
                        self._df,
                        key=data_editor_key,
                        column_config={
                            CSVTmpUploader.SELECT_COLUMN: st.column_config.CheckboxColumn(
                                "selected",
                                help="Select to pick out.",
                                default=True,
                            )
                        },
                        hide_index=True,
                        on_change=lambda: self._update_csv(st.session_state[data_editor_key]["edited_rows"])
                    )
                    return self.csv
                
                if self._error:
                    st.error(self._error)
                    return None

        # No file uploaded
        return None
    
    def _reset_field(self):
        self._df = None
        self._error = None
    
    def _rename_column(self, renamer: Renamer):
        if self.csv is None: return
        if all([new_col_name not in self.csv.columns for new_col_name in renamer.values()]):
            self._df = self._df.rename(columns=renamer)
    
    def _update_csv(self, editor: Dict[int, Dict[str, str]]):
        if self._df is None or not editor: return
        for idx, data in editor.items():
            col_name, new_value = list(data.items())[0]
            self._df.loc[idx, col_name] = new_value
    
    def _upload_csv(self, file: Optional[UploadedFile]) -> None:
        self._reset_field()
        if not file: return
        
        try:
            df = self.load_csv(file)
            df[CSVTmpUploader.SELECT_COLUMN] = True # add selection col
            # set SELECT_COLUMN as first column
            columns_order = [CSVTmpUploader.SELECT_COLUMN] + [column for column in df.columns if column != CSVTmpUploader.SELECT_COLUMN]
            df = df.reindex(columns=columns_order)
            self._df = df
        except:
            etype, value, tb = sys.exc_info()
            error_msg = "".join(traceback.format_exception_only(etype, value))
            self._error = error_msg
    
    def load_csv(self, file: Optional[UploadedFile]) -> Optional[pd.DataFrame]:
        if file is None: return None
        
        new_csv = pd.read_csv(io.BytesIO(file.read()))
        if self._validate(new_csv):
            return new_csv
        
        raise CSVFormatError(f"Invalid Format: file must contain columns: {self._columns}, but {self._df.columns}")
    
    def _validate(self, data: pd.DataFrame) -> bool:
        if not self._columns: return True
        
        if self.strict:
            return all([column in data.columns for column in self._columns])
        else:
            return any([column in data.columns for column in self._columns])
    
    @property
    def df(self) -> Optional[pd.DataFrame]:
        if self._df is None: return 
        return self._df[self._df[CSVTmpUploader.SELECT_COLUMN]==True]
