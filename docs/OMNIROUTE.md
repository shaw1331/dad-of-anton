# OmniRoute

## What is it?

OmniRoute is a free, open-source AI gateway that provides a single local endpoint for 350+ AI providers (90+ free). It acts as a proxy — your app talks to `localhost:20128`, and OmniRoute routes requests to the best available provider with automatic fallback.

## Why use it?

- **One endpoint** for all LLM providers (OpenAI, Anthropic, Google, etc.)
- **90+ free tiers** — ~1.51B free tokens/month
- **Auto-fallback** — if one provider is down or rate-limited, it switches automatically
- **Token compression** — saves 15-95% on token usage (RTK + Caveman)
- **Works out of the box** — no API keys required for basic usage
- **Compatible with** — Claude Code, Codex, Cursor, OpenCode, Cline, Copilot

## Installation

```bash
npm i -g omniroute
```

## Quick Start

```bash
# Start the server
omniroute serve --no-open

# Check health
curl http://localhost:20128/api/monitoring/health

# Test with auto model
curl http://localhost:20128/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"auto","messages":[{"role":"user","content":"Hello!"}]}'
```

## Server Options

```bash
omniroute serve                    # Default: port 20128, opens browser
omniroute serve --no-open          # Don't open browser
omniroute serve --port 3000        # Custom port
omniroute serve --daemon           # Run in background
omniroute serve --log              # Show live logs
omniroute serve --no-recovery      # Disable auto-restart on crash
```

## 4-Tier Auto-Fallback

OmniRoute cascades through provider tiers when one fails:

| Tier | Type | Example |
|------|------|---------|
| 1 | Subscription | Your paid OpenAI/Anthropic credits |
| 2 | API Key | Your own API keys |
| 3 | Cheap | Low-cost providers |
| 4 | Free | Free-tier providers |

## Token Compression

RTK + Caveman compression saves 15-95% tokens automatically. Enable in dashboard or set:
```
COMPRESSION_ENABLED=true
```

## Supported Models

Call `auto` to let OmniRoute pick the best available, or specify:
- `gpt-4o`, `gpt-4o-mini` (OpenAI)
- `claude-3-opus`, `claude-3-sonnet` (Anthropic)
- `gemini-pro`, `gemini-flash` (Google)
- `deepseek-chat`, `deepseek-coder` (DeepSeek)
- `llama-3-70b` (Meta)
- 1300+ more models

## Integration with Dad-of-Anton

OmniRoute provides an OpenAI-compatible API at `http://localhost:20128/v1`. To use it as the LLM provider:

1. Set `LLM_PROVIDER=openai` in `backend/.env`
2. Set `OPENAI_API_BASE=http://localhost:20128/v1` in `backend/.env`
3. Set `OPENAI_API_KEY=none` (OmniRoute doesn't require keys for local usage)
4. Set the model to `auto` or a specific model name

Example `.env` configuration:
```
LLM_PROVIDER=openai
OPENAI_API_BASE=http://localhost:20128/v1
OPENAI_API_KEY=none
OPENAI_MODEL=auto
```

## Dashboard

Access the OmniRoute dashboard at `http://localhost:20128` to:
- View available providers and models
- Monitor usage and costs
- Configure routing strategies
- Manage API keys
- View free tier budgets

Default login password: `CHANGEME` (change immediately)

## Docker

```bash
docker pull diegosouzapw/omniroute
docker run -p 20128:20128 diegosouzapw/omniroute
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OMNIROUTE_SERVER_HOST` | Bind address | `0.0.0.0` |
| `OMNIROUTE_SERVER_PORT` | Port | `20128` |
| `REQUIRE_API_KEY` | Require API key | `false` |
| `INITIAL_PASSWORD` | Dashboard password | `CHANGEME` |
| `DATA_DIR` | Data storage dir | `~/.omniroute` |

## Security Notes

- Default: no API key required (local-first)
- On untrusted networks, set `REQUIRE_API_KEY=true`
- Bind to loopback only: `OMNIROUTE_SERVER_HOST=127.0.0.1`
- Dashboard password is `CHANGEME` by default — change it

## Documentation

Full docs: https://github.com/diegosouzapw/OmniRoute/tree/release/v3.8.51/docs
GitHub: https://github.com/diegosouzapw/OmniRoute
