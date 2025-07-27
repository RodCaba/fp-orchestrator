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
    __slots__ = ("device_id", "tags", "current_tags")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    CURRENT_TAGS_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    tags: _containers.RepeatedScalarFieldContainer[str]
    current_tags: int
    def __init__(self, device_id: _Optional[str] = ..., tags: _Optional[_Iterable[str]] = ..., current_tags: _Optional[int] = ...) -> None: ...

class RFIDPayloadResponse(_message.Message):
    __slots__ = ("device_id", "status")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    status: str
    def __init__(self, device_id: _Optional[str] = ..., status: _Optional[str] = ...) -> None: ...
