"""Blocking DynamoDB adapter: call via asyncio.to_thread in HTTP handlers."""
from __future__ import annotations

from decimal import Decimal
import json
import os
from pathlib import Path
from time import time

import boto3
import botocore.session
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from .errors import Conflict, IntegrityFailure, InvalidRecord, StorageUnavailable
from .settings import PersistenceSettings

SERIALIZER, DESERIALIZER = TypeSerializer(), TypeDeserializer()
MODEL_VERSION = 1


def encode(value):
    try:
        result = {key: SERIALIZER.serialize(item) for key, item in value.items()}
        if len(json.dumps(result, ensure_ascii=False).encode()) > 390000:
            raise InvalidRecord("Item exceeds the internal metadata budget; store large bodies as objects")
        return result
    except (ValueError, TypeError):
        raise InvalidRecord("Invalid DynamoDB attribute value") from None


def decode(value):
    def numbers(item):
        if isinstance(item, Decimal):
            return int(item) if item == int(item) else str(item)
        if isinstance(item, dict):
            return {key: numbers(child) for key, child in item.items()}
        if isinstance(item, list):
            return [numbers(child) for child in item]
        return item
    return numbers({key: DESERIALIZER.deserialize(item) for key, item in value.items()})


class DynamoStore:
    def __init__(self, settings: PersistenceSettings, *, clock=time):
        # Revalidate even when a caller constructs the dataclass directly.
        self.settings = PersistenceSettings.from_environment({"DYNAMODB_ENDPOINT": settings.endpoint, "DYNAMODB_TABLE": settings.table_name, "APP_DATA_DIR": str(settings.data_dir)})
        self.clock = clock
        local_session = botocore.session.Session(session_vars={
            "profile": (None, None, None, None), "config_file": (None, None, os.devnull, None),
            "credentials_file": (None, None, os.devnull, None),
        })
        session = boto3.session.Session(botocore_session=local_session, aws_access_key_id="localdevelopment", aws_secret_access_key="localdevelopment", region_name="local")
        self.client = session.client("dynamodb", endpoint_url=self.settings.endpoint,
                                     config=Config(connect_timeout=2, read_timeout=5, retries={"max_attempts": 1}, proxies={}))
        self.table = self.settings.table_name

    def close(self):
        self.client.close()

    def call(self, method, **kwargs):
        try:
            return getattr(self.client, method)(**kwargs)
        except ClientError as exc:
            code = exc.response["Error"]["Code"]
            if code == "ConditionalCheckFailedException" or (code == "TransactionCanceledException" and any(item.get("Code") == "ConditionalCheckFailed" for item in exc.response.get("CancellationReasons", []))):
                raise Conflict("Conditional write conflict") from None
            if code == "ValidationException":
                raise InvalidRecord("DynamoDB rejected the item or transaction") from None
            raise StorageUnavailable("Local database operation failed") from None
        except BotoCoreError:
            raise StorageUnavailable("Local database is unavailable") from None

    def ensure_table(self):
        # Explicit administrative action only. App startup never creates a table.
        definition = json.loads((Path(__file__).resolve().parents[3] / "schema/dynamodb-v1.json").read_text())["table_definition"]
        try:
            current = self.client.describe_table(TableName=self.table)["Table"]
        except self.client.exceptions.ResourceNotFoundException:
            self.call("create_table", TableName=self.table, **definition)
            current = self.call("describe_table", TableName=self.table)["Table"]
        except BotoCoreError:
            raise StorageUnavailable("Start DynamoDB Local before initializing storage") from None
        expected = {("pk", "HASH"), ("sk", "RANGE")}
        matching_indexes = [item for item in current.get("GlobalSecondaryIndexes", []) if item["IndexName"] == "gsi1"]
        expected_gsi = {(item["AttributeName"], item["KeyType"]) for item in definition["GlobalSecondaryIndexes"][0]["KeySchema"]}
        if {(item["AttributeName"], item["KeyType"]) for item in current["KeySchema"]} != expected or not matching_indexes or {(item["AttributeName"], item["KeyType"]) for item in matching_indexes[0]["KeySchema"]} != expected_gsi:
            raise IntegrityFailure("Existing table does not match storage model v1")
        key = {"pk": "SYSTEM#MODEL", "sk": "META"}
        item = self.get(key, include_expired=True)
        if item and item.get("model_version") != MODEL_VERSION:
            raise IntegrityFailure("Storage model version mismatch; do not overwrite the table")
        if not item:
            try:
                self.transact([self.put_action({**key, "model_version": MODEL_VERSION, "revision": 1})])
            except Conflict:
                if self.get(key).get("model_version") != MODEL_VERSION:
                    raise IntegrityFailure("Storage model was initialized concurrently with another version") from None

    def health(self):
        try:
            self.call("describe_table", TableName=self.table)
            item = self.get({"pk": "SYSTEM#MODEL", "sk": "META"})
            return bool(item and item.get("model_version") == MODEL_VERSION)
        except StorageUnavailable:
            return False

    def get(self, key, *, include_expired=False):
        result = self.call("get_item", TableName=self.table, Key=encode(key), ConsistentRead=True)
        item = decode(result["Item"]) if "Item" in result else None
        if item and not include_expired and item.get("expires_at_s", float("inf")) <= self.clock():
            return None
        return item

    def put_action(self, item, expected_revision=0):
        output = {"TableName": self.table, "Item": encode(item), "ConditionExpression": "attribute_not_exists(pk)"}
        if expected_revision:
            output.update(ConditionExpression="#rev = :revision", ExpressionAttributeNames={"#rev": "revision"}, ExpressionAttributeValues={":revision": {"N": str(expected_revision)}})
        return {"Put": output}

    def delete_action(self, key, expected_revision):
        return {"Delete": {"TableName": self.table, "Key": encode(key), "ConditionExpression": "#rev = :revision", "ExpressionAttributeNames": {"#rev": "revision"}, "ExpressionAttributeValues": {":revision": {"N": str(expected_revision)}}}}

    def check_action(self, item):
        return {"ConditionCheck": {"TableName": self.table, "Key": encode({"pk": item["pk"], "sk": item["sk"]}), "ConditionExpression": "#rev = :revision", "ExpressionAttributeNames": {"#rev": "revision"}, "ExpressionAttributeValues": {":revision": {"N": str(item["revision"])}}}}

    def transact(self, actions):
        if not 1 <= len(actions) <= 100:
            raise InvalidRecord("Transaction must contain 1..100 actions")
        self.call("transact_write_items", TransactItems=actions)

    def query(self, pk, prefix, *, limit=20, start=None, reverse=False, filters=None, upper_bound=None):
        if not 1 <= limit <= 100:
            raise InvalidRecord("Invalid page limit")
        names, values = {"#pk": "pk", "#sk": "sk"}, {":pk": {"S": pk}, ":prefix": {"S": prefix}}
        expression = "#pk = :pk AND begins_with(#sk, :prefix)"
        if upper_bound is not None:
            expression = "#pk = :pk AND #sk BETWEEN :prefix AND :upper"
            values[":upper"] = {"S": upper_bound}
        args = {"TableName": self.table, "KeyConditionExpression": expression, "ExpressionAttributeNames": names, "ExpressionAttributeValues": values, "Limit": limit, "ScanIndexForward": not reverse, "ConsistentRead": True}
        conditions = []
        for index, (name, value) in enumerate(sorted((filters or {}).items())):
            names[f"#f{index}"] = name
            values[f":f{index}"] = SERIALIZER.serialize(value)
            conditions.append(f"#f{index} = :f{index}")
        if conditions:
            args["FilterExpression"] = " AND ".join(conditions)
        if start:
            args["ExclusiveStartKey"] = encode(start)
        result = self.call("query", **args)
        items = [decode(item) for item in result["Items"]]
        return [item for item in items if item.get("expires_at_s", float("inf")) > self.clock()], decode(result["LastEvaluatedKey"]) if result.get("LastEvaluatedKey") else None

    def export_items(self):
        # Maintenance only: quiesce writes for a stable multi-page backup.
        start = None
        while True:
            args = {"TableName": self.table, "ConsistentRead": True}
            if start:
                args["ExclusiveStartKey"] = start
            result = self.call("scan", **args)
            yield from (decode(item) for item in result["Items"])
            start = result.get("LastEvaluatedKey")
            if not start:
                break

    def query_index(self, partition, *, limit=20, start=None):
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise InvalidRecord("Invalid page limit")
        args = {"TableName": self.table, "IndexName": "gsi1", "KeyConditionExpression": "gsi_pk = :partition",
                "ExpressionAttributeValues": {":partition": {"S": partition}}, "Limit": limit, "ConsistentRead": False}
        if start:
            args["ExclusiveStartKey"] = encode(start)
        result = self.call("query", **args)
        return [decode(row) for row in result["Items"]], decode(result["LastEvaluatedKey"]) if result.get("LastEvaluatedKey") else None
