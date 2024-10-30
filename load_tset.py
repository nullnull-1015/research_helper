from research_helper.schemas.trace import TraceListSerializable

import json

with open("trace.log") as r:
    loaded = json.load(r)

trace_list = TraceListSerializable(**loaded)

print(trace_list.traces)