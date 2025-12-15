"""Example usage of SpiceDB testcontainer."""

from testcontainers_spicedb import SpiceDBContainer


def example_run_container():
    """Example: Run a SpiceDB container.

    This example demonstrates how to start a SpiceDB container,
    verify it's running, and properly clean it up.
    """
    # Start SpiceDB container
    container = SpiceDBContainer(image="authzed/spicedb:v1.47.1")
    container.start()

    try:
        # Get container state
        state = container.get_wrapped_container().status
        print(f"Container running: {state == 'running'}")

        # Get endpoint and secret for client usage
        endpoint = container.get_endpoint()
        secret_key = container.get_secret_key()

        print(f"SpiceDB endpoint: {endpoint}")
        print(f"Secret key: {secret_key}")

    finally:
        # Clean up the container
        container.stop()


def example_with_context_manager():
    """Example: Use SpiceDB container with context manager.

    This example shows the recommended way to use the container
    with Python's context manager for automatic cleanup.
    """
    with SpiceDBContainer(image="authzed/spicedb:v1.47.1") as spicedb:
        # Container is automatically started
        endpoint = spicedb.get_endpoint()
        secret_key = spicedb.get_secret_key()

        print(f"SpiceDB endpoint: {endpoint}")
        print(f"Secret key: {secret_key}")

        # Your test code here...

    # Container is automatically stopped and removed


def example_custom_secret():
    """Example: Use custom secret key.

    This example demonstrates how to configure a custom
    gRPC pre-shared key for authentication.
    """
    with SpiceDBContainer(
        image="authzed/spicedb:v1.47.1",
        secret_key="mycustomsecret"
    ) as spicedb:
        endpoint = spicedb.get_endpoint()
        secret_key = spicedb.get_secret_key()

        print(f"Using custom secret: {secret_key}")
        # Use this secret when creating your SpiceDB client


def example_with_model():
    """Example: Start container with pre-loaded schema.

    This example shows how to automatically load a schema
    when the container starts, useful for integration tests.
    """
    schema = """
        definition user {}

        definition document {
            relation owner: user
            relation viewer: user
            permission view = viewer + owner
        }
    """

    with SpiceDBContainer(
        image="authzed/spicedb:v1.47.1",
        model=schema,
        model_secret_key="somepresharedkey"
    ) as spicedb:
        endpoint = spicedb.get_endpoint()
        print(f"SpiceDB started with pre-loaded schema at {endpoint}")

        # Schema is already loaded, ready to write relationships


if __name__ == "__main__":
    print("Example 1: Basic container")
    example_run_container()

    print("\nExample 2: Context manager")
    example_with_context_manager()

    print("\nExample 3: Custom secret")
    example_custom_secret()

    print("\nExample 4: Pre-loaded model")
    example_with_model()
