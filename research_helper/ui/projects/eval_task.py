import streamlit as st
import pandas as pd
import os
import sys
import traceback
from typing import Optional, Any, Dict, List, Tuple, Type
from dataclasses import dataclass

from research_helper.evaluator import evaluators, EvaluatorBase
from research_helper.ui.components import ComponentBase, AddingList, RowComponentFactory, DictInput, TextInput, SelectiveInput, MultiCSVUploader
from research_helper.ui.projects.task_base import Task, TaskConfigComponent

name2evaluator = { evaluator.name: evaluator for evaluator in evaluators }


@dataclass
class EvalConfig:
    input_field: str
    example_field: str
    output_fields: List[Tuple[str, str]]
    evaluators: List[Tuple[str, EvaluatorBase]]
    df: pd.DataFrame

class Evaluation:    
    def __init__(self, eval_data_path: str, config: EvalConfig) -> None:
        self._data_path = eval_data_path
        
        self._config = config
        self._chache = config
        self._cols = self._get_cols()
        self._eval_df = self._load_data()
        self._save_data()
        
        self._view: Optional[EvaluationView] = None
    
    # return missing columns
    def _validate_data(self, data: pd.DataFrame) -> List[str]:
        missing_col = []
        if self._cols["input"] not in data.columns: missing_col.append(self._cols["input"])
        if self._cols["example"] not in data.columns: missing_col.append(self._cols["example"])
        for out_col in self._cols["outputs"]:
            if out_col not in data.columns: missing_col.append(out_col)
        for eval_col in self._cols["evals"]:
            if eval_col not in data.columns: missing_col.append(eval_col)
        return missing_col
    
    def _add_missing_col(self, data: pd.DataFrame, missing_col: List[str]) -> pd.DataFrame:
        io_fields = data.apply(
            lambda row: {
                "__input":   self._config.input_field.format(**row),
                "__example": row[self._config.example_field],
                **{
                    f"__{out_name}": out_format.format(**row)
                    for out_name, out_format in self._config.output_fields
                },
            }, axis=1, result_type="expand")
        
        eval_fields = io_fields.apply(
            lambda row: {
                f"{out_col_name}-{eval_name}": evaluator.evaluate(output=row[out_col_name], example=row["__example"])
                for out_col_name in self._cols["outputs"]
                for eval_name, evaluator in self._config.evaluators
            }, axis=1, result_type="expand")
        
        adding_col = pd.concat([io_fields, eval_fields], axis=1)
        adding_col = adding_col.drop(columns=[col for col in adding_col.columns if col not in missing_col])
        
        return pd.concat([data, adding_col], axis=1)
    
    def _load_data(self):
        try:
            data = pd.read_json(self._data_path, orient='records', lines=True)
        except Exception as e:
            data = self._config.df
        
        missing_col = self._validate_data(data)
        if not missing_col:
            return data
        else:
            return self._add_missing_col(data, missing_col=missing_col)
    
    def _save_data(self):
        self._eval_df.to_json(self._data_path, orient='records', lines=True, force_ascii=False)
    
    def _get_cols(self):
        return {
            "input": "__input",
            "example": "__example",
            "outputs": [f"__{out_name}" for out_name, format_ in self._config.output_fields],
            "evals": [f"__{out_name}-{eval_name}" for out_name, format_ in self._config.output_fields for eval_name, evaluator in self._config.evaluators],
        }
    
    def set_config(self, config: EvalConfig):
        self._config = config
        old_cols   = self._cols
        self._cols = self._get_cols()
        
        # update df
        data = self._eval_df if self._chache.df is config.df else config.df
        
        # delete changed field
        dropper = []
        if config.input_field != self._chache.input_field and old_cols["input"] in data.columns:
            dropper.append(old_cols["input"])
        if config.example_field != self._chache.example_field and old_cols["example"] in data.columns: # example
            dropper.append(old_cols["example"])
        for old_col_name, new_col_name, new_field, chache_field in zip(old_cols["outputs"], self._cols["outputs"], config.output_fields, self._chache.output_fields):
            if new_field[1] != chache_field[1]: # format changed
                # drop output col and eval col to reset them
                outcol_name = old_col_name
                dropper.extend([outcol_name]+[eval_col for eval_col in self._cols if eval_col.startswith(outcol_name)])
        
        data = data.drop(columns=dropper)
        
        missing_col = self._validate_data(data)
        self._eval_df = self._add_missing_col(data, missing_col=missing_col)
        
        self._chache = config
        self._view = None
        self._save_data()
    
    def get_info(self) -> Dict:
        infos = {}
        for col, dtype in self._eval_df.dtypes.items():
            if dtype is str:
                infos.update({col: {"mean-length": self._eval_df[col].str.len().mean()}})
            elif dtype in [int, float, bool]:
                infos.update({col: {"mean": self._eval_df[col].mean()}})
            else:
                pass
        return infos
    
    @property
    def name(self):
        return os.path.basename(self._data_path)
    
    @property
    def view(self):
        if self._view is None:
            self._view = EvaluationView(self)
        return self._view

