"""Bounded public requests, independent of the local Studio command surface."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Brief(RequestModel):
    title: str = Field(min_length=1, max_length=120)
    idea: str = Field(default="", max_length=4000)
    lyrics: str = Field(min_length=1, max_length=6000)
    caption: str = Field(min_length=1, max_length=1600)
    language: Literal["en", "zh", "ja", "mixed"] = "mixed"
    duration: int = Field(default=90, ge=30, le=180)
    bpm: int = Field(default=100, ge=40, le=200)
    key: str = Field(default="C major", pattern=r"^[A-G](?:#|b)? (?:major|minor)$")


class Generate(RequestModel):
    brief: Brief
    rights_confirmed: bool
    visibility: Literal["private", "public"] = "private"

    @field_validator("rights_confirmed")
    @classmethod
    def require_rights(cls, value):
        if value is not True:
            raise ValueError("Rights confirmation required")
        return value


class Draft(Brief):
    title: str = Field(default="", max_length=120)
    lyrics: str = Field(default="", max_length=6000)
    caption: str = Field(default="", max_length=1600)


class ChatMessage(RequestModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class Chat(RequestModel):
    message: str = Field(min_length=1, max_length=4000)
    brief: Draft | None = None
    history: list[ChatMessage] = Field(default_factory=list, max_length=12)

    @field_validator("history")
    @classmethod
    def bounded_history(cls, value):
        if sum(len(item.content) for item in value) > 16000:
            raise ValueError("Conversation context is too long")
        return value


class AgentReply(RequestModel):
    message: str = Field(min_length=1, max_length=1600)
    brief: Draft


class Visibility(RequestModel):
    visibility: Literal["private", "public"]


class Reaction(RequestModel):
    active: bool


class Comment(RequestModel):
    text: str = Field(min_length=1, max_length=1000)


class Report(RequestModel):
    reason: str = Field(min_length=3, max_length=1000)


class Invite(RequestModel):
    code: str = Field(min_length=20, max_length=128)


class CreatorError(Exception):
    def __init__(self, code: str, status: int = 400):
        self.code, self.status = code, status
        super().__init__(code)


# Owner-approved launch targets, 2026-10-09. Store products still need qualification.
PLANS = {
    "free": {"name": "Free", "renders": 2, "agent_turns_per_day": 10, "active_jobs": 1, "target_usd": "0"},
    "creator": {"name": "Creator", "renders": 20, "agent_turns_per_day": 50, "active_jobs": 2, "target_usd": "9.99"},
    "studio": {"name": "Studio", "renders": 80, "agent_turns_per_day": 150, "active_jobs": 3, "target_usd": "29.99"},
}

TERMS_VERSION = "2026-10-09"
