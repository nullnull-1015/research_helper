import os
import sys
import streamlit as st
import importlib
import inspect
import time
from typing import Union, List

from streamlit.runtime.uploaded_file_manager import UploadedFile
from langchain_core.runnables import Runnable
from langchain_core import runnables

from research_helper.ui.components.base import ComponentBase

MODEL_FILE_NAME = "user_model.py"
BUILT_IN_RUNNABLES = [runnable[1] for runnable in inspect.getmembers(runnables, inspect.isclass) if issubclass(runnable[1], Runnable)]

class ModelNotFoundError(Exception):
    pass

def path2module_name(path: str):
    if path.startswith(("/", "./")):
        path = path.split("/", maxsplit=1)[-1] # remove "./" or "/" e.x.) ./a/b/c.py -> a/b/c.py
    module_name, ext = os.path.splitext(path)  # e.x.) a/b/c.py -> a/b/c
    module_name = module_name.replace("/", ".")       # e.x.) a/b/c -> a.b.c
    return module_name

class ModelUploader(ComponentBase):
    def __init__(self, dir_path: str) -> None:
        super().__init__(dir_path+"-uploader")
        self.dir_path = dir_path if not dir_path.endswith("/") else dir_path[:-1]
        self.model_path = self.dir_path+ "/" + MODEL_FILE_NAME
        
        try:
            self._model_cls, self._model = self._load_model_cls(self.model_path)
        except Exception as e:
            print(e)
            self._model_cls = None
            self._model = None
        self._error: str = None
    
    def draw(self) -> None:        
        if self._error:
            st.error(self._error)
        elif self._model_cls:
            st.code(inspect.getsource(self._model_cls), language="python")
        st.file_uploader(
            "Upload your MODEL",
            key=self._key,
            type=["py"],
            on_change=lambda: self._upload(st.session_state[self._key])
        )
    
    def _reset_field(self):
        self._model_cls = None
        self._model = None
        self._error = None
    
    def _load_model_cls(self, model_path: str) -> type:
        # prepare module path
        module_name = path2module_name(model_path)
        
        # import
        module = importlib.import_module(module_name)
        module = importlib.reload(module)
        user_runnables = [
            {
                "cls"    : cls_info[1],
                "parents": cls_info[1].__mro__
            }
            for cls_info in inspect.getmembers(module, inspect.isclass)
            if issubclass(cls_info[1], Runnable)
        ]
        
        if user_runnables:
            # 継承が深い順にソート
            sorted_runnables = sorted(user_runnables, key=lambda cls_info: len(cls_info["parents"]), reverse=True)
            
            for user_runnable in user_runnables:
                model_cls: Runnable = user_runnable["cls"]
                if model_cls.name == "entry_point":
                    # もし "entry_point" という名前の ruunable があれば、それを model とする。
                    return model_cls, model_cls()
            
            # otherwise
            # ユーザが定義した runnable のうち継承が最も深いものを model とする。
            # 例えば research_helper.models.Model を 継承した SubModel があった場合 SubModel が対象となる
            model_cls = sorted_runnables[0]["cls"]
            return model_cls, model_cls()
        
        raise ModelNotFoundError("You need to define your model extending langchain_core.runnables.Runnable")
    
    def _upload(self, uploaded_file: UploadedFile) -> None:
        self._reset_field()
        if not uploaded_file: return
        
        with open(self.model_path, "wb") as fw:
            fw.write(uploaded_file.read())
            
            # TODO: 原因究明
            # ファイルの更新を確定させる
            # sleep しないと、<class 'KeyError'> 'user_model' になる
            fw.flush()
            time.sleep(0.5)
        
        try:
            self._model_cls, self._model = self._load_model_cls(self.model_path)
        except Exception as e:
            etype, value, tb = sys.exc_info()
            self._error = str(e.with_traceback(tb))
    
    
    @property
    def model(self) -> Union[None, Runnable]:
        return self._model
