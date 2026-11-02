"""Exercise the embedded launcher against its real pinned upstream package."""

import json
import os
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, Mock, patch

import mcp.types as types


ROOT = Path(__file__).resolve().parents[2]
SERVICE = json.loads((ROOT / "services/polymarket/manifest.json").read_text())["polymarket"]
LAUNCHER = {"__name__": "localish_mode_checks"}
exec(compile(SERVICE["command"][-1], "manifest.json:launcher", "exec"), LAUNCHER)
UPSTREAM = LAUNCHER["upstream"]


class ModeChecks(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, SERVICE['env'], clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        UPSTREAM.config = LAUNCHER['load_config']()
        UPSTREAM.polymarket_client = None

    def wallet(self, trading=False):
        os.environ['POLYGON_PRIVATE_KEY'] = '0x' + '0' * 63 + '1'
        os.environ['ENABLE_TRADING'] = str(trading).lower()
        UPSTREAM.config = LAUNCHER['load_config']()
        UPSTREAM.polymarket_client = Mock()
        UPSTREAM.polymarket_client.has_api_credentials.return_value = True

    async def test_public_tool_inventory_and_health_tool(self):
        tools = await LAUNCHER["list_tools"]()
        names = {tool.name for tool in tools}
        self.assertEqual(len(names), 23)
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

    async def test_wallet_free_mode_never_authenticates_even_with_trading_enabled(self):
        os.environ['ENABLE_TRADING'] = 'true'
        self.assertTrue(UPSTREAM.config.DEMO_MODE)
        self.assertFalse(UPSTREAM.config.has_api_credentials())
        client = Mock()
        with self.assertRaisesRegex(RuntimeError, 'No member wallet'):
            await UPSTREAM.PolymarketClient.create_api_credentials(client)
        client.get_client.assert_not_called()
        self.assertTrue((await LAUNCHER['call_tool']('cancel_all_orders', {})).isError)
        self.assertEqual(os.environ['CANCEL_ON_SHUTDOWN'], 'false')

    async def test_wallet_readonly_exposes_account_reads_but_blocks_every_mutation(self):
        self.wallet()
        names = {tool.name for tool in await LAUNCHER['list_tools']()}
        self.assertEqual(len(names), 37)
        self.assertIn('get_all_positions', names)
        self.assertIn('get_open_orders', names)
        self.assertIn('subscribe_user_orders', names)
        self.assertFalse(UPSTREAM.config.ENABLE_AUTONOMOUS_TRADING)
        dispatch = AsyncMock()
        with patch.dict(LAUNCHER, original_call_tool=dispatch):
            for tool in UPSTREAM.get_tool_definitions():
                if tool.name not in LAUNCHER['ORDER_READS']:
                    self.assertNotIn(tool.name, names)
                    self.assertTrue((await LAUNCHER['call_tool'](tool.name, {'confirm': True})).isError)
        dispatch.assert_not_awaited()

    async def test_trading_is_explicit_and_preserves_upstream_confirmation(self):
        self.wallet(trading=True)
        self.assertEqual(len(await LAUNCHER['list_tools']()), 45)
        self.assertFalse(UPSTREAM.config.ENABLE_AUTONOMOUS_TRADING)
        args = {'token_id': 'test', 'price': 0.5, 'size': 1, 'side': 'BUY', 'confirm': False}
        dispatch = AsyncMock(return_value=[types.TextContent(type='text', text='{"status":"confirmation_required"}')])
        with patch.dict(LAUNCHER, original_call_tool=dispatch):
            result = await LAUNCHER['call_tool']('create_limit_order', args)
        dispatch.assert_awaited_once_with('create_limit_order', args)
        self.assertIn('confirmation_required', result.content[0].text)

    async def test_health_checks_wallet_and_public_api_without_trades(self):
        self.wallet()
        dispatch = AsyncMock(return_value=[types.TextContent(type='text', text='[]')])
        with patch.dict(LAUNCHER, original_call_tool=dispatch):
            self.assertFalse((await LAUNCHER['call_tool']('check_connection', {})).isError)
        self.assertEqual([call.args[0] for call in dispatch.await_args_list], ['get_open_orders', 'get_trending_markets'])
        dispatch.return_value = [types.TextContent(type='text', text='{"error":"bad credentials"}')]
        with patch.dict(LAUNCHER, original_call_tool=dispatch):
            self.assertTrue((await LAUNCHER['call_tool']('check_connection', {})).isError)
        UPSTREAM.polymarket_client.has_api_credentials.return_value = False
        self.assertTrue((await LAUNCHER['call_tool']('check_connection', {})).isError)

    async def test_api_credentials_reused_and_available_to_account_websockets(self):
        self.wallet()
        client = Mock()
        creds = Mock(api_key='test-key', api_secret='test-secret', api_passphrase='test-passphrase')
        client.get_client.return_value.derive_api_key.return_value = creds
        result = await LAUNCHER['wallet_credentials'](client)
        self.assertIs(result, creds)
        client.get_client.return_value.create_api_key.assert_not_called()
        self.assertEqual(UPSTREAM.config.POLYMARKET_API_SECRET, 'test-secret')
        self.assertTrue(UPSTREAM.config.has_api_credentials())

    async def test_partial_or_invalid_credentials_fail_without_echoing_secrets(self):
        for env in [
            {'POLYMARKET_API_KEY': 'do-not-echo'},
            {'POLYGON_PRIVATE_KEY': 'do-not-echo'},
            {'POLYGON_PRIVATE_KEY': '0x' + '0'*63 + '1', 'POLYMARKET_API_SECRET': 'do-not-echo'},
            {'POLYGON_PRIVATE_KEY': '0x' + '0'*63 + '1', 'POLYGON_ADDRESS': 'do-not-echo'},
        ]:
            with self.subTest(env=list(env)), patch.dict(os.environ, env):
                with self.assertRaises(ValueError) as failure:
                    LAUNCHER['load_config']()
                self.assertNotIn('do-not-echo', str(failure.exception))

    async def test_optional_defaults_and_operator_settings(self):
        self.assertTrue(all(field['required'] is False for field in SERVICE['credentialFields']))
        settings = {item['key']: item['default'] for item in SERVICE['settings']}
        self.assertEqual(settings['ENABLE_TRADING'], 'false')
        self.assertEqual(settings['ENABLE_AUTONOMOUS_TRADING'], 'false')
        with patch.dict(os.environ, MAX_ORDER_SIZE_USD='42', ENABLE_AUTONOMOUS_TRADING='true'):
            config = LAUNCHER['load_config']()
            self.assertEqual(config.MAX_ORDER_SIZE_USD, 42)
            self.assertFalse(config.ENABLE_AUTONOMOUS_TRADING)
        for value in ['-1', 'nan', 'inf']:
            with patch.dict(os.environ, MAX_ORDER_SIZE_USD=value), self.assertRaises(ValueError):
                LAUNCHER['load_config']()


if __name__ == "__main__":
    unittest.main(verbosity=2)
