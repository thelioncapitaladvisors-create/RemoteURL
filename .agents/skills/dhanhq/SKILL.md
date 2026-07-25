---
name: dhanhq
description: Provides documentation and code resources for the Dhan HQ Trading API (Python SDK). Activate this skill when the user asks to build or integrate algorithmic trading scripts, webhooks, or API requests using DhanHQ.
---

# Dhan HQ API Skill

This skill contains the official DhanHQ Python SDK and documentation to assist with algorithmic trading integrations.

## Contents
The official DhanHQ-py SDK has been cloned into the `resources/` directory of this skill.
You can read through the `resources/README.md` or the Python source code inside `resources/` to understand how to authenticate, place orders, modify orders, cancel orders, and retrieve market data.

## Usage
When the user asks to build an algorithm or trading bot using Dhan HQ:
1. Refer to `/Users/vishant/Documents/Project/.agents/skills/dhanhq/resources/README.md` for standard usage examples.
2. The package is typically installed via `pip install dhanhq`.
3. The main client is instantiated via:
   ```python
   from dhanhq import dhanhq
   dhan = dhanhq(client_id="YOUR_CLIENT_ID", access_token="YOUR_ACCESS_TOKEN")
   ```
4. For placing orders, use `dhan.place_order(...)`.
5. For real-time data, refer to the WebSocket examples in the SDK.
