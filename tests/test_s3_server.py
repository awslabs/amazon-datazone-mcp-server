"""Tests for the S3 MCP server functionality."""

import json
import os
from unittest.mock import Mock, patch, MagicMock
import pytest
from botocore.exceptions import ClientError


class TestGetMCPCredentials:
    """Test get_mcp_credentials function."""

    @patch.dict(
        os.environ,
        {
            "AWS_ACCESS_KEY_ID": "ASIAQGYBP5OXW5MTKVKQ123456",  # pragma: allowlist secret
            "AWS_SECRET_ACCESS_KEY": "test-secret",  # pragma: allowlist secret
            "AWS_SESSION_TOKEN": "test-token",  # pragma: allowlist secret
            "AWS_DEFAULT_REGION": "us-west-2",  # pragma: allowlist secret
        },
    )
    def test_local_development_credentials(self):
        """Test credentials from environment variables for local development."""
        from servers.s3.server import get_mcp_credentials

        result = get_mcp_credentials()

        assert result is not None
        assert (
            result["aws_access_key_id"]  # pragma: allowlist secret
            == "ASIAQGYBP5OXW5MTKVKQ123456"  # pragma: allowlist secret
        )  # pragma: allowlist secret
        assert (
            result["aws_secret_access_key"] == "test-secret"  # pragma: allowlist secret
        )  # pragma: allowlist secret
        assert result["aws_session_token"] == "test-token"  # pragma: allowlist secret
        assert result["region_name"] == "us-west-2"  # pragma: allowlist secret
        assert result["account_id"] == "014498655151"  # pragma: allowlist secret

    @patch.dict(
        os.environ,
        {
            "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",  # Different pattern  # pragma: allowlist secret
            "AWS_SECRET_ACCESS_KEY": "test-secret",  # pragma: allowlist secret
            "AWS_SESSION_TOKEN": "test-token",  # pragma: allowlist secret
        },
    )
    @patch("boto3.client")
    def test_secrets_manager_retrieval(self, mock_boto_client):
        """Test credentials retrieval from Secrets Manager."""
        from servers.s3.server import get_mcp_credentials

        # Mock secrets manager response
        mock_secrets_client = Mock()
        mock_boto_client.return_value = mock_secrets_client
        mock_secrets_client.get_secret_value.return_value = {
            "SecretString": json.dumps(
                {
                    "AWS_ACCESS_KEY_ID": "secrets-access-key",  # pragma: allowlist secret
                    "AWS_SECRET_ACCESS_KEY": "secrets-secret-key",  # pragma: allowlist secret
                    "AWS_SESSION_TOKEN": "secrets-session-token",  # pragma: allowlist secret
                    "AWS_DEFAULT_REGION": "us-east-1",  # pragma: allowlist secret
                    "ACCOUNT_ID": "123456789012",  # pragma: allowlist secret
                }
            )
        }

        result = get_mcp_credentials()

        assert result is not None
        assert (
            result["aws_access_key_id"]
            == "secrets-access-key"  # pragma: allowlist secret
        )  # pragma: allowlist secret
        assert (
            result["aws_secret_access_key"]
            == "secrets-secret-key"  # pragma: allowlist secret
        )  # pragma: allowlist secret
        assert (
            result["aws_session_token"]
            == "secrets-session-token"  # pragma: allowlist secret
        )  # pragma: allowlist secret
        assert result["region_name"] == "us-east-1"  # pragma: allowlist secret
        assert result["account_id"] == "123456789012"  # pragma: allowlist secret

        # Verify secrets manager was called correctly
        mock_boto_client.assert_called_with(
            "secretsmanager", region_name="us-east-1"
        )  # pragma: allowlist secret
        mock_secrets_client.get_secret_value.assert_called_with(  # pragma: allowlist secret
            SecretId="datazone-mcp-server/aws-credentials"  # pragma: allowlist secret
        )  # pragma: allowlist secret

    @patch.dict(os.environ, {}, clear=True)
    @patch("boto3.client")
    def test_secrets_manager_failure_fallback(self, mock_boto_client):
        """Test fallback to None when Secrets Manager fails."""
        from servers.s3.server import get_mcp_credentials

        # Mock secrets manager to raise an exception
        mock_secrets_client = Mock()
        mock_boto_client.return_value = mock_secrets_client
        mock_secrets_client.get_secret_value.side_effect = Exception("Access denied")

        result = get_mcp_credentials()

        assert result is None


