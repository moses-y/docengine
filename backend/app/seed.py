"""Idempotent demo data: four seeded accounts and two sample documents, one
already shared, so a reviewer can exercise sharing without any setup
(PRD §9). Run with `python -m app.seed`; safe to run repeatedly.
"""

from __future__ import annotations

import asyncio

from app.content.sanitize import sanitize_document
from app.database import SessionLocal
from app.models.share import ShareRole
from app.models.user import User
from app.repositories.document_repo import DocumentRepo
from app.repositories.share_repo import ShareRepo
from app.repositories.user_repo import UserRepo
from app.security import hash_password

_SEED_PASSWORD = "demo1234"

_SEED_USERS = [
    ("alice@ajaia.test", "Alice Owusu"),
    ("bob@ajaia.test", "Bob Kim"),
    ("carol@ajaia.test", "Carol Mensah"),
    ("dave@ajaia.test", "Dave Ochieng"),
]

_WELCOME_DOC = sanitize_document(
    {
        "type": "doc",
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 1},
                "content": [{"type": "text", "text": "Welcome to DocEngine"}],
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "This document is "},
                    {"type": "text", "text": "shared", "marks": [{"type": "bold"}]},
                    {"type": "text", "text": " with Bob as an editor."},
                ],
            },
            {
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "Try editing this list"}],
                            }
                        ],
                    },
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "Share it with someone else"}],
                            }
                        ],
                    },
                ],
            },
        ],
    }
)

_PRIVATE_DOC = sanitize_document(
    {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "This one is private to Alice — no one else has access.",
                    }
                ],
            }
        ],
    }
)


async def seed() -> None:
    async with SessionLocal() as db:
        user_repo = UserRepo(db)
        users: dict[str, User] = {}
        for email, name in _SEED_USERS:
            existing = await user_repo.get_by_email(email)
            if existing is None:
                existing = await user_repo.create(
                    email=email, display_name=name, password_hash=hash_password(_SEED_PASSWORD)
                )
                print(f"created user {email}")
            users[email] = existing

        doc_repo = DocumentRepo(db)
        alice = users["alice@ajaia.test"]
        bob = users["bob@ajaia.test"]

        existing_docs = await doc_repo.list_for_user(alice.id, "owned")
        if not existing_docs:
            welcome = await doc_repo.create(
                owner_id=alice.id, title="Welcome to DocEngine", content=_WELCOME_DOC
            )
            await doc_repo.create(
                owner_id=alice.id, title="Alice's private notes", content=_PRIVATE_DOC
            )
            await ShareRepo(db).upsert(
                document_id=welcome.id, user_id=bob.id, role=ShareRole.EDITOR, granted_by=alice.id
            )
            print("created sample documents and a share grant")
        else:
            print("sample documents already exist, skipping")

        await db.commit()

    print("\nSeeded accounts (password for all: demo1234):")
    for email, _ in _SEED_USERS:
        print(f"  {email}")


if __name__ == "__main__":
    asyncio.run(seed())
