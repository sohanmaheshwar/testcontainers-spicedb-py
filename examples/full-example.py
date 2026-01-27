"""
Example: testing fine-grained authorization for a RAG pipeline using:
- testcontainers-spicedb-py (SpiceDBContainer)
- Authzed Python client
- pytest
run pytest full-example.py -v 
"""

import pytest
from testcontainers_spicedb import SpiceDBContainer

from authzed.api.v1 import (
    InsecureClient,
    WriteSchemaRequest,
    WriteRelationshipsRequest,
    RelationshipUpdate,
    Relationship,
    CheckPermissionRequest,
    CheckPermissionResponse,
    ObjectReference,
    SubjectReference,
)


# --- Fixtures ---


@pytest.fixture(scope="function")
def spicedb_container():
    """Provide a fresh SpiceDB container for each test."""
    with SpiceDBContainer(image="authzed/spicedb:v1.47.1") as spicedb:
        yield spicedb


@pytest.fixture(scope="function")
def spicedb_client(spicedb_container):
    """Create an Authzed client connected to the test container (no TLS)."""
    return InsecureClient(
        spicedb_container.get_endpoint(),
        spicedb_container.get_secret_key(),
    )


# --- Tests ---


def test_rag_document_permissions(spicedb_client):
    _setup_test_data(spicedb_client)

    assert _can_read(spicedb_client, "alice", "doc1")      # owner
    assert not _can_read(spicedb_client, "bob", "doc1")    # not granted

    assert _can_read(spicedb_client, "bob", "doc2")        # viewer
    assert _can_read(spicedb_client, "charlie", "doc3")    # viewer

    assert not _can_read(spicedb_client, "charlie", "doc1")
    assert not _can_read(spicedb_client, "charlie", "doc2")


def test_rag_post_filter_authorization(spicedb_client):
    _setup_test_data(spicedb_client)

    retrieved_docs = ["doc1", "doc2", "doc3"]  # simulated vector DB results
    authorized_docs = filter_docs_user_can_read(spicedb_client, "charlie", retrieved_docs)

    assert authorized_docs == ["doc3"]


def test_no_access_returns_empty_context(spicedb_client):
    _setup_test_data(spicedb_client)

    retrieved_docs = ["doc1", "doc2"]
    authorized_docs = filter_docs_user_can_read(spicedb_client, "charlie", retrieved_docs)

    assert authorized_docs == []


# --- Helpers ---


def filter_docs_user_can_read(client, user_id: str, doc_ids: list[str]) -> list[str]:
    """Post-filter vector DB hits to only documents the user can read."""
    return [doc_id for doc_id in doc_ids if _can_read(client, user_id, doc_id)]


def _can_read(client, user_id: str, doc_id: str) -> bool:
    resp = client.CheckPermission(
        CheckPermissionRequest(
            resource=ObjectReference(object_type="document", object_id=doc_id),
            permission="read",
            subject=SubjectReference(
                object=ObjectReference(object_type="user", object_id=user_id)
            ),
        )
    )
    return resp.permissionship == CheckPermissionResponse.PERMISSIONSHIP_HAS_PERMISSION


def _setup_test_data(client) -> None:
    """
    Schema: document has an owner and optional viewers.
    Permission read = owner OR viewer.
    """
    schema = """
    definition user {}

    definition document {
      relation owner: user
      relation viewer: user
      permission read = owner + viewer
    }
    """
    client.WriteSchema(WriteSchemaRequest(schema=schema))

    updates = [
        _touch_rel("document", "doc1", "owner", "user", "alice"),
        _touch_rel("document", "doc2", "viewer", "user", "bob"),
        _touch_rel("document", "doc3", "viewer", "user", "alice"),
        _touch_rel("document", "doc3", "viewer", "user", "bob"),
        _touch_rel("document", "doc3", "viewer", "user", "charlie"),
    ]
    client.WriteRelationships(WriteRelationshipsRequest(updates=updates))


def _touch_rel(resource_type, resource_id, relation, subject_type, subject_id) -> RelationshipUpdate:
    """Create a relationship update (TOUCH = create or update)."""
    return RelationshipUpdate(
        operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
        relationship=Relationship(
            resource=ObjectReference(object_type=resource_type, object_id=resource_id),
            relation=relation,
            subject=SubjectReference(
                object=ObjectReference(object_type=subject_type, object_id=subject_id)
            ),
        ),
    )