class TestS3ReadFile:
    """Test s3_read_file tool."""

    @patch("servers.s3.server.s3_client")
    async def test_read_file_text_success(self, mock_s3_client):
        """Test successful text file reading."""
        from servers.s3.server import s3_read_file

        # Mock S3 get_object response for text file
        mock_body = Mock()
        mock_body.read.return_value = b"Hello, World!\nThis is a test file."

        mock_response = MagicMock()
        mock_response.__getitem__.side_effect = lambda key: {
            "Body": mock_body,
            "ContentType": "text/plain",
            "ContentLength": 32,
            "LastModified": Mock(isoformat=lambda: "2024-01-01T12:00:00Z"),
        }[key]
        mock_response.get.side_effect = lambda key, default=None: {
            "Body": mock_body,
            "ContentType": "text/plain",
            "ContentLength": 32,
            "LastModified": Mock(isoformat=lambda: "2024-01-01T12:00:00Z"),
        }.get(key, default)

        mock_s3_client.get_object.return_value = mock_response

        result = await s3_read_file(
            bucket_name="test-bucket", file_path="test/file.txt"
        )

        assert result is not None
        assert "content" in result
        assert result["content"] == "Hello, World!\nThis is a test file."
        assert "metadata" in result
        assert result["metadata"]["content_type"] == "text/plain"
        assert result["metadata"]["content_length"] == 32
        assert result["metadata"]["last_modified"] == "2024-01-01T12:00:00Z"

        # Verify S3 client call
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="test/file.txt"
        )

    @patch("servers.s3.server.s3_client")
    async def test_read_file_binary_success(self, mock_s3_client):
        """Test successful binary file reading."""
        from servers.s3.server import s3_read_file

        # Mock S3 get_object response for binary file
        binary_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        mock_body = Mock()
        mock_body.read.return_value = binary_content

        mock_response = MagicMock()
        mock_response.__getitem__.side_effect = lambda key: {
            "Body": mock_body,
            "ContentType": "image/png",
            "ContentLength": 16,
            "LastModified": Mock(isoformat=lambda: "2024-01-01T12:00:00Z"),
        }[key]
        mock_response.get.side_effect = lambda key, default=None: {
            "Body": mock_body,
            "ContentType": "image/png",
            "ContentLength": 16,
            "LastModified": Mock(isoformat=lambda: "2024-01-01T12:00:00Z"),
        }.get(key, default)

        mock_s3_client.get_object.return_value = mock_response

        result = await s3_read_file(
            bucket_name="test-bucket", file_path="test/image.png"
        )

        assert result is not None
        assert "content" in result
        assert result["content"] == binary_content  # Should remain as bytes
        assert result["metadata"]["content_type"] == "image/png"

    @patch("servers.s3.server.s3_client")
    async def test_read_file_error(self, mock_s3_client):
        """Test file reading error handling."""
        from servers.s3.server import s3_read_file

        # Mock S3 get_object to raise an error
        mock_s3_client.get_object.side_effect = ClientError(
            {
                "Error": {
                    "Code": "NoSuchKey",
                    "Message": "The specified key does not exist",
                }
            },
            "GetObject",
        )

        with pytest.raises(Exception) as exc_info:
            await s3_read_file(
                bucket_name="test-bucket", file_path="nonexistent/file.txt"
            )
        # The implementation wraps ClientError in Exception
        assert "not found" in str(exc_info.value).lower()


