"""Tests for SpiceDB testcontainer module."""

from grpcutil import insecure_bearer_token_credentials
from authzed.api.v1 import (
    Client,
    WriteSchemaRequest,
    WriteRelationshipsRequest,
    RelationshipUpdate,
    Relationship,
    ObjectReference,
    SubjectReference,
)
from testcontainers_spicedb import SpiceDBContainer
from testcontainers_spicedb.testdata import MODEL


def test_spicedb_container():
    """Test basic SpiceDB container functionality."""
    with SpiceDBContainer(image="authzed/spicedb:v1.47.1") as container:
        endpoint = container.get_endpoint()
        secret_key = container.get_secret_key()

        # Create SpiceDB client
        client = Client(
            endpoint,
            insecure_bearer_token_credentials(secret_key)
        )

        # Write schema
        response = client.WriteSchema(WriteSchemaRequest(schema=MODEL))

        # Verify response
        assert response.written_at is not None


def test_spicedb_secret_customizer():
    """Test SpiceDB container with custom secret key."""
    custom_secret = "testsecret"

    with SpiceDBContainer(
        image="authzed/spicedb:v1.47.1",
        secret_key=custom_secret
    ) as container:
        secret_key = container.get_secret_key()

        # Verify custom secret key
        assert secret_key == custom_secret

        endpoint = container.get_endpoint()

        # Create SpiceDB client with custom secret
        client = Client(
            endpoint,
            insecure_bearer_token_credentials(custom_secret)
        )

        # Write schema
        response = client.WriteSchema(WriteSchemaRequest(schema=MODEL))

        # Verify response
        assert response.written_at is not None


def test_spicedb_model_customizer():
    """Test SpiceDB container with model customizer."""
    default_secret_key = "somepresharedkey"

    with SpiceDBContainer(
        image="authzed/spicedb:v1.47.1",
        model=MODEL,
        model_secret_key=default_secret_key
    ) as container:
        endpoint = container.get_endpoint()

        # Create SpiceDB client
        client = Client(
            endpoint,
            insecure_bearer_token_credentials(default_secret_key)
        )

        # Write relationships (schema should already be loaded)
        response = client.WriteRelationships(
            WriteRelationshipsRequest(
                updates=[
                    RelationshipUpdate(
                        operation=RelationshipUpdate.OPERATION_CREATE,
                        relationship=Relationship(
                            resource=ObjectReference(
                                object_id="testplatform",
                                object_type="platform"
                            ),
                            relation="administrator",
                            subject=SubjectReference(
                                object=ObjectReference(
                                    object_id="testuser",
                                    object_type="user"
                                )
                            )
                        )
                    )
                ]
            )
        )

        # Verify response
        assert response.written_at is not None
