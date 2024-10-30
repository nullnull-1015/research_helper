import os
from research_helper.dataframe.joiner import RHDataFrameAdapter

class CSV:
    def __init__(self, path: str, rhdf: RHDataFrameAdapter) -> None:
        self.path = path
        self.name = os.path.basename(self.path)
        self.rhdf = rhdf
    
    def delete(self):
        if os.path.isfile(self.path):
            os.remove(self.path)