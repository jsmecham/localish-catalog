"""Exercise the embedded launcher against its real pinned upstream package."""

import json
import os
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch

import mcp.types as types


ROOT = Path(__file__).resolve().parents[2]
SERVICE = json.loads((ROOT / "services/polymarket/manifest.json").read_text())["polymarket"]
LAUNCHER = {"__name__": "localish_readonly_checks"}
exec(compile(SERVICE["command"][-1], "manifest.json:launcher", "exec"), LAUNCHER)
UPSTREAM = LAUNCHER["upstream"]


class ReadonlyChecks(unittest.IsolatedAsyncioTestCase):
    async def test_public_tool_inventory_and_health_tool(self):
        tools = await LAUNCHER["list_tools"]()
        names = {tool.name for tool in tools}
        self.assertEqual(len(names), 22)
        self.assertIn(SERVICE["healthTool"]["name"], names)
        self.assertIn("search_markets", names)
        self.assertIn("get_orderbook", names)
        self.assertIn("subscribe_market_prices", names)

    async def test_private_tools_are_rejected_before_dispatch(self):
        private = [tool.name for tool in UPSTREAM.get_tool_definitions()]
        private += [tool.name for tool in UPSTREAM.portfolio_integration.get_portfolio_tool_definitions()]
        private += ["subscribe_user_orders", "subscribe_user_trades", "get_market_holders", "unknown_tool"]
        dispatch = AsyncMock(side_effect=AssertionError("Private tool reached upstream"))
        with patch.dict(LAUNCHER, original_call_tool=dispatch):
            for name in private:
                with self.subTest(tool=name):
                    result = await LAUNCHER["call_tool"](name, {"confirm": True})
                    self.assertTrue(result.isError)
            dispatch.assert_not_awaited()

    async def test_error_payloads_set_mcp_error_flag(self):
        for payload in ['{"error": "upstream unavailable"}', '{"success": false}',
                        'Error: WebSocket unavailable']:
            with self.subTest(payload=payload):
                content = [types.TextContent(type="text", text=payload)]
                with patch.dict(LAUNCHER, original_call_tool=AsyncMock(return_value=content)):
                    result = await LAUNCHER["call_tool"]("get_trending_markets", {"limit": 1})
                self.assertTrue(result.isError)
                self.assertEqual(result.content, content)

    async def test_success_and_empty_market_lists_remain_successful(self):
        for payload in ['[]', '[{"id": "market", "question": "Example?"}]',
                        '{"success": true}']:
            with self.subTest(payload=payload):
                content = [types.TextContent(type="text", text=payload)]
                dispatch = AsyncMock(return_value=content)
                arguments = {"timeframe": "24h", "limit": 1}
                with patch.dict(LAUNCHER, original_call_tool=dispatch):
                    result = await LAUNCHER["call_tool"]("get_trending_markets", arguments)
                dispatch.assert_awaited_once_with("get_trending_markets", arguments)
                self.assertFalse(result.isError)
                self.assertEqual(result.content, content)

    async def test_inherited_credentials_cannot_enable_authentication(self):
        credential_names = ["POLYMARKET_API_KEY", "POLYMARKET_API_SECRET",
                            "POLYMARKET_PASSPHRASE", "POLYMARKET_API_KEY_NAME"]
        environment = {name: "test-only-not-a-credential" for name in credential_names}
        environment.update(ENABLE_AUTONOMOUS_TRADING="true")
        with patch.dict(os.environ, environment):
            config = UPSTREAM.load_config()
        self.assertTrue(config.DEMO_MODE)
        self.assertFalse(config.ENABLE_AUTONOMOUS_TRADING)
        self.assertFalse(config.has_api_credentials())
        for name in credential_names:
            self.assertIsNone(getattr(config, name))
        with self.assertRaisesRegex(RuntimeError, "authentication is disabled"):
            await UPSTREAM.PolymarketClient.create_api_credentials(object())
        self.assertEqual(os.environ["CANCEL_ON_SHUTDOWN"], "false")


if __name__ == "__main__":
    unittest.main(verbosity=2)
