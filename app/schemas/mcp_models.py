"""Pydantic models for Trello MCP Server tools."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class BaseToolResponse(BaseModel):
    success: bool
    error: Optional[dict] = None


class MemberResponse(BaseToolResponse):
    member: Optional[Dict[str, Any]] = None


class BoardListResponse(BaseToolResponse):
    boards: List[Dict[str, Any]] = []
    total_count: int = 0


class BoardResponse(BaseToolResponse):
    board: Optional[Dict[str, Any]] = None


class ListListResponse(BaseToolResponse):
    lists: List[Dict[str, Any]] = []
    total_count: int = 0


class CardListResponse(BaseToolResponse):
    cards: List[Dict[str, Any]] = []
    total_count: int = 0


class CardResponse(BaseToolResponse):
    card: Optional[Dict[str, Any]] = None


class ActionResponse(BaseToolResponse):
    message: Optional[str] = None
    card_id: Optional[str] = None
    list_id: Optional[str] = None
    comment_id: Optional[str] = None
    dry_run: bool = False
    request_body: Optional[Dict[str, Any]] = None
