"""Aggregation of all API routers."""

from __future__ import annotations

from fastapi import APIRouter

from accountsvc.api import users

api_router = APIRouter()
api_router.include_router(users.router)
