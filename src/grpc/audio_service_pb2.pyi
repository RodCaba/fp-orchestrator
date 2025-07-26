from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AudioPayload(_message.Message):
    __slots__ = ("session_id", "timestamp", "original_file_path", "audio_format", "sample_rate", "channels", "features", "parameters")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    ORIGINAL_FILE_PATH_FIELD_NUMBER: _ClassVar[int]
    AUDIO_FORMAT_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
    CHANNELS_FIELD_NUMBER: _ClassVar[int]
    FEATURES_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    timestamp: int
    original_file_path: str
    audio_format: str
    sample_rate: int
    channels: int
    features: _containers.RepeatedCompositeFieldContainer[AudioFeature]
    parameters: ProcessingParameters
    def __init__(self, session_id: _Optional[str] = ..., timestamp: _Optional[int] = ..., original_file_path: _Optional[str] = ..., audio_format: _Optional[str] = ..., sample_rate: _Optional[int] = ..., channels: _Optional[int] = ..., features: _Optional[_Iterable[_Union[AudioFeature, _Mapping]]] = ..., parameters: _Optional[_Union[ProcessingParameters, _Mapping]] = ...) -> None: ...

class AudioFeature(_message.Message):
    __slots__ = ("feature_type", "feature_shape", "feature_parameters")
    FEATURE_TYPE_FIELD_NUMBER: _ClassVar[int]
    FEATURE_SHAPE_FIELD_NUMBER: _ClassVar[int]
    FEATURE_PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    feature_type: str
    feature_shape: _containers.RepeatedScalarFieldContainer[int]
    feature_parameters: FeatureParameters
    def __init__(self, feature_type: _Optional[str] = ..., feature_shape: _Optional[_Iterable[int]] = ..., feature_parameters: _Optional[_Union[FeatureParameters, _Mapping]] = ...) -> None: ...

class FeatureParameters(_message.Message):
    __slots__ = ("n_ftt", "hop_length", "n_mels", "f_min", "f_max")
    N_FTT_FIELD_NUMBER: _ClassVar[int]
    HOP_LENGTH_FIELD_NUMBER: _ClassVar[int]
    N_MELS_FIELD_NUMBER: _ClassVar[int]
    F_MIN_FIELD_NUMBER: _ClassVar[int]
    F_MAX_FIELD_NUMBER: _ClassVar[int]
    n_ftt: int
    hop_length: int
    n_mels: int
    f_min: int
    f_max: int
    def __init__(self, n_ftt: _Optional[int] = ..., hop_length: _Optional[int] = ..., n_mels: _Optional[int] = ..., f_min: _Optional[int] = ..., f_max: _Optional[int] = ...) -> None: ...

class ProcessingParameters(_message.Message):
    __slots__ = ("target_sample_rate", "target_length", "normalize")
    TARGET_SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
    TARGET_LENGTH_FIELD_NUMBER: _ClassVar[int]
    NORMALIZE_FIELD_NUMBER: _ClassVar[int]
    target_sample_rate: int
    target_length: int
    normalize: bool
    def __init__(self, target_sample_rate: _Optional[int] = ..., target_length: _Optional[int] = ..., normalize: bool = ...) -> None: ...

class AudioPayloadResponse(_message.Message):
    __slots__ = ("session_id", "timestamp", "status")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    timestamp: int
    status: str
    def __init__(self, session_id: _Optional[str] = ..., timestamp: _Optional[int] = ..., status: _Optional[str] = ...) -> None: ...

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