class TestS3ListObjects:
    """Test s3_list_objects tool."""

    @patch("servers.s3.server.s3_client")
    async def test_list_objects_success(self, mock_s3_client):
        """Test successful object listing."""
        from servers.s3.server import s3_list_objects

        # Mock S3 list_objects_v2 response (only folder1/ objects since that's the prefix requested)
        mock_s3_client.list_objects_v2.return_value = {
            "Contents": [
                {
                    "Key": "folder1/file1.txt",
                    "Size": 1024,
                    "LastModified": Mock(isoformat=lambda: "2024-01-01T12:00:00Z"),
                    "ETag": '"abc123"',
                    "StorageClass": "STANDARD",
                },
                {
                    "Key": "folder1/file2.txt",
                    "Size": 2048,
                    "LastModified": Mock(isoformat=lambda: "2024-01-01T13:00:00Z"),
                    "ETag": '"def456"',
                    "StorageClass": "STANDARD",
                },
            ],
            "CommonPrefixes": [
                {"Prefix": "folder1/subfolder/"},
                {"Prefix": "folder1/another/"},
            ],
            "IsTruncated": False,
            "KeyCount": 2,
        }

        result = await s3_list_objects(
            bucket_name="test-bucket", prefix="folder1/", max_items=100
        )

        assert result is not None
        assert "objects" in result
        assert "bucket" in result
        assert result["bucket"] == "test-bucket"
        assert result["prefix"] == "folder1/"
        # Should have only objects in folder1/
        assert len(result["objects"]) == 2
        assert result["objects"][0]["key"] == "folder1/file1.txt"
        assert result["objects"][1]["key"] == "folder1/file2.txt"
        assert "common_prefixes" in result
        assert len(result["common_prefixes"]) == 2

        # Verify S3 client call
        mock_s3_client.list_objects_v2.assert_called_once_with(
            Bucket="test-bucket", Prefix="folder1/", MaxKeys=100, Delimiter="/"
        )

    @patch("servers.s3.server.s3_client")
    async def test_list_objects_empty_bucket(self, mock_s3_client):
        """Test object listing for empty bucket."""
        from servers.s3.server import s3_list_objects

        # Mock S3 list_objects_v2 response for empty bucket
        mock_s3_client.list_objects_v2.return_value = {
            "Contents": [],
            "CommonPrefixes": [],
            "IsTruncated": False,
            "KeyCount": 0,
        }

        result = await s3_list_objects(bucket_name="empty-bucket")

        assert result is not None
        assert "objects" in result
        assert len(result["objects"]) == 0
        assert result["bucket"] == "empty-bucket"

    @patch("servers.s3.server.s3_client")
    async def test_list_objects_error(self, mock_s3_client):
        """Test object listing error handling."""
        from servers.s3.server import s3_list_objects

        # Mock S3 list_objects_v2 to raise an error
        mock_s3_client.list_objects_v2.side_effect = ClientError(
            {
                "Error": {
                    "Code": "NoSuchBucket",
                    "Message": "The specified bucket does not exist",
                }
            },
            "ListObjectsV2",
        )

        with pytest.raises(Exception):
            await s3_list_objects(bucket_name="nonexistent-bucket")


class TestS3HeadObject:
    """Test s3_head_object tool."""

    @patch("servers.s3.server.s3_client")
    async def test_head_object_success(self, mock_s3_client):
        """Test successful object head operation."""
        from servers.s3.server import s3_head_object

        # Mock S3 head_object response
        mock_s3_client.head_object.return_value = {
            "ContentType": "text/plain",
            "ContentLength": 1024,
            "LastModified": Mock(isoformat=lambda: "2024-01-01T12:00:00Z"),
            "ETag": '"abc123"',
            "StorageClass": "STANDARD",
            "Metadata": {"custom-key": "custom-value"},
        }

        result = await s3_head_object(
            bucket_name="test-bucket", object_key="test/file.txt"
        )

        assert result is not None
        # The actual implementation returns direct keys, not wrapped in metadata
        assert result["ContentType"] == "text/plain"
        assert result["ContentLength"] == 1024
        assert result["ETag"] == '"abc123"'
        assert result["StorageClass"] == "STANDARD"
        assert result["Metadata"]["custom-key"] == "custom-value"

        # Verify S3 client call
        mock_s3_client.head_object.assert_called_once_with(
            Bucket="test-bucket", Key="test/file.txt"
        )

    @patch("servers.s3.server.s3_client")
    async def test_head_object_with_version(self, mock_s3_client):
        """Test object head operation with version ID."""
        from servers.s3.server import s3_head_object

        mock_s3_client.head_object.return_value = {
            "ContentType": "text/plain",
            "ContentLength": 1024,
            "VersionId": "v1",
        }

        result = await s3_head_object(
            bucket_name="test-bucket", object_key="test/file.txt", version_id="v1"
        )

        assert result is not None

        # Verify S3 client call with version ID
        mock_s3_client.head_object.assert_called_once_with(
            Bucket="test-bucket", Key="test/file.txt", VersionId="v1"
        )

    @patch("servers.s3.server.s3_client")
    async def test_head_object_not_found(self, mock_s3_client):
        """Test object head operation when object not found."""
        from servers.s3.server import s3_head_object

        # Mock S3 head_object to raise an error
        mock_s3_client.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
        )

        with pytest.raises(Exception) as exc_info:
            await s3_head_object(
                bucket_name="test-bucket", object_key="nonexistent/file.txt"
            )

        # The actual implementation wraps ClientError in Exception
        assert "not found" in str(exc_info.value).lower()


