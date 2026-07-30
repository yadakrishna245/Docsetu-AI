"""
DocSetu AI - AWS Lambda Handler
================================
Main entry point for Lambda deployment using Mangum to wrap the FastAPI app.
Supports both API Gateway HTTP API (v2) and REST API (v1).

Usage:
    - Lambda: Set handler to `lambda_handler.handler`
    - Local: Run with `uvicorn main:app --reload`
"""

import os
import time
import logging

logger = logging.getLogger("docsetu.lambda")
logger.setLevel(logging.INFO)

# Cold start tracking
_cold_start = True
_init_time = time.time()

# Binary media types for PDF uploads and image responses
BINARY_MEDIA_TYPES = [
    "application/pdf",
    "application/octet-stream",
    "image/png",
    "image/jpeg",
    "image/gif",
    "multipart/form-data",
]


def is_lambda_environment() -> bool:
    """Detect if running inside AWS Lambda."""
    return "AWS_LAMBDA_FUNCTION_NAME" in os.environ


# Import the FastAPI app
if os.environ.get("USE_DYNAMODB", "true").lower() == "true":
    from main_lambda import app  # noqa: E402
else:
    from main import app  # noqa: E402
    from db import init_db  # noqa: E402
    init_db()

# Configure Mangum handler for API Gateway HTTP API v2
from mangum import Mangum  # noqa: E402

mangum_handler = Mangum(
    app,
    lifespan="off",
    api_gateway_base_path="/",
)


def handler(event, context):
    """
    AWS Lambda handler function.

    Wraps the FastAPI app via Mangum with cold start logging
    and binary media type support.

    Args:
        event: API Gateway event (v1 or v2 format)
        context: Lambda context object

    Returns:
        API Gateway response dict
    """
    global _cold_start

    if _cold_start:
        init_duration = time.time() - _init_time
        logger.info(
            "Cold start detected | Function: %s | Init duration: %.2fs | Memory: %sMB",
            os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "unknown"),
            init_duration,
            os.environ.get("AWS_LAMBDA_FUNCTION_MEMORY_SIZE", "unknown"),
        )
        _cold_start = False

    # Log request info for observability
    request_id = getattr(context, "aws_request_id", "local")
    http_method = event.get("httpMethod") or event.get("requestContext", {}).get(
        "http", {}
    ).get("method", "UNKNOWN")
    path = event.get("path") or event.get("rawPath", "/")

    logger.info(
        "Request: %s %s | RequestId: %s",
        http_method,
        path,
        request_id,
    )

    # Delegate to Mangum
    response = mangum_handler(event, context)

    logger.info(
        "Response: status=%s | RequestId: %s",
        response.get("statusCode", "unknown"),
        request_id,
    )

    return response


# Allow local execution for testing
if __name__ == "__main__":
    if not is_lambda_environment():
        import uvicorn

        print("Running locally with uvicorn...")
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    else:
        print("This module should be invoked by Lambda runtime, not directly.")
