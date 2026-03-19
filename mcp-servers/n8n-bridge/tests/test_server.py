from __future__ import annotations

import httpx
import pytest
import respx

from n8n_bridge.server import (
    BridgeSettings,
    IdempotencyCache,
    SecretRequest,
    TriggerWorkflowRequest,
    build_idempotency_key,
    get_1password_secret_impl,
    trigger_n8n_workflow_impl,
)


def test_build_idempotency_key_is_order_insensitive() -> None:
    first = build_idempotency_key("workflow-demo", {"alpha": 1, "beta": 2})
    second = build_idempotency_key("workflow-demo", {"beta": 2, "alpha": 1})
    assert first == second


@pytest.mark.asyncio
@respx.mock
async def test_trigger_n8n_workflow_deduplicates_identical_payloads() -> None:
    route = respx.post("http://n8n:5678/webhook/run-demo").mock(
        return_value=httpx.Response(200, json={"accepted": True})
    )
    settings = BridgeSettings(n8n_base_url="http://n8n:5678")
    request = TriggerWorkflowRequest(webhook_id="run-demo", payload={"job": "sync", "run": 1})
    cache = IdempotencyCache(ttl_seconds=300)

    async with httpx.AsyncClient() as client:
        first = await trigger_n8n_workflow_impl(request, settings, client=client, cache=cache)
        second = await trigger_n8n_workflow_impl(request, settings, client=client, cache=cache)

    assert route.call_count == 1
    assert first["deduplicated"] is False
    assert second["deduplicated"] is True
    assert second["idempotency_key"] == first["idempotency_key"]


@pytest.mark.asyncio
@respx.mock
async def test_trigger_n8n_workflow_raises_on_http_failure() -> None:
    respx.post("http://n8n:5678/webhook/broken").mock(return_value=httpx.Response(502))
    settings = BridgeSettings(n8n_base_url="http://n8n:5678")
    request = TriggerWorkflowRequest(webhook_id="broken", payload={"job": "sync"})
    cache = IdempotencyCache(ttl_seconds=300)

    async with httpx.AsyncClient() as client:
        with pytest.raises(RuntimeError, match="n8n webhook request failed"):
            await trigger_n8n_workflow_impl(request, settings, client=client, cache=cache)


@pytest.mark.asyncio
@respx.mock
async def test_get_1password_secret_returns_selected_field_value() -> None:
    respx.get("http://1password-connect-api:8080/v1/vaults/vault-dev/items/item-001").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "item-001",
                "title": "Demo Secret",
                "fields": [
                    {"id": "username", "label": "username", "value": "agent"},
                    {"id": "api-key", "label": "api-key", "value": "super-secret"},
                ],
            },
        )
    )
    settings = BridgeSettings(
        op_connect_url="http://1password-connect-api:8080",
        op_connect_token="development-token",
    )
    request = SecretRequest(vault_id="vault-dev", item_id="item-001", field_label="api-key")

    async with httpx.AsyncClient() as client:
        result = await get_1password_secret_impl(request, settings, client=client)

    assert result["field_label"] == "api-key"
    assert result["value"] == "super-secret"


@pytest.mark.asyncio
@respx.mock
async def test_get_1password_secret_returns_inventory_when_field_not_requested() -> None:
    respx.get("http://1password-connect-api:8080/v1/vaults/vault-dev/items/item-001").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "item-001",
                "title": "Demo Secret",
                "fields": [
                    {"id": "username", "label": "username", "value": "agent"},
                    {"id": "api-key", "label": "api-key", "value": "super-secret"},
                ],
            },
        )
    )
    settings = BridgeSettings(
        op_connect_url="http://1password-connect-api:8080",
        op_connect_token="development-token",
    )
    request = SecretRequest(vault_id="vault-dev", item_id="item-001")

    async with httpx.AsyncClient() as client:
        result = await get_1password_secret_impl(request, settings, client=client)

    assert result["title"] == "Demo Secret"
    assert result["available_fields"] == ["username", "api-key"]


@pytest.mark.asyncio
async def test_get_1password_secret_requires_connect_token() -> None:
    settings = BridgeSettings(op_connect_token=None)
    request = SecretRequest(vault_id="vault-dev", item_id="item-001", field_label="api-key")

    async with httpx.AsyncClient() as client:
        with pytest.raises(RuntimeError, match="OP_CONNECT_TOKEN is not configured"):
            await get_1password_secret_impl(request, settings, client=client)
