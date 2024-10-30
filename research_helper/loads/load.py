import importlib
import json
import os
from typing import Any, Optional, Dict, List, Tuple

from research_helper.loads.serialize import Serializable

DEFAULT_NAMESPACES = [
    "research_heloper"
]

ALL_SERIALIZABLE_MAPPINGS = {}
DISALLOW_LOAD_FROM_PATH = {}

class Reviver:
    """Reviver for JSON objects."""

    def __init__(
        self,
        secret_map: Optional[dict[str, str]] = None,
        valid_namespaces: Optional[List[str]] = None,
        secret_from_env: bool = True,
        additional_import_mappings: Optional[
            Dict[Tuple[str, ...], Tuple[str, ...]]
        ] = None,
    ):
        """Initialize the reviver.

        Args:
            secrets_map: A map of secrets to load. If a secret is not found in
                the map, it will be loaded from the environment if `secrets_from_env`
                is True. Defaults to None.
            valid_namespaces: A list of additional namespaces (modules)
                to allow to be deserialized. Defaults to None.
            secrets_from_env: Whether to load secrets from the environment.
                Defaults to True.
            additional_import_mappings: A dictionary of additional namespace mappings
                You can use this to override default mappings or add new mappings.
                Defaults to None.
        """
        self.secret_from_env = secret_from_env
        self.secret_map = secret_map or dict()
        self.valid_namespaces = (
            [*DEFAULT_NAMESPACES, *valid_namespaces]
            if valid_namespaces
            else DEFAULT_NAMESPACES
        )
        self.additional_import_mappings = additional_import_mappings or dict()
        self.import_mappings = (
            {
                **ALL_SERIALIZABLE_MAPPINGS,
                **self.additional_import_mappings,
            }
            if self.additional_import_mappings
            else ALL_SERIALIZABLE_MAPPINGS
        )
    
    def __call__(self, value: Dict[str, Any]) -> Any:
        if (
            value.get("lc", None) == 1
            and value.get("type", None) == "secret"
            and value.get("id", None) is not None
        ):
            [key] = value["id"]
            if key in self.secret_map:
                return self.secret_map[key]
            else:
                if self.secret_from_env and key in os.environ and os.environ[key]:
                    return os.environ[key]
                raise KeyError(f'Missing key "{key}" in load(secrets_map)')
        
        if (
            value.get("lc", None) == 1
            and value.get("type", None) == "not_implemented"
            and value.get("id", None) is not None
        ):
            raise NotImplementedError(
                "Trying to load an object that doesn't implement "
                f"serialization: {value}"
            )

        if (
            value.get("lc", None) == 1
            and value.get("type", None) == "constructor"
            and value.get("id", None) is not None
        ):
            [*namespace, name] = value["id"]
            mapping_key = tuple(value["id"])
            
            if namespace[0] not in self.valid_namespaces:
                raise ValueError(f"Invalid namespace: {value}")
            # The root namespace ["langchain"] is not a valid identifier.
            elif namespace == ["research_helper"]:
                raise ValueError(f"Invalid namespace: {value}")
            # Has explicit import path.
            elif mapping_key in self.import_mappings:
                import_path = self.import_mappings[mapping_key]
                # Split into module and name
                import_dir, name = import_path[:-1], import_path[-1]
                # Import module
                mod = importlib.import_module(".".join(import_dir))
            elif namespace[0] in DISALLOW_LOAD_FROM_PATH:
                raise ValueError(
                    "Trying to deserialize something that cannot "
                    "be deserialized in current version of langchain-core: "
                    f"{mapping_key}."
                )
            # Otherwise, treat namespace as path.
            else:
                mod = importlib.import_module(".".join(namespace))
        
            cls = getattr(mod, name)
            
            # The class must be a subclass of Serializable.
            if not issubclass(cls, Serializable):
                raise ValueError(f"Invalid namespace: {value}")
            
            # We don't need to recurse on kwargs
            # as json.loads will do that for us.
            kwargs = value.get("kwargs", dict())
            return cls(**kwargs)

        return value

def loads(
    text: str,
    *,
    secrets_map: Optional[Dict[str, str]] = None,
    valid_namespaces: Optional[List[str]] = None,
    secrets_from_env: bool = True,
    additional_import_mappings: Optional[Dict[Tuple[str, ...], Tuple[str, ...]]] = None,
) -> Any:
    """Revive a LangChain class from a JSON string.
    Equivalent to `load(json.loads(text))`.

    Args:
        text: The string to load.
        secrets_map: A map of secrets to load. If a secret is not found in
            the map, it will be loaded from the environment if `secrets_from_env`
            is True. Defaults to None.
        valid_namespaces: A list of additional namespaces (modules)
            to allow to be deserialized. Defaults to None.
        secrets_from_env: Whether to load secrets from the environment.
            Defaults to True.
        additional_import_mappings: A dictionary of additional namespace mappings
            You can use this to override default mappings or add new mappings.
            Defaults to None.

    Returns:
        Revived LangChain objects.
    """
    return json.loads(
        text,
        object_hook=Reviver(
            secrets_map, valid_namespaces, secrets_from_env, additional_import_mappings
        ),
    )

def load(
    obj: Any,
    *,
    secrets_map: Optional[Dict[str, str]] = None,
    valid_namespaces: Optional[List[str]] = None,
    secrets_from_env: bool = True,
    additional_import_mappings: Optional[Dict[Tuple[str, ...], Tuple[str, ...]]] = None,
) -> Any:
    """Revive a LangChain class from a JSON object. Use this if you already
    have a parsed JSON object, eg. from `json.load` or `orjson.loads`.

    Args:
        obj: The object to load.
        secrets_map: A map of secrets to load. If a secret is not found in
            the map, it will be loaded from the environment if `secrets_from_env`
            is True. Defaults to None.
        valid_namespaces: A list of additional namespaces (modules)
            to allow to be deserialized. Defaults to None.
        secrets_from_env: Whether to load secrets from the environment.
            Defaults to True.
        additional_import_mappings: A dictionary of additional namespace mappings
            You can use this to override default mappings or add new mappings.
            Defaults to None.

    Returns:
        Revived LangChain objects.
    """
    reviver = Reviver(
        secrets_map, valid_namespaces, secrets_from_env, additional_import_mappings
    )

    def _load(obj: Any) -> Any:
        if isinstance(obj, dict):
            # Need to revive leaf nodes before reviving this node
            loaded_obj = {k: _load(v) for k, v in obj.items()}
            return reviver(loaded_obj)
        if isinstance(obj, list):
            return [_load(o) for o in  obj]
        return obj
    
    return _load(obj)
