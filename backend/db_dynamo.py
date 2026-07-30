"""
DocSetu AI - DynamoDB Database Adapter
Replaces SQLAlchemy for serverless Lambda deployment.
Uses boto3 to interact with DynamoDB tables directly.
"""

import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

import boto3
from boto3.dynamodb.conditions import Key
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize DynamoDB resource
dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)

# Table references
users_table = dynamodb.Table(settings.dynamodb_users_table)
documents_table = dynamodb.Table(settings.dynamodb_documents_table)


class DynamoUser:
    """User operations on DynamoDB."""

    @staticmethod
    def create(email: str, username: str, hashed_password: str, full_name: str = "",
               organization: str = "", role: str = "viewer") -> Dict[str, Any]:
        user_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        item = {
            "id": user_id,
            "email": email,
            "username": username,
            "hashed_password": hashed_password,
            "full_name": full_name or "",
            "organization": organization or "",
            "role": role,
            "is_active": True,
            "is_verified": False,
            "mfa_enabled": False,
            "mfa_secret": None,
            "verification_token": None,
            "reset_token": None,
            "reset_token_expires": None,
            "created_at": now,
            "updated_at": now,
        }
        users_table.put_item(Item={k: v for k, v in item.items() if v is not None})
        return item

    @staticmethod
    def get_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        response = users_table.get_item(Key={"id": user_id})
        return response.get("Item")

    @staticmethod
    def get_by_email(email: str) -> Optional[Dict[str, Any]]:
        response = users_table.query(
            IndexName="email-index",
            KeyConditionExpression=Key("email").eq(email),
        )
        items = response.get("Items", [])
        return items[0] if items else None

    @staticmethod
    def get_by_username(username: str) -> Optional[Dict[str, Any]]:
        # Scan since no GSI on username (rare operation)
        response = users_table.scan(
            FilterExpression="username = :u",
            ExpressionAttributeValues={":u": username},
        )
        items = response.get("Items", [])
        return items[0] if items else None

    @staticmethod
    def update(user_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        kwargs["updated_at"] = datetime.utcnow().isoformat()
        update_expr = "SET " + ", ".join(f"#{k} = :{k}" for k in kwargs)
        expr_names = {f"#{k}": k for k in kwargs}
        expr_values = {f":{k}": v for k, v in kwargs.items()}
        users_table.update_item(
            Key={"id": user_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
        )
        return DynamoUser.get_by_id(user_id)

    @staticmethod
    def count_all() -> int:
        response = users_table.scan(Select="COUNT")
        return response.get("Count", 0)

    @staticmethod
    def list_all(limit: int = 100) -> List[Dict[str, Any]]:
        response = users_table.scan(Limit=limit)
        return response.get("Items", [])


class DynamoDocument:
    """Document operations on DynamoDB."""

    @staticmethod
    def create(filename: str, original_filename: str, file_path: str,
               file_type: str, file_size: int, mime_type: str,
               owner_id: str, batch_id: str = None) -> Dict[str, Any]:
        doc_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        item = {
            "id": doc_id,
            "filename": filename,
            "original_filename": original_filename,
            "file_path": file_path,
            "file_type": file_type,
            "file_size": file_size,
            "mime_type": mime_type,
            "owner_id": owner_id,
            "batch_id": batch_id,
            "status": "uploaded",
            "extracted_text": None,
            "language_detected": None,
            "page_count": None,
            "metadata_json": None,
            "error_message": None,
            "created_at": now,
            "updated_at": now,
            "processed_at": None,
        }
        documents_table.put_item(Item={k: v for k, v in item.items() if v is not None})
        return item

    @staticmethod
    def get_by_id(doc_id: str) -> Optional[Dict[str, Any]]:
        response = documents_table.get_item(Key={"id": doc_id})
        return response.get("Item")

    @staticmethod
    def get_by_owner(owner_id: str, limit: int = 20, status_filter: str = None) -> List[Dict[str, Any]]:
        kwargs = {
            "IndexName": "owner-index",
            "KeyConditionExpression": Key("owner_id").eq(owner_id),
            "Limit": limit,
        }
        if status_filter:
            kwargs["FilterExpression"] = "status = :s"
            kwargs["ExpressionAttributeValues"] = {":s": status_filter}
        response = documents_table.query(**kwargs)
        return response.get("Items", [])

    @staticmethod
    def update(doc_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        kwargs["updated_at"] = datetime.utcnow().isoformat()
        # Filter out None values
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        if not kwargs:
            return DynamoDocument.get_by_id(doc_id)
        update_expr = "SET " + ", ".join(f"#{k} = :{k}" for k in kwargs)
        expr_names = {f"#{k}": k for k in kwargs}
        expr_values = {f":{k}": v for k, v in kwargs.items()}
        documents_table.update_item(
            Key={"id": doc_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
        )
        return DynamoDocument.get_by_id(doc_id)

    @staticmethod
    def delete(doc_id: str):
        documents_table.delete_item(Key={"id": doc_id})

    @staticmethod
    def count_by_owner(owner_id: str) -> int:
        response = documents_table.query(
            IndexName="owner-index",
            KeyConditionExpression=Key("owner_id").eq(owner_id),
            Select="COUNT",
        )
        return response.get("Count", 0)

    @staticmethod
    def count_all() -> int:
        response = documents_table.scan(Select="COUNT")
        return response.get("Count", 0)
