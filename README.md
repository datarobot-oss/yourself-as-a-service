<p align="center">
    <span style="font-size: 2em; font-weight: bold; display: block;">🤖 YAAS — Yourself as a Service</span>
</p>

<p align="center">
    <span style="font-size: 1.2em; display: block;">An AI agent that embodies your personality, knowledge, and communication style</span>
</p>

<p align="center">
  <a href="https://github.com/datarobot-community/datarobot-agent-application/tags">
    <img src="https://img.shields.io/github/v/tag/datarobot-community/datarobot-agent-application?label=version" alt="Latest Release">
  </a>
  <a href="/LICENSE">
    <img src="https://img.shields.io/github/license/datarobot-community/datarobot-agent-application" alt="License">
  </a>
</p>

---

## See it in action

Watch the video below to see how YAAS was built from scratch in an hour:

[![Build a Production-Ready AI Agent in an Hour | DataRobot Build Club](https://img.youtube.com/vi/JVxVrv8kaYQ/maxresdefault.jpg)](https://www.youtube.com/watch?v=JVxVrv8kaYQ)

Read the [digital twin agent blog post](https://www.datarobot.com/blog/digital-twin-agent/) for a deep dive into the architecture and design decisions behind YAAS.

---

## What is YAAS?

**YAAS (Yourself as a Service)** is an AI agent application that creates a digital version of you. It responds to questions, shares opinions, and engages in conversations using your voice, personality, and perspective — as a Slack bot.

### How It Works

The agent reads your persona definition from a `SOUL.md` file that contains:
- Your personality traits and communication style
- Your technical preferences and opinions
- Your philosophy and approach to problem-solving

When someone @-mentions the bot in Slack, it responds **as you would** — using your vocabulary, referencing your experiences, and applying your judgment. An evaluator agent first decides if the mention actually needs your attention, and a scheduled jobs agent runs background research tasks on your behalf.

### Key Features

- **Personality-driven responses** — Embodies your unique voice via a `SOUL.md` persona file
- **Config-driven identity** — Your name, Slack user ID, and bot name are set once in `.env` and rendered everywhere
- **Slack-native** — Designed for Slack with proper markdown formatting and the Slack Bolt framework
- **Mention evaluation** — An evaluator agent filters noise and only notifies you when a mention actually needs attention
- **Scheduled jobs** — Background research tasks (news digests, Jira summaries, etc.) run on a schedule via APScheduler
- **Knowledge-enhanced** — Optional vector database integration for retrieval-augmented generation from your documents
- **Multi-agent architecture** — Separate specialized agents for the main persona, evaluation, knowledge base storage, scheduled tasks, and response finalization

### Use Cases

- Slack bot that answers questions in your voice when you're unavailable
- Personal assistant that thinks like you do
- Knowledge-sharing agent that captures your expertise and perspective
- Scheduled digests and research briefings delivered to your Slack DMs

# Table of contents

- [See it in action](#see-it-in-action)
- [What is YAAS?](#what-is-yaas)
- [Customizing Your Persona](#customizing-your-persona)
- [Configuration](#configuration)
- [Slack Bot Setup](#slack-bot-setup)
- [Adding Your Knowledge Base](#adding-your-knowledge-base)
- [Scheduled Jobs](#scheduled-jobs)
- [Quick start](#quick-start)
  - [Install prerequisite tools](#install-prerequisite-tools)
  - [Prepare your local development environment](#prepare-your-local-development-environment)
  - [Run your agent](#run-your-agent)
- [Deploy your agent](#deploy-your-agent)
- [Technical Details](#technical-details)
- [Troubleshooting](#troubleshooting)
- [Get help](#get-help)

---

# Customizing Your Persona

The heart of YAAS is the `SOUL.md` file at `agent/SOUL.md`. This file defines who the agent becomes. The `agent/agent/agents/main/SOUL.md` is a symlink to it so the agent always reads the same file.

## SOUL.md Structure

Your `SOUL.md` uses Python format-string syntax for config-driven values. The following variables are substituted at agent startup:

| Variable | Config key | Description |
|---|---|---|
| `{owner_name}` | `OWNER_NAME` | Your name (e.g. `"Carson Gee"`) |
| `{slack_owner_user_id}` | `SLACK_OWNER_USER_ID` | Your Slack user ID (e.g. `"U01234567"`) |
| `{bot_name}` | `BOT_NAME` | The Slack bot's display name (e.g. `"CaaS"`) |

The same variables are substituted in the evaluator and scheduled job agent SOUL files automatically.

### Sections

Your `SOUL.md` should include:

- **Name** — `{owner_name}` (rendered from config)
- **Information** — Professional background, expertise, interests
- **Personality** — Character traits, values, how you interact with others
- **Technical Preferences** — Languages, tools, coding philosophy
- **Communication Style** — Tone, humor, key phrases you use
- **Philosophy** — Core beliefs and worldview

## Editing Your Persona

1. Open `agent/SOUL.md` in your editor
2. Update each section to reflect your personality — be specific, include real phrases and preferences
3. The `{owner_name}`, `{slack_owner_user_id}`, and `{bot_name}` placeholders will be filled from your `.env` at runtime
4. Test the agent locally to ensure it captures the right voice
5. Iterate until the responses feel authentic

After updating `SOUL.md`, restart your agent:

```sh
dr run dev
```

---

# Configuration

All identity and integration configuration lives in your `.env` file. The three key persona-related variables are:

| Variable | Description | Example |
|---|---|---|
| `OWNER_NAME` | Your name — used in SOUL.md persona and agent prompts | `Carson Gee` |
| `BOT_NAME` | The Slack bot's display name | `CaaS` |
| `SLACK_OWNER_USER_ID` | Your Slack user ID — used for DM delivery and persona | `U01234567` |

These are defined once and rendered into every SOUL.md file, the Slack home tab, and any other persona-bearing text at startup.

### Finding Your Slack User ID

In Slack: click your profile picture → **Profile** → **⋮** (More) → **Copy member ID**.

### Full `.env` Reference

```sh
# DataRobot
DATAROBOT_API_TOKEN=your_token
DATAROBOT_ENDPOINT=https://app.datarobot.com/api/v2

# Identity
OWNER_NAME="Your Name"
BOT_NAME="YourBot"
SLACK_OWNER_USER_ID="U01234567"

# Slack bot
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...

# LLM
LLM_DEFAULT_MODEL=datarobot/bedrock/anthropic.claude-sonnet-4-6
USE_DATAROBOT_LLM_GATEWAY=1

# Optional: Tavily search for scheduled jobs
TAVILY_API_KEY=tvly-...

# Optional: OAuth integrations for MCP tools
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

---

# Slack Bot Setup

YAAS is designed to run as a Slack bot using [Slack Bolt](https://slack.dev/bolt-python/) with Socket Mode.

## Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and click **Create New App** → **From a manifest**
2. Use the manifest at `fastapi_server/slack_manifest.yml` as your starting point — update `YOUR_BOT_NAME` placeholders with your actual bot name before pasting
3. Install the app to your workspace

## Get Your Tokens

- **Bot Token** (`SLACK_BOT_TOKEN`): Found in **OAuth & Permissions** → **Bot User OAuth Token** (starts with `xoxb-`)
- **App Token** (`SLACK_APP_TOKEN`): Found in **Basic Information** → **App-Level Tokens** — create one with the `connections:write` scope (starts with `xapp-`)

Set both in your `.env` file.

## Required Scopes

The bot needs these OAuth scopes (configured in the manifest):
- `app_mentions:read` — receive @-mentions
- `channels:history` — read channel messages for context
- `chat:write` — send messages
- `im:write` — send direct messages
- `users:read` — resolve user info

---

# Adding Your Knowledge Base

YAAS can be enhanced with a knowledge base that provides context for your agent to reference. This is optional but powerful for creating an agent that knows about your work, projects, or areas of expertise.

## The `knowledgebase` Folder

Add any documents to the `knowledgebase/` folder at the root of the project:

- Technical documentation you've written
- Project specifications and architecture docs
- Meeting notes and decision records
- PDFs, `.txt`, `.md`, `.docx` files

During deployment, the infra layer automatically:

1. Packages all files into a zip and uploads to DataRobot as a dataset
2. Creates a vector database with configurable chunking and embedding
3. Links the VDB to your agent's LLM deployment
4. Enables retrieval-augmented generation (RAG) for all chat interactions

**You don't write any code** — the vector database is automatically integrated.

## Vector Database Configuration

Customize chunking via `.env`:

```sh
# Chunking method: "recursive" (default) or "overlap"
VDB_CHUNKING_METHOD=recursive

# Size of each chunk in tokens (default: 512)
VDB_CHUNK_SIZE=512

# Percentage overlap between chunks (default: 10)
VDB_CHUNK_OVERLAP_PERCENTAGE=10

# Embedding model
VDB_EMBEDDING_MODEL=intfloat/e5-large-v2
```

## Updating Your Knowledge Base

To update: add/modify files in `knowledgebase/` and redeploy with `dr task run infra:up-yes`. The VDB will be recreated with the new content.

---

# Scheduled Jobs

YAAS includes a scheduler that runs tasks on your behalf at configured intervals. Jobs are stored in the database and executed by the `scheduled_job` agent, which has access to:

- **Web search** (Tavily + DuckDuckGo fallback)
- **Arxiv search** for research/AI topics
- **Jira, Confluence, Gmail, Google Drive** via MCP tools

Results are delivered to your Slack DMs from the bot.

## Managing Schedules

Schedules are managed via the API at `/api/v1/schedules/` (cron format). The agent processes them using APScheduler and runs the research, then posts a Slack summary to you directly.

---

# Quick start

> [!CAUTION]
> This repository is only compatible with macOS and Linux operating systems.
> If you are using Windows, consider using [Windows Subsystem for Linux (WSL)](https://learn.microsoft.com/en-us/windows/wsl/install) or a virtual machine running a supported OS.

## Install prerequisite tools

| Tool | Version | Description | Installation guide |
|---|---|---|---|
| **dr** (DataRobot CLI) | >= 0.2.55 | DataRobot CLI for auth and task execution | [Installation](https://github.com/datarobot-oss/cli#installation) |
| **git** | >= 2.30.0 | Version control | [Installation](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) |
| **uv** | >= 0.9.0 | Python package manager | [Installation](https://docs.astral.sh/uv/getting-started/installation/) |
| **Pulumi** | >= 3.163.0 | Infrastructure as Code | [Installation](https://www.pulumi.com/docs/iac/download-install/) |
| **Taskfile** | >= 3.43.3 | Task runner | [Installation](https://taskfile.dev/docs/installation) |
| **NodeJS** | >= 24 | JavaScript runtime | [Installation](https://nodejs.org/en/download/) |

> [!TIP]
> Install tools **system-wide** rather than in a virtual environment.

**DataRobot CLI:** `curl https://cli.datarobot.com/install | sh` or `brew install datarobot-oss/taps/dr-cli`

<details><summary><b>macOS installation commands</b></summary>
<br>

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install datarobot-oss/taps/dr-cli uv pulumi/tap/pulumi go-task node git
```

</details>

<details><summary><b>Linux installation commands</b></summary>
<br>

```sh
curl https://cli.datarobot.com/install | sh
sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv git nodejs npm
curl -LsSf https://astral.sh/uv/install.sh | sh
curl -fsSL https://get.pulumi.com | sh
sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d
```

</details>

> [!NOTE]
> After installing `uv`, run `uv tool update-shell` once so your shell picks up the updated `PATH`.

## Prepare your local development environment

Run:

```sh
dr start
```

This opens an interactive wizard that configures your DataRobot API token, creates a `.env` file, and sets up your Pulumi stack. Once complete, you have a `.env` in your project root ready for customization.

After the wizard, add your identity and Slack configuration to `.env`:

```sh
OWNER_NAME="Your Name"
BOT_NAME="YourBot"
SLACK_OWNER_USER_ID="U01234567"
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
```

> [!NOTE]
> If you do not have a Pulumi account, use `pulumi login --local` for local login.

## Run your agent

```sh
dr run dev
```

This starts four processes in parallel:

- Application frontend (React/Vite chat UI)
- Application backend (FastAPI + Slack bot)
- Agent (multi-agent LangGraph)
- MCP server

Once running, open [http://localhost:5173](http://localhost:5173) to interact via the chat UI, or watch Slack for the bot to come online.

> [!NOTE]
> To start individual services: `dr run agent:dev`, `dr run fastapi_server:dev`, etc.

---

# Deploy your agent

> [!CAUTION]
> Test locally before deploying.

```sh
dr task run infra:up-yes
```

> [!NOTE]
> The deployment process will take several minutes. If it fails, `dr task run infra:down-yes` tears down the stack cleanly.

Once complete, Pulumi outputs the deployment details including agent endpoints, application URL, and VDB IDs.

---

# Technical Details

## Agent Architecture

YAAS uses a multi-agent LangGraph graph with these specialized nodes:

| Agent | Purpose |
|---|---|
| **Main** | Persona agent — responds as you using `SOUL.md` |
| **Evaluator** | Decides if a Slack @-mention requires your attention (returns JSON, no visible output) |
| **Knowledge Base** | Stores content into the VDB when you DM `Store this: ...` |
| **Scheduled Job** | Runs research tasks on a schedule; posts results to your Slack DMs |
| **Finalizer** | Ensures responses are under 2900 characters with correct Slack markdown formatting |

The router dispatches incoming messages to the right subgraph based on message type (mention evaluation, knowledge base storage, scheduled job, or normal conversation).

## Identity Substitution

All SOUL.md files use Python format-string syntax for persona variables:

```python
# In _load_agent_soul() — agent/agent/myagent.py
content = soul_path.read_text().format(
    owner_name=config.owner_name,
    bot_name=config.bot_name,
    slack_owner_user_id=config.slack_owner_user_id,
)
```

Set `OWNER_NAME`, `BOT_NAME`, and `SLACK_OWNER_USER_ID` in `.env` — they propagate to every SOUL file and Slack UI string automatically.

## Slack Integration

The Slack bot runs via Slack Bolt + Socket Mode in the FastAPI backend. Key behaviors:
- `app_home_opened` — renders the home tab with your bot name and a description
- `app_mention` — routes to the evaluator agent, then optionally notifies you via DM
- Socket Mode means no public webhook URL is required

## Knowledge Base and Vector Database

Deployed automatically by `infra/infra/data.py`:

1. Zips `knowledgebase/` and uploads as a DataRobot dataset
2. Creates a vector database with your configured chunking parameters
3. Attaches the VDB to the agent's LLM deployment for automatic RAG

## MCP Server

The MCP server (FastMCP) provides tools the scheduled job agent can call: Jira, Confluence, Gmail, Google Drive, and DataRobot operations. Tools are auto-discovered from `mcp_server/app/tools/`.

---

# Troubleshooting

## Ports reference

| Port | Component | Configurable |
|---|---|---|
| 8080 | Web application (proxied frontend) | No |
| 5173 | Vite dev server | No |
| 8842 | Agent endpoint | Yes (`AGENT_PORT`) |
| 9000 | MCP server | Yes (`MCP_SERVER_PORT`) |

## Common Issues

### Slack bot not responding

- Verify `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` are set in `.env`
- Ensure the app has Socket Mode enabled in the Slack dashboard
- Check that the bot is invited to the channel where you @-mentioned it

### SOUL.md format errors on startup

- The SOUL files use `{variable}` format-string syntax — any literal `{` or `}` in the text must be escaped as `{{` or `}}`
- Check that `OWNER_NAME`, `BOT_NAME`, and `SLACK_OWNER_USER_ID` are set in `.env`

### Port conflicts

```sh
lsof -i :PORT | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### Service startup failures

```sh
# Verify tools
dr --version && uv --version && pulumi version && task --version

# Reinstall dependencies
dr run install
```

### Deployment failures

```sh
pulumi whoami   # ensure logged in
pulumi stack ls # verify correct stack
dr task run infra:down-yes && dr task run infra:up-yes  # clean redeploy
```

---

# Get help

- [DataRobot agentic AI documentation](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/index.html)
- [DataRobot CLI documentation](https://github.com/datarobot-oss/cli)
- [Contact DataRobot support](https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html)

<p align="center">
    <span style="font-size: 1.5em; font-weight: bold; display: block;">Agentic Starter application template</span>
</p>

<p align="center">
  <a href="https://datarobot.com">Homepage</a>
  ·
  <a href="https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/index.html">Documentation</a>
  ·
  <a href="https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html">Support</a>
</p>

<p align="center">
  <a href="https://app.datarobot.com/usecases/application-templates/69090966c601dbd8c8514516?referrerUrl=github">
    <img src="https://img.shields.io/badge/US-Open%20in%20a%20Codespace-%23909BF5?style=flat&labelColor=%2330373D" alt="US - Open in a Codespace">
  </a>
  <a href="https://app.eu.datarobot.com/usecases/application-templates/69090966c601dbd8c8514516?referrerUrl=github">
    <img src="https://img.shields.io/badge/EU-Open%20in%20a%20Codespace-%232BC46F?labelColor=%2330373D" alt="EU - Open in a Codespace">
  </a>
  <a href="https://app.jp.datarobot.com/usecases/application-templates/69090966c601dbd8c8514516?referrerUrl=github">
    <img src="https://img.shields.io/badge/JP-Open%20in%20a%20Codespace-%23EDA769?labelColor=%2330373D" alt="JP - Open in a Codespace">
  </a>
  <a href="https://app.jp.datarobot.com/usecases/application-templates/69090966c601dbd8c8514516?referrerUrl=github">
    <img src="https://img.shields.io/badge/JP-%E3%80%8CCodespace%20%E3%81%A7%E9%96%8B%E3%81%8F%E3%80%8D-%23EDA769?labelColor=%2330373D" alt="JP - 「Codespaceで開く」">
  </a>
  <a href="https://github.com/datarobot-community/datarobot-agent-application/tags">
    <img src="https://img.shields.io/github/v/tag/datarobot-community/datarobot-agent-application?label=version" alt="Latest Release">
  </a>
  <a href="/LICENSE">
    <img src="https://img.shields.io/github/license/datarobot-community/datarobot-agent-application" alt="License">
  </a>
  <a href="https://join.slack.com/t/datarobot-community/shared_invite/zt-3uzfp8k50-SUdMqeux25ok9_5wr4okrg">
    <img src="https://img.shields.io/badge/%23applications-a?label=Slack&labelColor=30373D&color=81FBA6" alt="Slack #applications">
  </a>
</p>

This repository provides a ready-to-use application template for building and deploying agentic workflows with multi-agent frameworks, a FastAPI backend server, a React frontend, and an MCP server.
The template streamlines the process of setting up new agentic applications with minimal configuration requirements.
It supports local development and testing, as well as one-command deployments to production environments within DataRobot.

> [!CAUTION]
> This repository updates frequently.
> Make sure to update your local branch regularly to obtain the latest changes.

