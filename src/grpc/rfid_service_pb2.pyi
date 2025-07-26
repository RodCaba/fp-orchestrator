from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class HealthCheckRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HealthCheckResponse(_message.Message):
    __slots__ = ("status", "message")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    status: str
    message: str
    def __init__(self, status: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class RFIDPayload(_message.Message):
    __slots__ = ("device_id", "timestamp", "tags", "is_active")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    IS_ACTIVE_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    timestamp: float
    tags: _containers.RepeatedScalarFieldContainer[str]
    is_active: bool
    def __init__(self, device_id: _Optional[str] = ..., timestamp: _Optional[float] = ..., tags: _Optional[_Iterable[str]] = ..., is_active: bool = ...) -> None: ...

class RFIDPayloadResponse(_message.Message):
    __slots__ = ("device_id", "timestamp", "status")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    timestamp: float
    status: str
    def __init__(self, device_id: _Optional[str] = ..., timestamp: _Optional[float] = ..., status: _Optional[str] = ...) -> None: ...
