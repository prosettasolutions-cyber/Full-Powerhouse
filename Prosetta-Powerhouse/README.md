# Ritu Command Center

Ritu Command Center is a local-first, cinematic interface for a personal AI companion. It presents Ritu as the central cognitive orchestration layer coordinating projects, specialist agents, tasks, decisions, memory, activity, and system state.

## Folder structure

```text
ritu-command-center/
├── index.html
├── styles.css
├── app.js
├── data.js
├── README.md
└── assets/
    ├── icons/
    └── sounds/
```

## Run locally

For the first OCR-enabled run, double-click:

```text
setup-ocr.cmd
```

Automatic startup is installed for the current Windows user:

- **Ritu AI Backend** in the Windows Startup folder starts a hidden watchdog after sign-in.
- **Ritu Portal** on the desktop checks the API, starts it if needed, waits until healthy, and opens the portal.
- The watchdog checks Ritu every 20 seconds and automatically restarts the server after a failure.

You can also double-click `start-ritu.cmd`; it now performs the same automatic health check and opens `http://127.0.0.1:8080` without leaving a terminal window open. Server logs are stored in `P:\RituAI\Powerhouse\.ritu\logs`.

## Main features

- Animated, state-aware Ritu intelligence core and particle field
- Durable local eCEO core for projects, agents, tasks, memories, references, artifacts, and audit events
- eCEO Training Room for versioned intelligence modules, scoped memory, and reviewed lessons
- Separate conversation rooms with isolated histories for Command, Company, Training, Boardroom, Projects, and Agents
- Natural-language planning and bounded agent delegation through local Qwen/Ollama
- Agent hiring, waking, sleeping, and recoverable archiving
- Versioned project-file creation confined to `P:\RituAI\Powerhouse`
- Model QA plus machine-verifiable acceptance gates for generated Python work
- Command Center, Boardroom, Projects, Agents, Tasks, Memory, Activity, and System views
- Streaming local-Qwen responses and project-scoped conversation
- Browser speech recognition with live listening feedback
- Permission-based one-frame screen capture with local RapidOCR extraction
- Review-before-send OCR workflow connected to Qwen through Ollama
- Large project detail modal and correct project-to-Boardroom routing
- Task workflow with LocalStorage persistence
- Searchable durable memory, live audit activity, and verified local service status
- Responsive desktop, tablet, and mobile layouts
- Keyboard navigation, visible focus states, Escape-to-close, and reduced-motion support

## Browser requirements

Use a current version of Chrome, Edge, Firefox, or Safari. Fullscreen, LocalStorage, Canvas, and modern CSS are required for the intended experience.

## Voice input

Voice input uses the browser Web Speech API. Support is strongest in Chromium-based browsers and can depend on browser or operating-system speech services. The browser will request microphone permission. When speech recognition is unavailable, the app shows a graceful message and text commands remain fully usable.

## Local screen reading

The `OCR` button asks the browser for screen-sharing permission, captures one frame, and immediately stops sharing. The frame is sent only to the local `/api/ocr` endpoint served by `server.py`. RapidOCR extracts text locally with ONNX Runtime, then displays the screenshot and recognized text for review.

Choose **Ask Ritu about screen** to send only the reviewed OCR text to the selected local Ollama model. Choose **Use as context** to place the text in the composer without sending it. No screenshot is sent to Ollama or any cloud service.

## Ritu eCEO operating core

Ritu's durable company workspace is stored under:

```text
P:\RituAI\Powerhouse
├── .ritu\ritu_company.db
├── projects\
└── uploads\
```

The **Company** view shows live projects, active and sleeping agents, delegation tasks, reusable memories, generated artifacts, uploaded references, and the audit stream.

Commands entered in the portal are planned by local Qwen and executed through an allowlisted action layer. Ritu can create projects, hire or sleep agents, assign and run tasks, create versioned project files, capture memory, and report outcomes. Generated files cannot leave the Powerhouse workspace, unsupported file types are rejected, overwritten files receive recoverable history copies, and every action is recorded.

Agent-generated Python work is reviewed twice: first by the QA Agent and then by deterministic checks for required paths, text, Python symbols, syntax, and exact constant return contracts. Work that fails acceptance remains in review instead of being reported as complete.