@dataclass
class EvalData:
    input: Optional[str] = None
    example: Optional[str] = None 
    # タプルの辞書, キーは評価対象名, バリューは評価対象の出力と評価の組
    eval_data: Optional[Dict[str, Tuple[str, Dict[str, Any]]]] = None
    page: int = 0
    error: str = ""

class EvaluationView:
    def __init__(self, evaluation: Evaluation) -> None:
        self.evaluation = evaluation
        self._cursor = 0
    
    def jump_to(self, to: int):
        self._cursor = to % len(self.evaluation._eval_df)
    
    def next(self):
        self.jump_to(self._cursor+1)
    
    def prev(self):
        self.jump_to(self._cursor-1)
    
    def set(self, col: str, val: Any):
        self.evaluation._eval_df.loc[self._cursor, col] = val
        self.evaluation._save_data()
    
    def get(self):
        try:
            outputs = self.evaluation._eval_df.loc[self._cursor, self.evaluation._cols["outputs"]]
            evals   = self.evaluation._eval_df.loc[self._cursor, self.evaluation._cols["evals"]]
            eval_cols = self.evaluation._cols["evals"]
            eval_data = {
                out_name: (
                    outputs[out_name],
                    evals[[eval_col for eval_col in eval_cols if out_name in eval_col]].to_dict()
                )
                for out_name in self.evaluation._cols["outputs"]
            }
            return EvalData(
                input=self.evaluation._eval_df.loc[self._cursor, self.evaluation._cols["input"]],
                example=self.evaluation._eval_df.loc[self._cursor, self.evaluation._cols["example"]],
                eval_data=eval_data,
                page=self._cursor
            )
        except:
            etype, value, tb = sys.exc_info()
            error_msg = traceback.format_exception_only(etype, value)
            return EvalData(
                error=error_msg
            )

