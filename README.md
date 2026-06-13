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

# Table of contents

- [Quick start](#quick-start)
  - [Install prerequisite tools](#install-prerequisite-tools)
  - [Prepare your local development environment](#prepare-your-local-development-environment)
  - [Run your agent](#run-your-agent)
- [Develop your agent](#develop-your-agent)
  - [Component documentation](#component-documentation)
  - [DataRobot documentation](#datarobot-documentation)
- [Deploy your agent](#deploy-your-agent)
- [MCP server](#mcp-server)
- [OAuth applications](#oauth-applications)
- [Agent-to-agent](#agent-to-agent)
- [Troubleshooting](#troubleshooting)
- [Get help](#get-help)

For information on the latest changes to the template, see the [CHANGELOG](CHANGELOG.md).

# Quick start

Follow the instructions in the sections below to install the prerequisite tools and develop the Agentic Starter application template locally.

> [!CAUTION]
> This repository is only compatible with macOS and Linux operating systems.
> If you are using Windows, consider using a [DataRobot codespace](https://docs.datarobot.com/en/docs/workbench/wb-notebook/codespaces/index.html), [Windows Subsystem for Linux (WSL)](https://learn.microsoft.com/en-us/windows/wsl/install), or a virtual machine running a supported OS.

## Install prerequisite tools

Before you begin, you'll need the following tools installed.
If you already have these tools installed, ensure that they are at the required version (or newer) indicated in the table below.
For example commands to install the tools, see the [Detailed installation commands](#detailed-installation-commands) section.

| Tool         | Version    | Description                     | Installation guide            |
|--------------|------------|---------------------------------|-------------------------------|
| **dr** (DataRobot CLI) | >= 0.2.55  | The DataRobot CLI for templates, auth, and task execution. | [DataRobot CLI installation](https://github.com/datarobot-oss/cli#installation) |
| **git**      | >= 2.30.0  | A version control system.       | [git installation guide](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)      |
| **uv**       | >= 0.9.0  | A Python package manager.        | [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)       |
| **Pulumi**   | >= 3.163.0 | An Infrastructure as Code tool. | [Pulumi installation guide](https://www.pulumi.com/docs/iac/download-install/)                   |
| **Taskfile** | >= 3.43.3  | A task runner.                  | [Taskfile installation guide](https://taskfile.dev/docs/installation)                        |
| **NodeJS**   | >= 24      | JavaScript runtime for frontend development. | [NodeJS installation guide](https://nodejs.org/en/download/)                        |

> [!TIP]
> Make sure to install the tools **system-wide** rather than in a virtual environment so they are available in your terminal sessions.

**DataRobot CLI (dr):** Install the latest version with `curl https://cli.datarobot.com/install | sh` (macOS/Linux) or via Homebrew: `brew install datarobot-oss/taps/dr-cli`. To update: `dr self update`. Verify with `dr --version` or `dr self version`.

### Detailed installation commands

The following sections provide example installation commands for macOS and Linux (Debian/Ubuntu/DataRobot codespace).
Click the dropdown below that corresponds to your operating system:

- <details><summary><b>macOS</b></summary>
  <br>

  macOS users can install the prerequisite tools using Homebrew. First, install Homebrew if you don't already have it.

  ```sh
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" # If homebrew is not already installed
  ```

  Then, install the prerequisite tools with it:

  ```sh
  brew install datarobot-oss/taps/dr-cli uv pulumi/tap/pulumi go-task node git
  ```

</details>

- <details><summary><b>Linux</b></summary>
  <br>

  Linux users can install the prerequisite tools using the package manager for their distribution.

  ```sh
  curl https://cli.datarobot.com/install | sh
  sudo apt-get update
  sudo apt-get install -y python3 python3-pip python3-venv
  sudo apt-get install -y git
  curl -LsSf https://astral.sh/uv/install.sh | sh
  curl -fsSL https://get.pulumi.com | sh
  sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d
  sudo apt-get install -y nodejs npm
  ```

</details>

> [!NOTE]
> After installing `uv`, run `uv tool update-shell` once so your shell picks up the updated `PATH` before using `uv tool run` or invoking tools installed via `uv tool install`.

> [!IMPORTANT]
> You will also need a compatible C++ compiler and build tools installed on your system to compile some Python packages.

<details><summary><i>Click here for details on using a development container</i></summary>

### Use a development container (experimental)

[Dev containers](https://containers.dev/) allow you to use a container environment for local development. They are integrated with [modern IDEs](https://containers.dev/supporting) such as VSCode and PyCharm, and the [Dev Container CLI](https://containers.dev/supporting#devcontainer-cli) allows you to integrate them with terminal-centric development workflows.

> [!NOTE]
> This can also be used as a solution for Windows development. [Docker Desktop](https://docs.docker.com/desktop/) is the recommended backend for running devcontainers, but any Docker-compatible backend is supported.

This template offers a `devcontainer` with all prerequisites installed. To start working in it:

1. Open the template in PyCharm (version >= 2023.2, Pro) or VSCode, and the IDE will prompt you to reopen it in a container.

*PyCharm*:

<img src="docs/img/pycharm-devcontainer.png" alt="Open in Dev Container PyCharm" width="350px" />

*VSCode*:

<img src="docs/img/vscode-devcontainer.png" alt="Open in Dev Container VSCode" width="350px" />

2. Click **Reopen in Container** to proceed.
3. If you work directly in the terminal, run:

```sh
devcontainer up --workspace-folder . \&\& devcontainer exec --workspace-folder . /bin/sh
```

</details>

> [!NOTE]
> If you do not have a Pulumi account, use `pulumi login --local` for local login or create a free account at [the Pulumi website](https://app.pulumi.com/signup).

## Prepare your local development environment

> [!NOTE]
> If you are using a DataRobot codespace, you must expose several ports for local testing. See the [DataRobot codespace port configuration](#datarobot-codespace-port-configuration) section for more details.

Run the following command to start the local development environment:

```sh
dr start
```

If you run `dr start` from a directory that is not yet a template clone, you will first go through template selection and clone; once in the template directory, the wizard guides you through configuring your application and creates a `.env` file.
You will see progress lines in the terminal (e.g., ✓ Starting application quickstart process…, ✓ Checking DataRobot CLI version…, and so on) as each step runs.
For more details for the individual wizard steps, click the dropdown below.

<details><summary><b>Click here for a detailed walkthrough of the wizard steps</b></summary>
<br>

1. Initially, the wizard opens a web browser window to automatically configure your API endpoint and key.
   - If the browser doesn't open automatically, look for a URL in the terminal output and open it manually.
   - Click **Proceed** in the browser to continue.
   - If you encounter authentication issues, ensure you're logged into DataRobot in your browser.
2. Select the Agentic Starter and press `Enter`.
3. Enter the directory name for your application and press `Enter`. The default is `datarobot-agent-application`.
4. Provide a secret key to sign cookies for your session and press `Enter`. If you do not provide a value, a randomly-generated one will be used.
5. Choose your OAuth provider and press `Enter`.
   - Choose **DataRobot OAuth Provider** (default) to use DataRobot’s OAuth, or **Authlib OAuth Provider** to host OAuth in the app.
   - For additional information on authorization server configuration, see the [OAuth applications documentation](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-authentication.html#oauth-2-0-authentication).
6. Enter a passphrase (or leave blank if you don't want to use a passphrase) for your Pulumi stack and press `Enter`.
7. Specify the ID of a DataRobot Use Case (e.g., `69331fad5e07469e7c4f5c6f`), if one is available, and press `Enter`.
   - You can find your Use Case ID by navigating to the Use Case in the DataRobot UI and copying the ID from the URL.
   - If left blank, a new Use Case will be created automatically.
8. Specify your LLM integration and press `Enter`.
   - For additional information on LLM configuration, see the [LLM configuration documentation](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-llm-providers-metadata.html).
   - If you choose **DataRobot Deployed LLM**, you enter the deployment ID for your custom model LLM (`LLM_DEPLOYMENT_ID`). The template sets `USE_DATAROBOT_LLM_GATEWAY=0` automatically so traffic goes to that deployment rather than the LLM Gateway.
9. Review the `.env` configuration summary displayed and press `Enter` to confirm.

   > NOTE: This step will take several minutes to complete.

10. Once the configuration finishes, you can specify if you wish to use the YAML-based NeMo Agent Toolkit template:
   - Press `y` to use the YAML-based NeMo Agent Toolkit template.
   - Press `n` to choose from a list of available agent templates (default).
11. Finally, choose a Pulumi stack to use for your application and press `Enter`. If you wish to create a new stack, press `Enter` and you will be prompted to enter a name for it. The name cannot match any existing stack name.

</details>

> [!NOTE]
> The first time you run `dr start` in this template, it runs `task start`, which prepares your development environment (agent choice, `.env` configuration, and dependencies). Completion is tracked so later runs can skip redundant steps. To change environment variables later, use `dr dotenv setup` or `dr dotenv edit`. To update the agent component (e.g., after pulling template changes), run `dr component update`.

After `dr start` completes successfully, you have:

- A `.env` file in your project root.
- Your application directory created (named `datarobot-agent-application` by default).

If you encounter any errors during setup, see the [Troubleshooting](#troubleshooting) section for help.
Now that your application is configured, proceed to the next section.

## Run your agent

Navigate to the application directory created during `dr start`:

```sh
cd datarobot-agent-application # or the custom directory name you specified during the wizard, if different
```

Run the following command to start all components of the application:

```sh
dr run dev
```

This starts four processes, running in parallel:

- Application frontend
- Application backend
- Agent
- MCP server

Once all services are running:

1. Open your web browser and navigate to [http://localhost:5173](http://localhost:5173) to see the Agentic Starter interface.
2. Send a test message to verify that everything is working as expected.

From here, start customizing the agent by adding your own logic and functionality. See the section on [developing your agent](#develop-your-agent) for more details.

> [!NOTE]
> You can also start individual services in separate terminal windows; for example, `dr run agent:dev` (or `task agent:dev`) will start just the agent.

# Develop your agent

Now that your agent has been built and tested, you are ready to customize it by adding your own logic and functionality.
The agent implementation lives in **`./agent/agent/`**: the main agent class is in `agent/agent/myagent.py` (`MyAgent`).
For structure and required components, see [AGENTS.md](AGENTS.md#agent-structure).
The template includes **chat history** support: conversation context is injected into the agent so multi-turn chats stay consistent.
The frontend uses the **DataRobot UI component registry** (`@dr-ui`) for theming and reusable components; you can customize the UI via the shared theme and component set.

## Component documentation

The `docs/` directory contains detailed documentation for each component of this template:

| Document | Description |
|---|---|
| [Agent](docs/agent/README.md) | Agent architecture, file structure, framework-specific guides, tool integration, front servers, and debugging. |
| [LLM component](docs/llm.md) | Configuring LLM providers, DataRobot gateway, deployments, and external APIs. |
| [MCP server](docs/mcp-server.md) | MCP server architecture, custom tools, and deployment. |
| [OAuth applications](docs/oauth-applications.md) | OAuth provider setup for external service authentication. |

The agent documentation includes per-framework guides with tool integration and prompt modification examples:

| Framework | Guide |
|---|---|
| LangGraph (default) | [docs/agent/frameworks/langgraph.md](docs/agent/frameworks/langgraph.md) |
| CrewAI | [docs/agent/frameworks/crewai.md](docs/agent/frameworks/crewai.md) |
| LlamaIndex | [docs/agent/frameworks/llamaindex.md](docs/agent/frameworks/llamaindex.md) |
| NAT (NeMo Agent Toolkit) | [docs/agent/frameworks/nat.md](docs/agent/frameworks/nat.md) |
| Base (generic) | [docs/agent/frameworks/base.md](docs/agent/frameworks/base.md) |

See also: [AG-UI integration](docs/agent/ag-ui.md), [Agent-to-Agent (A2A)](docs/agent/agent2agent.md), [Debugging](docs/agent/debugging.md).

## DataRobot documentation

For additional guidance beyond what this template covers, see the official DataRobot documentation:

- [Customize your agent](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-development.html)&mdash;modify agent logic, prompts, and behavior.
- [Add tools to your agent](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-tools-integrate.html)&mdash;integrate MCP, custom, and global tools.
- [Configure LLM providers](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-llm-providers.html)&mdash;set up DataRobot gateway, deployments, or external APIs.
- [Add Python packages](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-python-packages.html)&mdash;manage dependencies via `uv` and custom Docker images.
- [Manage prompts](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-development.html#modify-agent-prompts)&mdash;modify agent prompts per framework.
- [Agent authentication](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-authentication.html)&mdash;API tokens, OAuth 2.0, and credential management.
- [Deploy agentic tools](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-tools.html)&mdash;deploy global tools from the DataRobot Registry.
- [DataRobot agentic skills](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-skills.html)&mdash;install modular skill packages for coding agents.
- [Implement tracing](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-tracing-code.html)&mdash;add custom OpenTelemetry tracing for deployed agents.
- [Troubleshooting](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-troubleshooting.html)&mdash;diagnose common setup, deployment, and runtime issues.

# Deploy your agent

Next, deploy your agent to DataRobot, which requires a Pulumi login.
Run the following command to deploy:

```sh
dr run deploy
```

> [!NOTE]
> The deployment process will take several minutes to complete.

Once deployment is complete, the script displays the deployment details, as shown in the example below. Note that the deployment details will vary based on your configuration.

```sh
Outputs:
    AGENT_DEPLOYMENT_ID                               : "69331fad5e07469e7c4f5c6f"
    Agent Custom Model Chat Endpoint [apptest] [agent]: "https://datarobot.com/api/v2/genai/agents/fromCustomModel/69331f816e1bf9f1890d5d1d/chat/"
    Agent Deployment Chat Endpoint [apptest] [agent]  : "https://datarobot.com/api/v2/deployments/69331fad5e07469e7c4f5c6f/chat/completions"
    Agent Execution Environment ID [apptest] [agent]  : "680fe4949604e9eba46b1775"
    Agent Playground URL [apptest] [agent]            : "https://datarobot.com/usecases/69331e4c3be0efe3b95a7be0/agentic-playgrounds/69331e4d1c036307186c9b16/comparison/chats"
    Agentic Starter [apptest]             : "https://datarobot.com/custom_applications/6933204a9e21e9b59b5a7bee/"
    DATABASE_URI                                      : "sqlite+aiosqlite:////tmp/agent_app/.data/agent_app.db"
    DATAROBOT_APPLICATION_ID                          : "6933204a9e21e9b59b5a7bee"
    DATAROBOT_OAUTH_PROVIDERS                         : (json) []

    LLM_DEFAULT_MODEL                                 : "azure/gpt-4o-2024-11-20"
    SESSION_SECRET_KEY                                : "secretkey123"
    USE_DATAROBOT_LLM_GATEWAY                         : "1"
    [apptest] [mcp_server] Custom Model Id            : "69331eebb49131d3d5430ac7"
    [apptest] [mcp_server] Deployment Id              : "69331f1f30548f83b668d9dc"
    [apptest] [mcp_server] MCP Server Base Endpoint   : "https://datarobot.com/api/v2/deployments/69331f1f30548f83b668d9dc/directAccess/"
    [apptest] [mcp_server] MCP Server MCP Endpoint    : "https://datarobot.com/api/v2/deployments/69331f1f30548f83b668d9dc/directAccess/mcp"
```

# MCP server

The Model Context Protocol (MCP) is an open standard that allows AI agents, such as large language models (LLMs), to discover and interact with external data sources, applications, and services in a secure and structured way.
For detailed information about the MCP server, see [MCP server documentation](docs/mcp-server.md).

# OAuth applications

For detailed information about configuring OAuth applications, see [OAuth applications documentation](docs/oauth-applications.md).

# Troubleshooting

This section covers common issues you may encounter and how to resolve them.

## Ports reference

The following ports are used by the application components during local development:

| Port  | Component                    | Description                                    | Configurable |
|-------|------------------------------|------------------------------------------------|--------------|
| 8080  | Web application              | Main web interface (proxied frontend)          | No           |
| 5173  | Vite dev server              | Frontend development server                    | No           |
| 8842  | Agent endpoint               | Local agent service endpoint                   | Yes (in wizard) |
| 9000  | MCP server                   | Model Context Protocol server                  | Yes (via `MCP_SERVER_PORT`) |

> [!NOTE]
> Ports 8080 and 5173 are fixed. The agent endpoint (8842) can be configured during the `dr start` wizard, and the MCP server port (9000) can be changed by setting the `MCP_SERVER_PORT` environment variable in your `.env` file.

### DataRobot codespace port configuration

If you are developing within a DataRobot codespace, the development ports need to be exposed.
This is configured in the **Exposed Ports** section of your **Session Environment** tab (pictured below).
The ports in the table above must be exposed for local testing.
If you cloned this application template using the `dr start` command and selected it from the gallery, this configuration is performed automatically; otherwise (e.g., if cloned manually) you must configure these ports manually.

There is a link next to the port to a URL where the service can be accessed when running locally in the codespace.

<img src="docs/img/codespace-ports.png" alt="Ports" width="500px" />

## DataRobot CLI issues

### Issue: "dr: command not found"

**Symptoms**: The shell cannot find the `dr` command.

**Solutions**:

1. Ensure the DataRobot CLI is installed (see [Install prerequisite tools](#install-prerequisite-tools)).
2. Check that the CLI binary is in your PATH:

   ```sh
   which dr
   # If not found, you may need to add the install directory to PATH (e.g. /usr/local/bin)
   export PATH="/usr/local/bin:$PATH"
   ```

### Issue: CLI version too old or template requires a newer dr

**Symptoms**: The template or `dr start` reports that your CLI version is below the minimum (see `.datarobot/cli/versions.yaml`).

**Solution**: Update the DataRobot CLI:

```sh
dr self update
dr self version   # verify
```

## Port conflicts

### Issue: "Address already in use" or port conflict errors

**Symptoms**: Services fail to start with port conflict errors.

**Solutions**:

1. **Identify the process using the port**:

   ```sh
   # For port 8080 (web application)
   lsof -i :8080

   # For port 9000 (MCP server)
   lsof -i :9000

   # For port 5173 (Vite dev server)
   lsof -i :5173
   ```

2. **Kill the process** (replace `PORT` with the actual port number):

   ```sh
   lsof -i :PORT | grep LISTEN | awk '{print $2}' | xargs kill -9
   ```

3. **Or change the port**:
   - For MCP server: Set `MCP_SERVER_PORT` in your `.env` file
   - For agent endpoint: Configure during `dr start` wizard (default is 8842)

## Service startup issues

### Issue: Services won't start or fail immediately

**Solutions**:

1. **Verify prerequisites are installed**:

   ```sh
   dr --version
   git --version
   uv --version
   pulumi version
   task --version
   node --version
   ```

2. **Check dependencies are installed**:

   ```sh
   dr run install
   ```

3. **Verify environment variables**:
   - Ensure `.env` file exists in the project root
   - Check that required variables are set (see [Prepare your local development environment](#prepare-your-local-development-environment) section)

4. **Check logs**:
   - Review terminal output for specific error messages
   - Check for missing API tokens or invalid endpoints

## Quickstart and wizard issues

### Issue: "No start command or quickstart script found"

**Symptoms**: You run `dr start` inside a DataRobot template directory and see a message that no start command or quickstart script was found.

**Explanation**: The CLI looks for either a `task start` task in the Taskfile or an executable script in `.datarobot/cli/bin/` whose name starts with `quickstart`. This template provides `task start` in the root `Taskfile.yml`. If you see this message, the Taskfile may be missing or not generated yet (run `dr task compose` if applicable).

### Issue: `dr start` wizard fails or is interrupted

**Solutions**:

1. **Restart the wizard**:

   ```sh
   dr start
   ```

2. **Check for existing configuration**:
   - If `.env` file exists, you may need to remove it and start fresh:

     ```sh
     # Backup first if needed
     cp .env .env.backup
     rm .env
     dr start
     ```

3. **Verify DataRobot credentials**:
   - Ensure you have a valid DataRobot API token
   - Check that your DataRobot endpoint URL is correct
   - Verify your account has necessary permissions

4. **Check network connectivity**:
   - Ensure you can access your DataRobot instance
   - Verify firewall settings allow connections

## MCP server connection issues

### Issue: Agent can't connect to MCP server

**Symptoms**: Agent errors mention MCP connection failures or tools not available.

**Solutions**:

1. **Verify MCP server is running**:

   ```sh
   # Check if MCP server process is running
   curl http://localhost:9000/
   ```

2. **Check MCP server logs**:
   - Review the terminal where `dr run mcp_server:dev` is running
   - Look for connection or authentication errors

3. **Verify port configuration**:
   - Check that `MCP_SERVER_PORT` in `.env` matches the port the server is using
   - See [Ports reference](#ports-reference) for default ports

4. **Check environment variables**:
   - Ensure `DATAROBOT_API_TOKEN` is set correctly
   - Verify `DATAROBOT_ENDPOINT` is correct

## OAuth configuration issues

### Issue: OAuth authentication fails or redirects don't work

**Solutions**:

1. **Verify redirect URLs**:
   - Ensure all callback URLs are added to your OAuth application
   - Check that URLs match exactly (including trailing slashes)
   - See [OAuth applications documentation](docs/oauth-applications.md) for required URLs

2. **Check OAuth credentials**:
   - Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` (or Box equivalents) are set in `.env`
   - Ensure credentials are correct and not expired

3. **Verify OAuth scopes**:
   - Check that all required scopes are enabled in your OAuth application
   - See provider-specific sections for required scopes

4. **Check OAuth providers in DataRobot**:
   - Navigate to `<your_datarobot_url>/account/oauth-providers`
   - Verify providers are created and configured correctly

## Deployment issues

### Issue: `dr run deploy` fails

**Solutions**:

1. **Verify Pulumi is configured**:

   ```sh
   pulumi whoami
   ```

   - If not logged in, use `pulumi login --local` or create an account at [app.pulumi.com](https://app.pulumi.com/signup)

2. **Check prerequisites**:
   - Ensure all services tested locally before deploying
   - Verify `.env` file has all required variables

3. **Review Pulumi stack**:

   ```sh
   pulumi stack ls
   ```

   - Ensure you're using the correct stack
   - Check for stack configuration issues

4. **Check deployment logs**:
   - Review Pulumi output for specific error messages
   - Verify DataRobot API token has deployment permissions

## Frontend build issues

### Issue: Frontend build fails or displays errors

**Solutions**:

1. **Clear build cache**:

   ```sh
   cd frontend_web
   rm -rf node_modules dist
   npm install
   ```

2. **Check Node.js version**:

   ```sh
   node --version
   ```

   - Ensure Node.js >= 24 is installed (see [Prerequisite tools](#prerequisite-tools))

3. **Verify dependencies**:

   ```sh
   cd frontend_web
   npm install
   ```

## General debugging tips

1. **Check service status**:
   - Verify all required services are running in separate terminals
   - Check that services are listening on expected ports (see [Ports reference](#ports-reference))

2. **Review logs**:
   - Check terminal output for each running service
   - Look for error messages or stack traces

3. **Verify configuration**:
   - Review `.env` file for missing or incorrect values
   - Check that file paths and URLs are correct

4. **Test components individually**:
   - Try running services one at a time to isolate issues

5. **Update dependencies**:

   ```sh
   dr run install
   ```


# Get help

If you encounter issues or have questions, try the following:

- Check the [DataRobot documentation](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/index.html) for detailed guides.
- For DataRobot CLI (`dr`) commands and options: run `dr --help` or see the [DataRobot CLI documentation](https://github.com/datarobot-oss/cli). The [`dr start` command](https://github.com/datarobot-oss/cli/blob/main/docs/commands/start.md) describes the full quickstart flow, options (`--yes`), and behavior when not in a repository.
- [Contact DataRobot](https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html) for support.
- Open an issue on the [GitHub repository](https://github.com/datarobot-community/datarobot-agent-application).
