"""Data-access layer. Repositories speak SQLAlchemy and return ORM objects
(or None); they know nothing about HTTP status codes or Pydantic schemas.
Services compose repositories and enforce business rules on top of them.
"""