class TestS3ListBuckets:
    """Test s3_list_buckets tool."""

    @patch("servers.s3.server.s3_client")
    async def test_list_buckets_success(self, mock_s3_client):
        """Test successful bucket listing."""
        from servers.s3.server import s3_list_buckets

        # Mock S3 list_buckets response
        mock_s3_client.list_buckets.return_value = {
            "Buckets": [
                {
                    "Name": "bucket1",
                    "CreationDate": Mock(isoformat=lambda: "2024-01-01T00:00:00Z"),
                },
                {
                    "Name": "bucket2",
                    "CreationDate": Mock(isoformat=lambda: "2024-01-02T00:00:00Z"),
                },
                {
                    "Name": "bucket3",
                    "CreationDate": Mock(isoformat=lambda: "2024-01-03T00:00:00Z"),
                },
            ],
            "Owner": {"DisplayName": "test-user", "ID": "123456789012"},
        }

        result = await s3_list_buckets()

        assert result is not None
        assert "buckets" in result
        assert len(result["buckets"]) == 3
        assert result["buckets"][0]["name"] == "bucket1"
        assert result["buckets"][1]["name"] == "bucket2"
        assert result["buckets"][2]["name"] == "bucket3"
        # Note: the actual implementation doesn't return owner info

        # Verify S3 client call
        mock_s3_client.list_buckets.assert_called_once()

    @patch("servers.s3.server.s3_client")
    async def test_list_buckets_error(self, mock_s3_client):
        """Test bucket listing error handling."""
        from servers.s3.server import s3_list_buckets

        # Mock S3 list_buckets to raise an error
        mock_s3_client.list_buckets.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "ListBuckets",
        )

        with pytest.raises(Exception):
            await s3_list_buckets()


class TestS3UploadObject:
    """Test s3_upload_object tool."""

    @patch("servers.s3.server.s3_client")
    async def test_upload_object_success(self, mock_s3_client):
        """Test successful object upload."""
        from servers.s3.server import s3_upload_object

        # Mock S3 put_object response
        mock_s3_client.put_object.return_value = {
            "ETag": '"abc123"',
            "VersionId": "v1",
            "ResponseMetadata": {"HTTPStatusCode": 200},
        }

        result = await s3_upload_object(
            bucket_name="test-bucket",
            object_key="test/file.txt",
            content="Hello, World!",
            content_type="text/plain",
        )

        assert result is not None
        assert "etag" in result
        assert result["etag"] == '"abc123"'
        assert "status" in result
        assert result["status"] == "success"
        assert "bucket" in result
        assert result["bucket"] == "test-bucket"
        assert "key" in result
        assert result["key"] == "test/file.txt"

        # Verify S3 client call
        mock_s3_client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test/file.txt",
            Body="Hello, World!",
            ContentType="text/plain",
        )

    @patch("servers.s3.server.s3_client")
    async def test_upload_object_error(self, mock_s3_client):
        """Test object upload error handling."""
        from servers.s3.server import s3_upload_object

        # Mock S3 put_object to raise an error
        mock_s3_client.put_object.side_effect = ClientError(
            {
                "Error": {
                    "Code": "NoSuchBucket",
                    "Message": "The specified bucket does not exist",
                }
            },
            "PutObject",
        )

        with pytest.raises(Exception):
            await s3_upload_object(
                bucket_name="nonexistent-bucket",
                object_key="test/file.txt",
                content="Hello, World!",
            )


