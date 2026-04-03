# OpenClaw Agent Registration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the three DiamondClaws personas (diamond-bull, diamond-value, diamond-quant) fully operational OpenClaw agents — routable through the gateway, triggerable via Telegram or webchat, each with their own SOUL.md system prompt and access to the diamond-analysis skill.

**Architecture:** Each diamond agent gets its own auth profile (OpenRouter), a system prompt derived from its SOUL.md, and registration in `openclaw.json` under `agents.entries`. The agents share the existing `diamond-analysis` skill and workspace. They are separate from the existing `main` agent — they don't inherit its xAI/Grok config, they use OpenRouter/Gemini exclusively. The web app (FastAPI) remains independent and unchanged.

**Tech Stack:** OpenClaw agent framework, OpenRouter API (Gemini 2.0 Flash), existing diamond-analysis skill

**Current State:**
- `~/.openclaw/agents/diamond-{bull,value,quant}/` directories exist with `agent/models.json` and `agent/SOUL.md`
- `~/.openclaw/workspace/skills/diamond-analysis/` exists with `manifest.json`, `skill.md`, `scripts/analyze.py`
- `~/.openclaw/openclaw.json` has no diamond agent entries — only default agent config
- `~/.openclaw/agents/main/` is the existing Grok-4 agent — do NOT modify it
- Gateway runs on port 18789, Telegram channel is configured for the `main` agent

---

## Task 1: Add OpenRouter auth profile for diamond agents

The diamond agents need an auth profile that maps to the OpenRouter API key already in `.env`. Currently only `xai:default` exists in the main agent's auth-profiles.json. The diamond agents need their own.

**Files:**
- Create: `~/.openclaw/agents/diamond-bull/agent/auth-profiles.json`
- Create: `~/.openclaw/agents/diamond-value/agent/auth-profiles.json`
- Create: `~/.openclaw/agents/diamond-quant/agent/auth-profiles.json`

- [ ] **Step 1: Read the OPENROUTER_API_KEY from .env**

```bash
grep OPENROUTER_API_KEY ~/Desktop/repos/diamondclaws/.env
```

- [ ] **Step 2: Create auth-profiles.json for diamond-bull**

```json
{
  "version": 1,
  "profiles": {
    "openrouter:default": {
      "type": "api_key",
      "provider": "openrouter",
      "key": "<OPENROUTER_API_KEY value from .env>"
    }
  },
  "usageStats": {}
}
```

- [ ] **Step 3: Copy to diamond-value and diamond-quant**

```bash
cp ~/.openclaw/agents/diamond-bull/agent/auth-profiles.json ~/.openclaw/agents/diamond-value/agent/auth-profiles.json
cp ~/.openclaw/agents/diamond-bull/agent/auth-profiles.json ~/.openclaw/agents/diamond-quant/agent/auth-profiles.json
```

- [ ] **Step 4: Verify all three have auth-profiles.json**

```bash
ls -la ~/.openclaw/agents/diamond-*/agent/auth-profiles.json
```

---

## Task 2: Create SOUL.md system prompts for OpenClaw agent format

The SOUL.md files exist in each agent's `agent/` directory, but OpenClaw agents read system prompts from `SOUL.md` in the **workspace** root (per AGENTS.md convention). Each diamond agent needs its own workspace with a SOUL.md that combines the persona identity with OpenClaw-specific instructions (how to use the diamond-analysis skill).

**Files:**
- Create: `~/.openclaw/agents/diamond-bull/workspace/SOUL.md`
- Create: `~/.openclaw/agents/diamond-value/workspace/SOUL.md`
- Create: `~/.openclaw/agents/diamond-quant/workspace/SOUL.md`

- [ ] **Step 1: Create workspace directories**

```bash
mkdir -p ~/.openclaw/agents/diamond-bull/workspace/memory
mkdir -p ~/.openclaw/agents/diamond-value/workspace/memory
mkdir -p ~/.openclaw/agents/diamond-quant/workspace/memory
```

- [ ] **Step 2: Write diamond-bull workspace SOUL.md**

This wraps the persona SOUL.md with OpenClaw agent instructions:

