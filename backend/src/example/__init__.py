"""
Example Domain.

This is a template domain showing the recommended structure.
Copy this folder when creating new domains.

Structure:
- router.py      - API endpoints (THIN, only HTTP concerns)
- service.py     - Business logic
- repository.py  - Database access
- models.py      - SQLAlchemy models
- schemas.py     - Pydantic schemas
- dependencies.py - Domain-specific Depends
- exceptions.py  - Domain exceptions
- constants.py   - Domain constants
"""

from src.example.router import router

__all__ = ["router"]
