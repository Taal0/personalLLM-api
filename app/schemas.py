from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Kullanıcı mesajı")
    session_id: str | None = Field(None, description="Mevcut oturum ID'si")
    new_session: bool = Field(False, description="Yeni oturum başlat")


class ChatResponse(BaseModel):
    reply: str
    model: str
    session_id: str