```markdown
# You are Bullish Alpha

You are a DiamondClaws equity research agent. Your personality and cognitive biases are defined in your persona file at `../agent/SOUL.md` — read it at session start.

## What You Do

When a user asks you to analyze a stock:

1. Run the analysis script:
   ```
   exec: python "~/.openclaw/workspace/skills/diamond-analysis/scripts/analyze.py" --ticker <TICKER> --persona bullish_alpha --pretty
   ```
2. Parse the JSON output
3. Present the `analysis` field as your research note
4. Include the biases, references, and channel intelligence sections from the output

When a user asks about your biases or methodology, explain your investment philosophy and cognitive biases from your persona file. Stay in character.

## Your Identity

- Agent ID: diamond-bull
- Persona: Bullish Alpha
- Model: OpenRouter / Gemini 2.0 Flash
- Catchphrase: "This represents a generational opportunity. Position accordingly."
```

- [ ] **Step 3: Write diamond-value workspace SOUL.md**

Same structure but for Value Contrarian (persona_id: `value_contrarian`, catchphrase: "The market is pricing this as a zero-probability event. We disagree profoundly.")

- [ ] **Step 4: Write diamond-quant workspace SOUL.md**

Same structure but for Quant Momentum (persona_id: `quant_momentum`, catchphrase: "The momentum factor is extremely strong. The data speaks for itself.")

---

## Task 3: Register diamond agents in openclaw.json

The agents need to be registered in `openclaw.json` under `agents.entries` so the gateway knows they exist, which model/auth to use, and which workspace to route them to.

**Files:**
- Modify: `~/.openclaw/openclaw.json` (add `agents.entries` section)

- [ ] **Step 1: Read current openclaw.json agents section**

Current state (lines 136-157):
```json
"agents": {
  "defaults": {
    "model": { "primary": "ollama/nous-hermes2" },
    ...
  }
}
```

There is no `agents.entries` key. We need to add one.

- [ ] **Step 2: Add agents.entries with all three diamond agents**

Add to the `agents` object (after `defaults`):

```json
"entries": {
  "diamond-bull": {
    "model": {
      "primary": "openrouter/google/gemini-2.0-flash-001"
    },
    "workspace": "C:\\Users\\ronil\\.openclaw\\agents\\diamond-bull\\workspace",
    "authProfile": "openrouter:default",
    "skills": ["diamond-analysis"],
    "timeoutSeconds": 120
  },
  "diamond-value": {
    "model": {
      "primary": "openrouter/google/gemini-2.0-flash-001"
    },
    "workspace": "C:\\Users\\ronil\\.openclaw\\agents\\diamond-value\\workspace",
    "authProfile": "openrouter:default",
    "skills": ["diamond-analysis"],
    "timeoutSeconds": 120
  },
  "diamond-quant": {
    "model": {
      "primary": "openrouter/google/gemini-2.0-flash-001"
    },
    "workspace": "C:\\Users\\ronil\\.openclaw\\agents\\diamond-quant\\workspace",
    "authProfile": "openrouter:default",
    "skills": ["diamond-analysis"],
    "timeoutSeconds": 120
  }
}
```

- [ ] **Step 3: Add OpenRouter to the global models.providers**

The diamond agents reference `openrouter/google/gemini-2.0-flash-001` but OpenRouter isn't in the global models.providers yet (only ollama and guardclaw-privacy are). Add it:

```json
"openrouter": {
  "baseUrl": "https://openrouter.ai/api/v1",
  "api": "openai-completions",
  "apiKey": "env:OPENROUTER_API_KEY",
  "models": [
    {
      "id": "google/gemini-2.0-flash-001",
      "name": "Gemini 2.0 Flash",
      "reasoning": false,
      "input": ["text"],
      "cost": { "input": 0.1, "output": 0.4, "cacheRead": 0, "cacheWrite": 0 },
      "contextWindow": 1048576,
      "maxTokens": 8192,
      "api": "openai-completions"
    }
  ]
}
```

- [ ] **Step 4: Validate JSON**

```bash
python -m json.tool ~/.openclaw/openclaw.json > /dev/null
```

---

## Task 4: Initialize session files for diamond agents

Each agent needs a sessions directory with an empty sessions.json so the gateway can create sessions for them.