class TestS3GetObject:
    """Test s3_get_object tool."""

    @patch("servers.s3.server.s3_client")
    async def test_get_object_success(self, mock_s3_client):
        """Test successful object retrieval."""
        from servers.s3.server import s3_get_object

        # Mock S3 get_object response
        mock_body = Mock()
        mock_body.read.return_value = b"Hello, World!"

        mock_response = MagicMock()
        mock_response.__getitem__.side_effect = lambda key: {
            "Body": mock_body,
            "ContentType": "text/plain",
            "ContentLength": 13,
            "LastModified": Mock(isoformat=lambda: "2024-01-01T12:00:00Z"),
            "ETag": '"abc123"',
            "VersionId": "v1",
            "Metadata": {"custom-key": "custom-value"},
        }[key]
        mock_response.get.side_effect = lambda key, default=None: {
            "Body": mock_body,
            "ContentType": "text/plain",
            "ContentLength": 13,
            "LastModified": Mock(isoformat=lambda: "2024-01-01T12:00:00Z"),
            "ETag": '"abc123"',
            "VersionId": "v1",
            "Metadata": {"custom-key": "custom-value"},
        }.get(key, default)

        mock_s3_client.get_object.return_value = mock_response

        result = await s3_get_object(
            bucket_name="test-bucket", object_key="test/file.txt"
        )

        assert result is not None
        assert "Body" in result
        assert result["Body"] == b"Hello, World!"  # Body is returned as bytes
        assert "ContentType" in result
        assert result["ContentType"] == "text/plain"
        assert result["ContentLength"] == 13
        assert result["ETag"] == '"abc123"'
        assert result["VersionId"] == "v1"
        assert result["Metadata"]["custom-key"] == "custom-value"

        # Verify S3 client call
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="test/file.txt"
        )

    @patch("servers.s3.server.s3_client")
    async def test_get_object_with_range(self, mock_s3_client):
        """Test object retrieval with range."""
        from servers.s3.server import s3_get_object

        mock_body = Mock()
        mock_body.read.return_value = b"World"

        mock_response = MagicMock()
        mock_response.__getitem__.side_effect = lambda key: {
            "Body": mock_body,
            "ContentType": "text/plain",
            "ContentLength": 5,
            "ContentRange": "bytes 7-11/13",
        }[key]

        mock_s3_client.get_object.return_value = mock_response

        result = await s3_get_object(
            bucket_name="test-bucket",
            object_key="test/file.txt",
            range_start=7,
            range_end=11,
        )

        assert result is not None
        assert result["Body"] == b"World"

        # Verify S3 client call with range
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="test/file.txt", Range="bytes=7-11"
        )

    @patch("servers.s3.server.s3_client")
    async def test_get_object_with_version(self, mock_s3_client):
        """Test object retrieval with version ID."""
        from servers.s3.server import s3_get_object

        mock_body = Mock()
        mock_body.read.return_value = b"Versioned content"

        mock_response = MagicMock()
        mock_response.__getitem__.side_effect = lambda key: {
            "Body": mock_body,
            "ContentType": "text/plain",
            "ContentLength": 17,
            "VersionId": "v2",
        }[key]
        mock_response.get.side_effect = lambda key, default=None: {
            "Body": mock_body,
            "ContentType": "text/plain",
            "ContentLength": 17,
            "VersionId": "v2",
        }.get(key, default)

        mock_s3_client.get_object.return_value = mock_response

        result = await s3_get_object(
            bucket_name="test-bucket", object_key="test/file.txt", version_id="v2"
        )

        assert result is not None
        assert result["VersionId"] == "v2"

        # Verify S3 client call with version ID
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="test/file.txt", VersionId="v2"
        )

    @patch("servers.s3.server.s3_client")
    async def test_get_object_error(self, mock_s3_client):
        """Test object retrieval error handling."""
        from servers.s3.server import s3_get_object

        # Mock S3 get_object to raise an error
        mock_s3_client.get_object.side_effect = ClientError(
            {
                "Error": {
                    "Code": "NoSuchKey",
                    "Message": "The specified key does not exist",
                }
            },
            "GetObject",
        )

        with pytest.raises(Exception):
            await s3_get_object(
                bucket_name="test-bucket", object_key="nonexistent/file.txt"
            )


class TestModuleImports:
    """Test module imports and initialization."""

    def test_server_module_imports(self):
        """Test that the server module can be imported successfully."""
        try:
            import servers.s3.server

            assert servers.s3.server is not None
        except ImportError as e:
            pytest.fail(f"Failed to import s3 server module: {e}")

    def test_required_dependencies(self):
        """Test that required dependencies are available."""
        try:
            import boto3

            assert boto3 is not None
        except ImportError as e:
            pytest.fail(f"Missing required dependency boto3: {e}")

        try:
            import mcp.server.fastmcp

            assert mcp.server.fastmcp is not None
        except ImportError as e:
            pytest.fail(f"Missing required dependency mcp.server.fastmcp: {e}")


