import json
from typing import Any

from research_helper.loads.serialize import Serializable, to_json_not_implemented

# serialization implementation
# refer: https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/load/dump.py

def default(obj: Any) -> Any:
    """Return a default value for a Serializable object or
    a SerializedNotImplemented object.

    Args:
        obj: The object to serialize to json if it is a Serializable object.

    Returns:
        A json serializable object or a SerializedNotImplemented object.
    """
    if isinstance(obj, Serializable):
        return obj.to_json()
    else:
        return to_json_not_implemented(obj)


def dumps(obj: Any, *, pretty: bool = False, **kwargs: Any) -> str:
    """Return a json string representation of an object.

    Args:
        obj: The object to dump.
        pretty: Whether to pretty print the json. If true, the json will be
            indented with 2 spaces (if no indent is provided as part of kwargs).
            Default is False.
        kwargs: Additional arguments to pass to json.dumps

    Returns:
        A json string representation of the object.
    """
    if "default" in kwargs:
        raise ValueError("`default` should not be passed to dumps")
    else:
        try:
            if pretty:
                indent = kwargs("indent", 2)
                return json.dumps(obj, default=default, indent=indent, **kwargs)
            else:
                return json.dumps(obj, default=default, **kwargs)
        except:
            if pretty:
                indent = kwargs("indent", 2)
                return json.dumps(to_json_not_implemented(obj), indent=indent, **kwargs)
            else:
                return json.dumps(to_json_not_implemented(obj), **kwargs)


def dumpd(obj: Any) -> Any:
    """Return a dict representation of an object.

    Note:
        Unfortunately this function is not as efficient as it could be
        because it first dumps the object to a json string and then loads it
        back into a dictionary.

    Args:
        obj: The object to dump.

    Returns:
        dictionary that can be serialized to json using json.dumps
    """
    return json.loads(dumps(obj))
