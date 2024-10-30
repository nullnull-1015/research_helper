from uuid import UUID

from research_helper.loads.serialize import Serializable, SerializedConstructor, SerializedNotImplemented

class UUIDSerializable(Serializable):
    uuid: UUID
    
    def to_json(self) -> SerializedConstructor | SerializedNotImplemented:
        return super().to_json()