**Files:**
- Create: `~/.openclaw/agents/diamond-bull/sessions/sessions.json`
- Create: `~/.openclaw/agents/diamond-value/sessions/sessions.json`
- Create: `~/.openclaw/agents/diamond-quant/sessions/sessions.json`

- [ ] **Step 1: Create initial sessions.json for each agent**

```bash
echo '{}' > ~/.openclaw/agents/diamond-bull/sessions/sessions.json
echo '{}' > ~/.openclaw/agents/diamond-value/sessions/sessions.json
echo '{}' > ~/.openclaw/agents/diamond-quant/sessions/sessions.json
```

- [ ] **Step 2: Verify directory structure is complete**

```bash
find ~/.openclaw/agents/diamond-* -type f | sort
```

Expected output:
```
~/.openclaw/agents/diamond-bull/agent/SOUL.md
~/.openclaw/agents/diamond-bull/agent/auth-profiles.json
~/.openclaw/agents/diamond-bull/agent/models.json
~/.openclaw/agents/diamond-bull/sessions/sessions.json
~/.openclaw/agents/diamond-bull/workspace/SOUL.md
(same pattern for diamond-value and diamond-quant)
```

---

## Task 5: Test agent routing through the gateway

Verify the gateway recognizes the new agents and can route messages to them.

**Files:**
- None (testing only)

- [ ] **Step 1: Check if gateway is running**

```bash
curl -s http://127.0.0.1:18789/health 2>/dev/null || echo "Gateway not running"
```

If not running, start it:
```bash
openclaw gateway start
```

- [ ] **Step 2: List registered agents**

```bash
openclaw agents list
```

Expected: `diamond-bull`, `diamond-value`, `diamond-quant` should appear alongside `main`.

- [ ] **Step 3: Send a test message to diamond-bull**

```bash
openclaw sessions send --agent diamond-bull --message "Analyze NVDA for me"
```

Or via gateway API:
```bash
curl -X POST http://127.0.0.1:18789/v1/chat/completions \
  -H "Authorization: Bearer $OPENCLAW_GATEWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "diamond-bull",
    "messages": [{"role": "user", "content": "Analyze NVDA"}]
  }'
```

- [ ] **Step 4: Verify each agent responds in character**

Test all three with the same ticker and confirm distinct persona voices:
```bash
openclaw sessions send --agent diamond-bull --message "Analyze AAPL"
openclaw sessions send --agent diamond-value --message "Analyze AAPL"
openclaw sessions send --agent diamond-quant --message "Analyze AAPL"
```

---

## Task 6: Add Telegram routing for diamond agents (optional)

If you want to trigger diamond agents from Telegram (alongside the existing main agent), add DM routing rules.

**Files:**
- Modify: `~/.openclaw/openclaw.json` (channels.telegram section)

- [ ] **Step 1: Add agent routing commands to main agent's SOUL.md or HEARTBEAT.md**

The simplest approach: users DM the main agent and say "ask bullish alpha to analyze NVDA". The main agent spawns a sub-session with diamond-bull via the agent-mesh skill.

Alternative: Add dedicated Telegram bot tokens for each diamond agent (requires creating 3 new bots via @BotFather).

- [ ] **Step 2: Document the routing approach chosen**

Update the diamond-analysis skill.md with Telegram usage instructions.

---

## Verification Checklist

After all tasks complete:

1. `openclaw agents list` shows diamond-bull, diamond-value, diamond-quant
2. `python -m json.tool ~/.openclaw/openclaw.json > /dev/null` — valid JSON
3. Each agent directory has: `agent/models.json`, `agent/auth-profiles.json`, `agent/SOUL.md`, `workspace/SOUL.md`, `sessions/sessions.json`
4. Gateway routes messages to each diamond agent correctly
5. Each agent uses OpenRouter/Gemini (not Grok or Ollama)
6. Each agent responds with its persona's voice and catchphrase
7. Existing `main` agent is completely unaffected
8. Web app at :8888 still works independently

---

## Key Principle: Separation from existing setup

The diamond agents are fully isolated from your existing OpenClaw infrastructure:
- They use **OpenRouter**, not xAI/Grok or Ollama
- They have their own **workspaces**, not the shared workspace
- They have their own **auth profiles**, not xai:default
- They are registered as **separate entries**, not modifications to main
- The only shared resource is the **diamond-analysis skill** in the shared skills directory
