from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ChatRequest(_message.Message):
    __slots__ = ("message", "history", "session_id")
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    HISTORY_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    message: str
    history: _containers.RepeatedCompositeFieldContainer[MessageHistory]
    session_id: str
    def __init__(self, message: _Optional[str] = ..., history: _Optional[_Iterable[_Union[MessageHistory, _Mapping]]] = ..., session_id: _Optional[str] = ...) -> None: ...

class MessageHistory(_message.Message):
    __slots__ = ("role", "content")
    ROLE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    role: str
    content: str
    def __init__(self, role: _Optional[str] = ..., content: _Optional[str] = ...) -> None: ...

class ChatResponse(_message.Message):
    __slots__ = ("answer", "sources", "session_id")
    ANSWER_FIELD_NUMBER: _ClassVar[int]
    SOURCES_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    answer: str
    sources: _containers.RepeatedCompositeFieldContainer[Source]
    session_id: str
    def __init__(self, answer: _Optional[str] = ..., sources: _Optional[_Iterable[_Union[Source, _Mapping]]] = ..., session_id: _Optional[str] = ...) -> None: ...

class Source(_message.Message):
    __slots__ = ("doc_name", "page", "score")
    DOC_NAME_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    doc_name: str
    page: int
    score: float
    def __init__(self, doc_name: _Optional[str] = ..., page: _Optional[int] = ..., score: _Optional[float] = ...) -> None: ...
