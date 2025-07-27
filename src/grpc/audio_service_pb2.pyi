from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AudioPayload(_message.Message):
    __slots__ = ("session_id", "sample_rate", "channels", "features", "parameters")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
    CHANNELS_FIELD_NUMBER: _ClassVar[int]
    FEATURES_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    sample_rate: int
    channels: int
    features: AudioFeature
    parameters: ProcessingParameters
    def __init__(self, session_id: _Optional[str] = ..., sample_rate: _Optional[int] = ..., channels: _Optional[int] = ..., features: _Optional[_Union[AudioFeature, _Mapping]] = ..., parameters: _Optional[_Union[ProcessingParameters, _Mapping]] = ...) -> None: ...

class AudioFeature(_message.Message):
    __slots__ = ("feature_type", "feature_shape", "feature_data", "feature_parameters", "data_type")
    FEATURE_TYPE_FIELD_NUMBER: _ClassVar[int]
    FEATURE_SHAPE_FIELD_NUMBER: _ClassVar[int]
    FEATURE_DATA_FIELD_NUMBER: _ClassVar[int]
    FEATURE_PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    DATA_TYPE_FIELD_NUMBER: _ClassVar[int]
    feature_type: str
    feature_shape: _containers.RepeatedScalarFieldContainer[int]
    feature_data: bytes
    feature_parameters: FeatureParameters
    data_type: str
    def __init__(self, feature_type: _Optional[str] = ..., feature_shape: _Optional[_Iterable[int]] = ..., feature_data: _Optional[bytes] = ..., feature_parameters: _Optional[_Union[FeatureParameters, _Mapping]] = ..., data_type: _Optional[str] = ...) -> None: ...

class FeatureParameters(_message.Message):
    __slots__ = ("n_fft", "hop_length", "n_mels", "f_min", "f_max", "target_sample_rate", "power")
    N_FFT_FIELD_NUMBER: _ClassVar[int]
    HOP_LENGTH_FIELD_NUMBER: _ClassVar[int]
    N_MELS_FIELD_NUMBER: _ClassVar[int]
    F_MIN_FIELD_NUMBER: _ClassVar[int]
    F_MAX_FIELD_NUMBER: _ClassVar[int]
    TARGET_SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
    POWER_FIELD_NUMBER: _ClassVar[int]
    n_fft: int
    hop_length: int
    n_mels: int
    f_min: int
    f_max: int
    target_sample_rate: int
    power: float
    def __init__(self, n_fft: _Optional[int] = ..., hop_length: _Optional[int] = ..., n_mels: _Optional[int] = ..., f_min: _Optional[int] = ..., f_max: _Optional[int] = ..., target_sample_rate: _Optional[int] = ..., power: _Optional[float] = ...) -> None: ...

class ProcessingParameters(_message.Message):
    __slots__ = ("target_sample_rate", "target_length", "normalize", "normalization_method", "trim_strategy")
    TARGET_SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
    TARGET_LENGTH_FIELD_NUMBER: _ClassVar[int]
    NORMALIZE_FIELD_NUMBER: _ClassVar[int]
    NORMALIZATION_METHOD_FIELD_NUMBER: _ClassVar[int]
    TRIM_STRATEGY_FIELD_NUMBER: _ClassVar[int]
    target_sample_rate: int
    target_length: int
    normalize: bool
    normalization_method: str
    trim_strategy: str
    def __init__(self, target_sample_rate: _Optional[int] = ..., target_length: _Optional[int] = ..., normalize: bool = ..., normalization_method: _Optional[str] = ..., trim_strategy: _Optional[str] = ...) -> None: ...

class AudioPayloadResponse(_message.Message):
    __slots__ = ("session_id", "status", "message")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    status: str
    message: str
    def __init__(self, session_id: _Optional[str] = ..., status: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

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
