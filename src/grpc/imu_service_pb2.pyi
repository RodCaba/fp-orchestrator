from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class IMUPayload(_message.Message):
    __slots__ = ("device_id", "data")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    data: SensorData
    def __init__(self, device_id: _Optional[str] = ..., data: _Optional[_Union[SensorData, _Mapping]] = ...) -> None: ...

class SensorData(_message.Message):
    __slots__ = ("sensor_type", "values")
    SENSOR_TYPE_FIELD_NUMBER: _ClassVar[int]
    VALUES_FIELD_NUMBER: _ClassVar[int]
    sensor_type: str
    values: SensorValues
    def __init__(self, sensor_type: _Optional[str] = ..., values: _Optional[_Union[SensorValues, _Mapping]] = ...) -> None: ...

class IMUPayloadResponse(_message.Message):
    __slots__ = ("device_id", "status")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    status: str
    def __init__(self, device_id: _Optional[str] = ..., status: _Optional[str] = ...) -> None: ...

class SensorValues(_message.Message):
    __slots__ = ("standard", "orientation")
    STANDARD_FIELD_NUMBER: _ClassVar[int]
    ORIENTATION_FIELD_NUMBER: _ClassVar[int]
    standard: StandardSensorValues
    orientation: OrientationSensorValues
    def __init__(self, standard: _Optional[_Union[StandardSensorValues, _Mapping]] = ..., orientation: _Optional[_Union[OrientationSensorValues, _Mapping]] = ...) -> None: ...

class StandardSensorValues(_message.Message):
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
