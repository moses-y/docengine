"""ORM models. Import every model here so Alembic's autogenerate and
`Base.metadata.create_all` (used only by tests) can discover them all
from a single import of `app.models`.
"""

from app.models.attachment import Attachment
from app.models.document import Document
from app.models.share import DocumentShare, ShareRole
from app.models.user import User
from app.models.version import DocumentVersion

__all__ = [
    "Attachment",
    "Document",
    "DocumentShare",
    "DocumentVersion",
    "ShareRole",
    "User",
]
