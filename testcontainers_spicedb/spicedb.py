"""SpiceDB testcontainer module."""

from typing import Optional, Callable
import time
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
from authzed.api.v1 import Client, WriteSchemaRequest

DEFAULT_SECRET_KEY = "somepresharedkey"
DEFAULT_IMAGE = "authzed/spicedb:v1.47.1"
DEFAULT_PORT = 50051


class SpiceDBContainer(DockerContainer):
    """SpiceDB testcontainer.

    Example:
        >>> with SpiceDBContainer() as spicedb:
        ...     endpoint = spicedb.get_endpoint()
        ...     secret_key = spicedb.get_secret_key()
    """

    def __init__(
        self,
        image: str = DEFAULT_IMAGE,
        secret_key: str = DEFAULT_SECRET_KEY,
        model: Optional[str] = None,
        model_secret_key: Optional[str] = None,
        schema_writer: Optional[Callable] = None,
        port: int = DEFAULT_PORT,
        **kwargs
    ):
        """Initialize SpiceDB container.

        Args:
            image: Docker image to use (default: authzed/spicedb:v1.47.1)
            secret_key: gRPC pre-shared key for authentication
            model: Optional schema/model to write on startup
            model_secret_key: Secret key for schema writer (defaults to secret_key)
            schema_writer: Optional custom schema writer function
            port: Port to expose (default: 50051)
            **kwargs: Additional arguments passed to DockerContainer
        """
        super().__init__(image, **kwargs)
        self._secret_key = secret_key
        self._model = model
        self._model_secret_key = model_secret_key or secret_key
        self._schema_writer = schema_writer
        self._port = port
        self._endpoint = None

        # Set up container configuration
        self.with_exposed_ports(port)
        self.with_command([
            "serve",
            "--grpc-preshared-key",
            secret_key
        ])

    def start(self) -> "SpiceDBContainer":
        """Start the container and wait for it to be ready."""
        super().start()

        # Wait for the exposed port
        self.get_exposed_port(self._port)

        # Wait for log message indicating server is ready
        wait_for_logs(self, "grpc server started serving", timeout=30)

        # Store endpoint
        host = self.get_container_host_ip()
        port = self.get_exposed_port(self._port)
        self._endpoint = f"{host}:{port}"

        # Write schema if model is provided
        if self._model:
            if self._schema_writer:
                self._schema_writer(self, self._model, self._model_secret_key)
            else:
                self._default_schema_writer()

        return self

    def get_endpoint(self) -> str:
        """Get the gRPC endpoint for the SpiceDB container.

        Returns:
            The endpoint string in format 'host:port'
        """
        if not self._endpoint:
            host = self.get_container_host_ip()
            port = self.get_exposed_port(self._port)
            self._endpoint = f"{host}:{port}"
        return self._endpoint

    def get_secret_key(self) -> str:
        """Get the gRPC pre-shared key.

        Returns:
            The secret key string
        """
        return self._secret_key

    def _default_schema_writer(self) -> None:
        """Write schema to SpiceDB using the default method."""
        from authzed.api.v1 import Client
        from grpcutil import insecure_bearer_token_credentials

        endpoint = self.get_endpoint()

        # Create insecure client for local testing
        client = Client(
            endpoint,
            insecure_bearer_token_credentials(self._model_secret_key)
        )

        # Write schema
        request = WriteSchemaRequest(schema=self._model)
        client.WriteSchema(request)


class SecretKeyCustomizer:
    """Customizer for setting a custom secret key.

    Example:
        >>> container = SpiceDBContainer(secret_key="mycustomsecret")
    """

    def __init__(self, secret_key: str):
        """Initialize the secret key customizer.

        Args:
            secret_key: The gRPC pre-shared key to use
        """
        self.secret_key = secret_key


class ModelCustomizer:
    """Customizer for setting a custom schema/model.

    Example:
        >>> model = '''
        ... definition user {}
        ... definition resource {
        ...     relation owner: user
        ... }
        ... '''
        >>> container = SpiceDBContainer(
        ...     model=model,
        ...     model_secret_key="somepresharedkey"
        ... )
    """

    def __init__(
        self,
        model: str,
        secret_key: str = DEFAULT_SECRET_KEY,
        schema_writer: Optional[Callable] = None
    ):
        """Initialize the model customizer.

        Args:
            model: The schema definition to write
            secret_key: The gRPC pre-shared key for authentication
            schema_writer: Optional custom schema writer function
        """
        self.model = model
        self.secret_key = secret_key
        self.schema_writer = schema_writer


def with_otel(otel_provider: str, endpoint: str) -> dict:
    """Add OpenTelemetry configuration to container.

    Args:
        otel_provider: The OTEL provider to use
        endpoint: The OTEL endpoint

    Returns:
        Dictionary with command arguments to add
    """
    return {
        "command_args": [
            "--otel-endpoint", endpoint,
            "--otel-provider", otel_provider
        ]
    }


def with_http(port: str) -> dict:
    """Enable HTTP endpoint on the specified port.

    Args:
        port: The port to expose for HTTP

    Returns:
        Dictionary with command arguments and exposed ports
    """
    return {
        "command_args": [
            "--http-enabled",
            "--http-addr", f":{port}"
        ],
        "exposed_ports": [f"{port}/tcp"]
    }