Reference uploads use the **+** button beside the composer and stay inside the active local project. Text-based references are made available to assigned agents; screen text can be captured through RapidOCR and sent to Ritu after review.

Autonomous authority is deliberately bounded. Ritu does not run generated code, execute shell commands, manage credentials, publish externally, make purchases, or irreversibly delete user data. Those capabilities require an explicit future approval workflow.

## eCEO Training Room

Open **Training Room** in the portal to discuss what Ritu should learn, improve, or remember. Ritu first proposes the intelligence, memory, and guardrails. Chat-based training actions require explicit permission such as “approve” or “begin training”; the structured **Begin approved training** button also acts as explicit permission.

Training creates a versioned declarative Python intelligence module under:

```text
P:\RituAI\Powerhouse\projects\ritu-autonomous-company\intelligence
```

The session, module, scoped memories, and audit event are stored in the local company database. This is operational training for Ritu's orchestration layer; it does not fine-tune or change the Qwen model weights. Generated intelligence modules are stored for review and are not executed automatically.

## Conversation rooms

Each conversational area uses an isolated local history and a distinct backend session:

- **Command Center:** overall questions, cross-project direction, and new missions
- **CEO Company:** live project, program, agent, task, and blocker status
- **Training Room:** permission-gated discussion about Ritu's memory and intelligence
- **Boardroom:** consequential company, project, agent, and intelligence decisions
- **Project Room:** one project's requirements, tasks, agents, risks, files, and status
- **Agent Organization:** overall staffing, workload, performance, issues, and learning
- **Direct Agent Room:** one specialist's current work, blockers, validation, and reusable learning

Projects and Agents open dedicated rooms from their cards. Tasks is a Jira-style status board. Memory is searchable but has no chat. Activity provides text, project, and event filters. System remains an operational status view without chat.

## Local Ollama connection

Ritu connects directly to Ollama at `http://127.0.0.1:11434`. Start Ollama before opening the app:

```bash
ollama serve
```

Model selection is automatic and room-specific:

- `qwen2.5:14b` is reserved for the Training Room and Boardroom.
- `qwen2.5:7b` handles Command Center, CEO Company, Project Rooms, Agent Rooms, and other fast-response work.
- Task execution and QA also use the fast model unless a future workflow explicitly promotes a decision to the Boardroom.

The model selector is read-only and shows the route for the current room. The backend is authoritative, so browser changes cannot silently override the policy.

## Live backend state

Projects, agents, tasks, memories, artifacts, references, and activity are read from the local SQLite company database through `GET /api/portal/state`. The browser polls the revision every two seconds and only redraws when the database changes. Browser storage keeps presentation preferences and separate room chat transcripts; it is not an operational source of truth.

Ritu's planner can create and update projects, agents, and tasks. Every accepted mutation is written through the store, recorded in the audit event stream, read back from SQLite, and returned with `verified: true`. Boardroom actions still require explicit approval. Jira board movements use `POST /api/portal/task`, and delegated execution uses `POST /api/company/run-task`.

The System view displays only known local service state and model routing; simulated CPU, RAM, GPU, and network figures were removed.

## Internal API

- `GET /api/health` — backend, Ollama models, routing, and record counts
- `GET /api/portal/state` — normalized authoritative portal state
- `GET /api/portal/files?scope=project|portal` — verified file inventory for a project or the portal source
- `GET /api/portal/file?scope=...&project=...&path=...` — read one permitted text file from disk
- `POST /api/portal/file` — atomically create or update a file, back up the previous version, audit it, and verify its hash
- `POST /api/ritu/chat` — room-scoped Ritu conversation and verified actions
- `POST /api/portal/task` — verified Jira task status update
- `POST /api/company/run-task` — real agent execution against the Powerhouse workspace
- `GET /api/training/status` and `POST /api/training/session` — permission-gated eCEO training
- `POST /api/ocr` — local RapidOCR screen-text extraction

Keep the service bound to localhost unless authentication and transport security are added.

Ritu receives the selected project's live file inventory and permitted text contents as working context. The portal source inventory is available for UI or website discussions. Small source changes can use exact `patch_file` actions, while complete files can use `write_file`. Ritu may change portal source only through an explicitly approved Boardroom action. The file API never exposes `.env` files, Git internals, history, backups, caches, binaries, or paths outside the two protected roots.
