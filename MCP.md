### Limitations of Local Models for MCP

| Issue | Mitigation |
|---|---|
| Malformed JSON output | Use constrained decoding (GBNF grammars, Outlines, vLLM guided decoding) |
| Context window too small | Use models with 32k+ context; limit exposed tools per session |
| Wrong tool selection | Curate tools per task; use clear descriptions in schema |
| Wrong arguments extracted | Strict schema validation; detailed parameter descriptions |
| Multi-step planning degradation | Keep workflows short; build deterministic orchestration |
| Slow inference | Use 7B model on GPU (RTX 4070+) for responsive performance |

### Gemma-Specific Notes
- Use **Gemma 3 Instruct** (latest) — better tool handling than Gemma 1/2.
- Consider community Gemma tool-calling fine-tunes on Hugging Face.
- Write a custom system prompt teaching the JSON tool-call format explicitly.
- Use grammar-constrained decoding to enforce valid tool-call JSON.

### Why Use Local LLM + MCP?

- **Privacy / data residency** — sensitive data never leaves your machine or VPC.
- **Offline operation** — works on air-gapped or low-connectivity environments.
- **Cost** — no per-token API charges.
- **Customization** — fine-tune the model for your tools and domain.
- **Compliance** — easier to satisfy GDPR, HIPAA, regulated-industry rules.

### Quick Start Guide
1. Install **Ollama** → pull `llama3.1:8b`
2. Install **Goose** or **Continue.dev**
3. Configure filesystem + web search MCP servers
4. Point the host at your Ollama endpoint
5. Once working, swap in `gemma3:9b` to compare reliability

---

## 9. MCP Server Code Walkthrough (Screenshot)

### Context
The screenshot showed `example_mcp_server.py` open in VS Code — a single-file
teaching demo that covers all major MCP building blocks.

**Tagline:** *"Cross-platform MCP server — teaching example."*

### The Nine Building Blocks

#### 1. Tools — plain functions exposed to the model (math, utils)
The simplest MCP primitive. Python functions (e.g., `add(a, b)`, `slugify(text)`)
that the LLM can call. The MCP framework auto-generates JSON schema from the function
signature. This is the most commonly used pattern in real MCP servers.

#### 2. File CRUD — read / write / edit / list / delete (sandboxed)
Filesystem operations: Create, Read, Update, Delete, and List.
The word **sandboxed** means access is restricted to a specific directory — the LLM
cannot read `/etc/passwd` or write to `~/.ssh`. Demonstrates safe tool design: every
powerful capability should be scoped.

#### 3. Resources — read-only data the model can fetch by URI
Resources are a different MCP primitive from tools. While tools are *actions*, resources
are *data* the host can attach to context. Addressed by URIs (e.g., `file:///notes/today.md`).
Think of them as attachments the model can pull in.

#### 4. HTTP fetch — reaching the outside world from a tool
A tool that makes outbound HTTP requests (using the `requests` library). Shows how an
MCP server bridges the LLM to external web APIs without the LLM opening network sockets.

#### 5. SQLite CRUD — a stateful tool (tiny notes DB)
Unlike pure functions, this maintains **state across invocations** by reading/writing
a small SQLite database. Teaches how MCP servers can hold persistent data — useful for
memory, task lists, or record-keeping.

#### 6. Shell runner — a "dangerous" tool guarded by an allowlist
Executes shell commands. Flagged as *dangerous* — running arbitrary shell from an LLM
is a major security risk. Mitigated by an **allowlist** — only pre-approved commands
(e.g., `ls`, `pwd`, `git status`) are permitted. Key enterprise pattern: constrain
the surface area of sharp tools aggressively.

#### 7. GUI automation — cross-platform via pyautogui (works on mac/win/linux)
*(This line was highlighted/selected in the screenshot.)*
Uses **PyAutoGUI** to control mouse and keyboard at the OS level — clicking, typing,
taking screenshots. Works on macOS, Windows, and Linux. Makes the MCP server capable
of full **desktop automation** — driving any app on the user's machine, not just APIs.

#### 8. Image tool — returns a real PNG thumbnail
Demonstrates that MCP tools can return **binary content** (images), not just text or
JSON. Produces an actual PNG (using Pillow) returned as base64-encoded image content
that the host/LLM can display. Teaches multi-modal tool returns.

#### 9. Prompts — reusable prompt templates
"Prompts" are a third MCP primitive (alongside tools and resources). Named,
parameterized prompt templates (e.g., "summarize this document" with a `style`
argument) that the host offers to the user. The server fills in arguments and returns
the final prompt string. Packages reusable LLM workflows.

### Three MCP Primitives Summary

| Primitive | Type | Description |
|---|---|---|
| **Tools** | Action | Functions the LLM calls to do things |
| **Resources** | Data | Read-only content the host attaches by URI |
| **Prompts** | Templates | Named, parameterized prompt templates |

### Run Instructions

```bash
# stdio (how an MCP client launches it)
python example_mcp_server.py

# dev inspector — web UI to test tools manually (like Postman for MCP)
mcp dev example_mcp_server.py
```

### Install

```bash
pip install "mcp[cli]" pillow requests pyautogui
```

| Package | Purpose |
|---|---|
| `mcp[cli]` | Official Anthropic MCP Python SDK + CLI tools |
| `pillow` | Image handling for the PNG thumbnail tool (#8) |
| `requests` | HTTP requests for the web-fetch tool (#4) |
| `pyautogui` | GUI automation for the desktop control tool (#7) |

### Why This File Is Valuable

It is a **single-file curriculum** for MCP — all three primitives, safe vs. dangerous
tool patterns, state management, networking, multi-modal returns, and reusable prompt
templates in one annotated, runnable file. Ideal for learning the full MCP surface
area before building a production server.

---

*Document compiled from a live Q&A session on LLM concepts.*
*Date: April 25, 2026*