class EvalConfigPanel(TaskConfigComponent):
    eval_file = "eval_data.jsonl"
    
    def __init__(self, task_path: str) -> None:
        super().__init__(task_path)
        
        # eval task ではデータフレーム等の再結合等で csv ファイルが頻繁に書き換わる恐れがある
        # 処理軽量化のためオートセーブをオフ
        self._auto_save = False
        
        self._csv_uploader = MultiCSVUploader(dir_path=task_path)
        
        name_input_factory = RowComponentFactory(row_component_cls=TextInput, placeholder="name")
        format_input_factory = RowComponentFactory(row_component_cls=TextInput, placeholder="format")
        output_row_factory = RowComponentFactory(
            row_component_cls=DictInput,
            key_component_factory=name_input_factory,
            val_component_factory=format_input_factory
        )
        self._outputs_list = AddingList(label="Outputs", row_factory=output_row_factory)
        
        key_text_input = RowComponentFactory(row_component_cls=TextInput, placeholder="eval name")
        evaluator_select_factory = RowComponentFactory(SelectiveInput, placeholder="eval type", options=[e.name for e in evaluators])
        eval_row_factory = RowComponentFactory(
            row_component_cls=DictInput,
            key_component_factory=key_text_input,
            val_component_factory=evaluator_select_factory
        )
        self._evaluators_list = AddingList(label="Evaluators", row_factory=eval_row_factory)
        
        # initialize state
        self._outputs_list.set_values(self._config["outputs"])
        self._evaluators_list.set_values(self._config["evaluators"])
        
        self.error = ""
        self._evaluation = Evaluation(eval_data_path=self.task_path+"/"+self.eval_file, config=self.config)
    
    def draw_body(self) -> None:
        if self.error:
            st.error(self.error)
            self.error = ""
        
        data_col, config_col = st.tabs(["data", "config"])
        with data_col:
            self._csv_uploader.draw()
        
        with config_col:
            left_col, right_col = st.columns([0.5, 0.5])
            with left_col:
                st.text_area(
                    label="Input", key=self.task_id+"_in", value=self._config["input"],
                    on_change=lambda: self._update_config("input", st.session_state[self.task_id+"_in"])
                )
            with right_col:
                self._config["example"] = st.text_area(
                    label="Example", key=self.task_id+"_ex", value=self._config["example"],
                    on_change=lambda: self._update_config("example", st.session_state[self.task_id+"_ex"])
                )
            
            outputs_col, _, evals_col = st.columns([0.45, 0.1, 0.45])
            with outputs_col:
                self._config["outputs"] = self._outputs_list.draw()
            with evals_col:
                self._config["evaluators"] = self._evaluators_list.draw()
        
        with st.expander("columns"):
            if rhdf:=self._csv_uploader.get_rhdf():
                st.markdown("\n".join([f"- {{{col}}}" for col in rhdf.df.columns.to_list()]))
        
        st.button("FINALIZE", help="変更を保存", on_click=self._save_config)
    
    def _load_config(self) -> Dict:
        config = super()._load_config()
        config["task_type"] = "eval"
        if "input" not in config:
            config["input"] = ""
        if "example" not in config:
            config["example"] = ""
        if "outputs" not in config:
            config["outputs"] = []
        if "evaluators" not in config:
            config["evaluators"] = []
        return config
    
    def _save_config(self):
        super()._save_config()
        try:
            # reset eval with new config
            self._evaluation.set_config(self.config)
        except:
            etype, value, tb = sys.exc_info()
            error_msg = traceback.format_exception_only(etype, value)
            self.error = error_msg
    
    @property
    def config(self) -> Optional[EvalConfig]:
        output_fields = self._outputs_list.get_inputs()
        evaluators = [(col, name2evaluator[cls_name]()) for col, cls_name in self._evaluators_list.get_inputs()]
        rhdf = self._csv_uploader.get_rhdf()
        return EvalConfig(
            input_field=self._config["input"],
            example_field=self._config["example"],
            output_fields=output_fields,
            evaluators=evaluators,
            df=rhdf.df if rhdf else pd.DataFrame()
        )
    
    @property
    def evaluation(self):
        return self._evaluation

class ViewerBase(ComponentBase):
    def __init__(self, col_name: str, value: Any, eval_view: EvaluationView, key: Optional[str] = None) -> None:
        super().__init__(key)
        self._col_name = col_name
        self._value = value
        self._view = eval_view
    
    def set(self, value: Any):
        self._view.set(col=self._col_name, val=value)

class BoolViewer(ViewerBase):
    def draw(self) -> Any:
        st.button(
            label="O" if self._value else "X", key=self._key,
            on_click=lambda: self.set(not self._value)
        )

class TextViewer(ViewerBase):
    def draw(self) -> Any:
        st.text_input(
            label=" ", key=self._key, value=self._value, label_visibility="collapsed",
            on_change=lambda: self.set(st.session_state[self._key])
        )

