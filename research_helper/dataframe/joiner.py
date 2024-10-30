import pandas as pd
from abc import ABC, abstractmethod
from typing import Optional, Union, Iterable, Hashable, List
from pandas._typing import MergeHow, IndexLabel, AnyArrayLike, Suffixes, Axis, HashableT

class RHDataFrame(ABC):
    """ DataFrame for Research_Helper """
    @property
    @abstractmethod
    def df(self) -> pd.DataFrame:
        pass

class RHDataFrameAdapter(RHDataFrame):
    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df
    
    @property
    def df(self) -> pd.DataFrame:
        return self._df
        

class CombinedRHDataFrameBase(RHDataFrame):
    def __init__(self, left: RHDataFrame, right: RHDataFrame) -> None:
        super().__init__()
        
        self._left  = left
        self._right = right
        self._df = None
    
    @abstractmethod
    def _join(self, left: RHDataFrame, right: RHDataFrame) -> pd.DataFrame:
        pass
    
    @property
    def df(self) -> pd.DataFrame:
        if self._df is None:
            self._df = self._join(self._left, self._right)
        return self._df

class MergedRHDataFrame(CombinedRHDataFrameBase):
    def __init__(
        self,
        left: RHDataFrame, right: RHDataFrame,
        how: MergeHow = 'inner',
        on: Union[IndexLabel, AnyArrayLike, None] = None,
        left_on: Union[IndexLabel, AnyArrayLike, None] = None,
        right_on: Union[IndexLabel, AnyArrayLike, None] = None,
        left_index: bool = False,
        right_index: bool = False,
        sort: bool = False,
        suffixes: Suffixes = ("_x", "_y"),
        copy: Optional[bool] = None,
        indicator: Union[str, bool] = False,
        validate: Optional[str] = None,
    ) -> None:
        """ https://pandas.pydata.org/docs/reference/api/pandas.merge.html """
        super().__init__(left, right)
        self._args = {
            "how": how,
            "on": on,
            "left_on": left_on,
            "right_on": right_on,
            'right_index': right_index,
            'left_index': left_index,
            'sort': sort,
            'suffixes': suffixes,
            'copy': copy,
            'indicator': indicator,
            'validate': validate,
        }
    
    def _join(self, left: RHDataFrame, right: RHDataFrame) -> pd.DataFrame:
        return pd.merge(left.df, right.df, **self._args)

class ConcatedRHDataFrame(CombinedRHDataFrameBase):
    def __init__(
        self,
        left: RHDataFrame, right: RHDataFrame,
        axis: Axis = 0,
        join: str = "outer",
        ignore_index: bool = True,
        keys: Optional[Iterable[Hashable]] = None,
        levels=None,
        names: Optional[List[HashableT]] = None,
        verify_integrity: bool = False,
        sort: bool = False,
        copy: Optional[bool] = None,
    ) -> None:
        super().__init__(left, right)
        self._args = {
            'axis': axis,
            'join': join,
            'ignore_index': ignore_index,
            'keys': keys,
            'levels': levels,
            'names': names,
            'verify_integrity': verify_integrity,
            'sort': sort,
            'copy': copy,
        }
    
    def _join(self, left: RHDataFrame, right: RHDataFrame) -> pd.DataFrame:
        return pd.concat([left.df, right.df], **self._args)
