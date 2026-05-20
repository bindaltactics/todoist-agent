# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **pre-implementation** repository for an AI-powered task management layer on top of Todoist. The primary user interface is Todoist's own comment threads — no separate UI is needed. The system receives Todoist webhooks, processes them through a pipeline of specialised agents, and writes back to Todoist (comments, field updates) while keeping the user in control via a human-in-the-loop (HITL) gate.

## Planned Tech Stack

- **Runtime**: Python (FastAPI for ingress, async workers)
- **Queue**: Managed pub/sub or SQS/SNS
- **DB**: Postgres with pgvector (single DB for both relational data and embeddings)
- **Cache**: Redis (idempotency, rate limits, short-term locks)
- **Orchestration**: LangGraph or Burr (stateful agent graph with checkpointing + interrupts)
- **LLM gateway**: LiteLLM or Portkey (routing, retries, cost tracking)
- **Observability**: Langfuse (LLM traces + evals), OpenTelemetry → Grafana/Datadog
- **Hosting**: Containerised on Cloud Run / Fargate; one ingress service, one worker service, one scheduler

## End-to-End Flow

```
Todoist webhook → Ingress API → Event queue → Worker → Orchestrator → Agent(s) → Validator → Action (Todoist write / comment) → State + Audit
```

## Architecture Principles

- **Event-driven and async**: Webhook acks immediately (200 fast); all real work happens behind a queue.
- **HITL gate**: Every proposed write that changes task content, dates, or priority must pass through the Validator before being applied. Low-confidence actions are downgraded to suggestions posted as comments rather than direct mutations.
- **No deletes, no auto-complete**: The system never deletes tasks and never completes tasks unless the user explicitly says so.
- **Idempotency everywhere**: Short-TTL idempotency cache keyed on event ID prevents double-processing; action dedupe prevents the same mutation running twice within N minutes.
- **Single open question rule**: `ai_questions` table enforces one unanswered question per task at a time — the system will not re-ask a question already open.

## Agents

| Agent | Responsibility | Triggered when |
|---|---|---|
| **Router** | Classifies event + user intent, picks downstream path | Every event |
| **Classifier** | Assigns type, priority, effort, urgency, importance, vagueness | New/updated task |
| **Planner** | Subtasks, next action, due-date suggestion, clarifying question | Vague, large, or unclear task |
| **Solver** | Drafts emails, messages, docs, plans inside the task | Comment intent = "draft / write / plan" |
| **Conversationalist** | Reads comments → infers intent → routes → composes reply | New comment from user |
| **Validator** | Approves / suggests / rejects every proposed write | Before any Todoist mutation |
| **Notifier** | Decides if, when, and how to nudge the user | State changes + scheduled scans |

## Skills (Stateless LLM Units)

Skills are stateless prompt + schema units that agents compose. Each is isolated and individually testable:

`detect_vagueness`, `classify_task_type`, `infer_priority`, `estimate_effort`, `estimate_urgency`, `estimate_importance`, `rewrite_title`, `decompose_into_subtasks`, `suggest_next_action`, `generate_clarifying_question`, `parse_comment_intent`, `draft_artifact`, `summarise_task_context`, `detect_duplicate`, `judge_action_safety`

## Tools (Side-Effecting Integrations)

- **TodoistTool**: read task, update fields, add comment, set due, set priority, move section, add label, add subtask. No delete. No close unless user explicitly requested.
- **LLMTool**: chat/completions with structured output, behind a gateway for routing and cost control
- **VectorTool**: upsert and query embeddings
- **StateTool**: read/write task state, AI questions, run records
- **AuditTool**: append-only log — what was suggested, what was changed, why, by which agent, at what confidence
- **NotifyTool**: channel-aware send respecting quiet hours and frequency caps
- **TimeTool**: user timezone, natural language date resolution ("tomorrow / later / next week"), business hours

## Per-Task State Machine

```
new → classified → {clear | awaiting_clarification} → planned → {active | blocked | waiting | stale} → completed
```

Fields tracked per task: `ai_pending_question_id`, `last_ai_run_at`, `last_user_action_at`, `follow_up_due_at`, `consecutive_unanswered_nudges`

## Data Model (Minimum Tables)

- `tasks` — Todoist mirror + AI-derived fields (type, effort, importance, vagueness)
- `task_history` — slowly-changing history for task evolution
- `ai_questions` — open questions: `asked_at`, `answered_at`, `answer_text` (prevents repeat asks)
- `agent_runs` — every orchestrator run: inputs, outputs, confidence, latency, cost, tools used
- `audit_log` — every suggestion + action with reason and confidence (append-only)
- `user_prefs` — quiet hours, auto-vs-approve mode, planning style, project mapping
- `embeddings` — vector rows for duplicate detection and semantic recall

## Validator Rules

The Validator is the safety spine. It applies in order:
1. **Hard rules**: no delete, no auto-complete, no priority jump >1 level without explicit user words, no due-date change >30 days without confirmation
2. **Confidence gate**: below threshold → downgrade from "apply" to "suggest in comment"
3. **Action dedupe**: reject if same action ran in last N minutes
4. **Question dedupe**: block re-asking a question already open in `ai_questions`
5. **LLM safety judge**: for ambiguous cases

Returns `{approve | suggest | reject, reason, confidence}`. "Suggest" outcomes surface back to the user as task comments.

## Scheduled Jobs

- **Hourly**: scan overdue tasks, follow-up nudges for unanswered AI questions (with backoff)
- **Daily (user-local morning)**: daily review — top focus, overdue, blocked, unclear, open AI questions
- **Nightly**: stale-task detection, learning pass (acceptance rates → adjust confidence thresholds), embedding refresh

## MVP Build Order

Ship in this order (from `design.md`):
1. Ingress + queue + idempotency
2. Tasks mirror table + webhook → DB sync
3. Classifier agent (priority, project, section, type, vagueness)
4. Conversationalist + `parse_comment_intent` covering: plan, next step, due, priority, block, remind
5. Validator with hard rules + confidence gate
6. `ai_questions` table + single-question rule
7. Daily review job
8. `audit_log` from day one

**Defer to post-MVP**: Solver drafting, duplicate detection, learning loop, multi-channel notifications, subtask decomposition.