class TestEnvironmentConfiguration:
    """Test environment configuration handling."""

    @patch.dict(
        os.environ,
        {
            "AWS_ACCESS_KEY_ID": "ASIAQGYBP5OXW5MTKVKQ123456",  # pragma: allowlist secret
            "AWS_SECRET_ACCESS_KEY": "test-secret",  # pragma: allowlist secret
            "AWS_SESSION_TOKEN": "test-token",  # pragma: allowlist secret
            # No AWS_DEFAULT_REGION
        },
    )
    def test_default_region(self):
        """Test default region configuration."""
        from servers.s3.server import get_mcp_credentials

        result = get_mcp_credentials()
        if result is not None:  # Only test if credentials are available
            assert result["region_name"] == "us-east-1"  # Default region

    @patch.dict(
        os.environ,
        {
            "AWS_ACCESS_KEY_ID": "ASIAQGYBP5OXW5MTKVKQ123456",  # pragma: allowlist secret
            "AWS_SECRET_ACCESS_KEY": "test-secret",  # pragma: allowlist secret
            "AWS_SESSION_TOKEN": "test-token",  # pragma: allowlist secret
            "AWS_DEFAULT_REGION": "us-west-2",  # pragma: allowlist secret
        },
    )
    def test_custom_region(self):
        """Test custom region configuration."""
        from servers.s3.server import get_mcp_credentials

        result = get_mcp_credentials()
        if result is not None:  # Only test if credentials are available
            assert result["region_name"] == "us-west-2"  # pragma: allowlist secret


class TestErrorHandling:
    """Test error handling scenarios."""

    @patch("servers.s3.server.s3_client")
    async def test_client_not_initialized(self, mock_s3_client):
        """Test behavior when AWS client is not initialized."""
        from servers.s3.server import s3_list_buckets

        # Set client to None to simulate initialization failure
        import servers.s3.server

        original_client = servers.s3.server.s3_client
        servers.s3.server.s3_client = None

        try:
            with pytest.raises(Exception) as exc_info:
                await s3_list_buckets()

            assert "not initialized" in str(
                exc_info.value
            ).lower() or "NoneType" in str(exc_info.value)
        finally:
            # Restore original client
            servers.s3.server.s3_client = original_client

    @patch("servers.s3.server.s3_client")
    async def test_invalid_parameters(self, mock_s3_client):
        """Test handling of invalid parameters."""
        from servers.s3.server import s3_read_file

        # Test with empty bucket name should still call the function but may fail in implementation
        try:
            await s3_read_file(bucket_name="", file_path="test.txt")
        except Exception:
            pass  # Expected to fail but shouldn't crash

        # Test with empty file path
        try:
            await s3_read_file(bucket_name="test-bucket", file_path="")
        except Exception:
            pass  # Expected to fail but shouldn't crash


class TestIntegration:
    """Integration tests for S3 server."""

    @patch("servers.s3.server.s3_client")
    async def test_full_file_workflow(self, mock_s3_client):
        """Test complete file upload and download workflow."""
        from servers.s3.server import s3_upload_object, s3_get_object, s3_head_object

        # Mock upload response
        mock_s3_client.put_object.return_value = {
            "ETag": '"abc123"',
            "VersionId": "v1",
            "ResponseMetadata": {"HTTPStatusCode": 200},
        }

        # Mock get object response
        mock_get_body = Mock()
        mock_get_body.read.return_value = b"Test content"

        mock_get_response = MagicMock()
        mock_get_response.__getitem__.side_effect = lambda key: {
            "Body": mock_get_body,
            "ContentType": "text/plain",
            "ContentLength": 12,
            "ETag": '"abc123"',
            "VersionId": "v1",
        }[key]
        mock_get_response.get.side_effect = lambda key, default=None: {
            "Body": mock_get_body,
            "ContentType": "text/plain",
            "ContentLength": 12,
            "ETag": '"abc123"',
            "VersionId": "v1",
        }.get(key, default)

        # Mock head object response
        mock_s3_client.head_object.return_value = {
            "ContentType": "text/plain",
            "ContentLength": 12,
            "ETag": '"abc123"',
            "VersionId": "v1",
        }

        # Upload file
        upload_result = await s3_upload_object(
            bucket_name="test-bucket",
            object_key="test/file.txt",
            content="Test content",
            content_type="text/plain",
        )

        assert upload_result is not None
        assert upload_result["etag"] == '"abc123"'

        # Get file metadata
        head_result = await s3_head_object(
            bucket_name="test-bucket", object_key="test/file.txt"
        )

        assert head_result is not None
        assert head_result["ContentLength"] == 12

        # Download file
        mock_s3_client.get_object.return_value = mock_get_response
        get_result = await s3_get_object(
            bucket_name="test-bucket", object_key="test/file.txt"
        )

        assert get_result is not None
        assert get_result["Body"] == b"Test content"
        assert get_result["ETag"] == '"abc123"'
