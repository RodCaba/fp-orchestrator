from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class IMUPayload(_message.Message):
    __slots__ = ("device_id", "timestamp", "accelerometer", "gyroscope", "gravity", "total_acceleration", "orientation")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    ACCELEROMETER_FIELD_NUMBER: _ClassVar[int]
    GYROSCOPE_FIELD_NUMBER: _ClassVar[int]
    GRAVITY_FIELD_NUMBER: _ClassVar[int]
    TOTAL_ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    ORIENTATION_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    timestamp: float
    accelerometer: _containers.RepeatedCompositeFieldContainer[SensorValues]
    gyroscope: _containers.RepeatedCompositeFieldContainer[SensorValues]
    gravity: _containers.RepeatedCompositeFieldContainer[SensorValues]
    total_acceleration: _containers.RepeatedCompositeFieldContainer[SensorValues]
    orientation: _containers.RepeatedCompositeFieldContainer[OrientationSensorValues]
    def __init__(self, device_id: _Optional[str] = ..., timestamp: _Optional[float] = ..., accelerometer: _Optional[_Iterable[_Union[SensorValues, _Mapping]]] = ..., gyroscope: _Optional[_Iterable[_Union[SensorValues, _Mapping]]] = ..., gravity: _Optional[_Iterable[_Union[SensorValues, _Mapping]]] = ..., total_acceleration: _Optional[_Iterable[_Union[SensorValues, _Mapping]]] = ..., orientation: _Optional[_Iterable[_Union[OrientationSensorValues, _Mapping]]] = ...) -> None: ...

class IMUPayloadResponse(_message.Message):
    __slots__ = ("device_id", "timestamp", "status")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    timestamp: float
    status: str
    def __init__(self, device_id: _Optional[str] = ..., timestamp: _Optional[float] = ..., status: _Optional[str] = ...) -> None: ...

class SensorValues(_message.Message):
    __slots__ = ("x", "y", "z")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    z: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., z: _Optional[float] = ...) -> None: ...

class OrientationSensorValues(_message.Message):
    __slots__ = ("qx", "qy", "qz", "qw", "roll", "pitch", "yaw")
    QX_FIELD_NUMBER: _ClassVar[int]
    QY_FIELD_NUMBER: _ClassVar[int]
    QZ_FIELD_NUMBER: _ClassVar[int]
    QW_FIELD_NUMBER: _ClassVar[int]
    ROLL_FIELD_NUMBER: _ClassVar[int]
    PITCH_FIELD_NUMBER: _ClassVar[int]
    YAW_FIELD_NUMBER: _ClassVar[int]
    qx: float
    qy: float
    qz: float
    qw: float
    roll: float
    pitch: float
    yaw: float
    def __init__(self, qx: _Optional[float] = ..., qy: _Optional[float] = ..., qz: _Optional[float] = ..., qw: _Optional[float] = ..., roll: _Optional[float] = ..., pitch: _Optional[float] = ..., yaw: _Optional[float] = ...) -> None: ...

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