class DefaultViewer(ViewerBase):
    def draw(self) -> Any:
        st.markdown(self._value)

TYPE2VIEWER = {
    bool: BoolViewer,
    str: TextViewer,
}

class EvalRow(ComponentBase):
    def __init__(self, label: str, eval_data: Tuple[str, Any], view: EvaluationView, key: Optional[str] = None) -> None:
        super().__init__(key)
        self._label = label.replace("__", "")
        self._eval_data = eval_data
        self._view = view
    
    def draw(self) -> None:
        right_rate = 0.5
        col_rate   = right_rate / len(self._eval_data[1]) if len(self._eval_data[1])>0 else 0.5
        
        with st.container(border=True):
            output_col, *eval_cols = st.columns([1-right_rate, *[col_rate]*len(self._eval_data[1])])
            with output_col:
                st.text(self._label)
                st.text(self._eval_data[0])
            
            evals: Dict = self._eval_data[1]
            for eval_col, eval_value in zip(eval_cols, evals.items()):
                with eval_col:
                    st.text(eval_value[0].replace("__", ""))
                    cls: Type[ViewerBase] = TYPE2VIEWER.get(type(eval_value[1]), DefaultViewer)
                    evaluator: ViewerBase = cls(col_name=eval_value[0], value=eval_value[1], eval_view=self._view)
                    evaluator.draw()

class EvalViewPanel(ComponentBase):
    def __init__(self, config_panel: EvalConfigPanel) -> None:
        super().__init__()
        
        self._config = config_panel
    
    def _jump_to(self, input: str):
        try:
            self._config.evaluation.view.jump_to(int(input))
        except:
            pass
    
    def draw(self) -> Any:
        if self._config.evaluation._eval_df.empty: return
        
        view = self._config.evaluation.view
        data = view.get()
        
        if data.error:
            st.error(data.error)
            return
        
        # Page Content
        ## Header
        _, curr_page, slash, page_count = st.columns([12, 1, 0.5, 1], gap="small")
        with curr_page:
            st.text_input(
                " ", value=data.page, key=self._key+"_page", label_visibility="collapsed",
                on_change=lambda: self._jump_to(st.session_state[self._key+"_page"])
            )
        with slash:
            st.text("/")
        with page_count:
            st.text(len(self._config.evaluation._eval_df)-1)
        
        ## Body
        with st.container(height=200, border=False):
            left_col, right_col = st.columns([0.5, 0.5])
            with left_col:
                st.text_area("Input", data.input, height=200, disabled=True)
                # with st.container(border=True, height=200):
                #     st.text("Input")
                #     st.text(data.input)
            
            with right_col:
                st.text_area("Example", data.example, height=200, disabled=True)
                # with st.container(border=True, height=200):
                #     st.text("Example")
                #     st.text(data.example)
        
        with st.container(height=250, border=False):
            for model_name, eval_data in data.eval_data.items():
                row = EvalRow(label=model_name, eval_data=eval_data, view=view)
                row.draw()
        
        ## footer
        left_col, _, right_col = st.columns([1, 12, 1])
        with left_col:
            st.button("←", key=self._key+"_lb", on_click=view.prev)
        with right_col:
            st.button("→", key=self._key+"_rb", on_click=view.next)

class EvalTask(Task):
    task_type: str = "eval-task"
    
    def __init__(self, project_id: str, task_id: str = None) -> None:
        super().__init__(project_id, task_id)
        
        self._config = EvalConfigPanel(task_path=self.task_path)
        self._viewer = EvalViewPanel(self._config)
    
    def draw(self) -> Any:
        setup_tab, eval_tab, data_tab = st.tabs(["setup", "evaluation", "data"])
        with setup_tab:
            self._config.draw()
        with eval_tab:
            self._viewer.draw()
        with data_tab:
            st.subheader(self._config.evaluation.name)
            st.dataframe(self._config.evaluation._eval_df, height=400)
            with st.expander("Analytics"):
                st.json(self._config.evaluation.get_info())
    