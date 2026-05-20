Architecture pattern
	•	Event-driven, agentic system with classification/routing into specialised agents
	•	Comment thread in Todoist = primary user interface (no separate UI needed)
	•	HITL gate before any write that changes task content, dates, or priority
	•	Async processing — webhook acks fast, real work happens behind a queue
End-to-end flow
Todoist webhook → Ingress API → Event queue → Worker → Orchestrator → Agent(s) → Validator → Action (Todoist write / comment / notification) → State + Audit
Application components
	•	Ingress API — receives Todoist webhook, verifies signature, dedupes by event ID, enqueues, returns 200 fast
	•	Event queue — decouples ingress from processing, enables retries and back-pressure
	•	Idempotency cache — short-TTL store keyed on event ID to prevent double-processing
	•	Worker pool — pulls events, hydrates context, invokes orchestrator
	•	Orchestrator — stateful graph executor that routes events through agents, supports interrupts for HITL and resumes
	•	State store — relational DB for tasks mirror, task state machine, AI questions, agent runs, audit, user prefs
	•	Vector store — embeddings for duplicate detection and semantic recall of past tasks/decisions
	•	Secrets manager — Todoist tokens per user, LLM keys
	•	Scheduler — cron-style trigger for daily review, stale scans, follow-up nudges
	•	Notification service — channel-agnostic dispatcher (push, email, in-task comment) with rate limiting and quiet-hours
	•	Observability stack — LLM tracing (prompts, tools, latency, cost), metrics, structured logs, eval harness
	•	Admin/replay tool — inspect agent runs, replay events, override AI decisions
Agents



|Agent                |Responsibility                                                 |Triggered when                         |
|---------------------|---------------------------------------------------------------|---------------------------------------|
|**Router**           |Classifies the event + user intent, picks the downstream path  |Every event                            |
|**Classifier**       |Assigns type, priority, effort, urgency, importance, vagueness |New / updated task                     |
|**Planner**          |Subtasks, next action, due-date suggestion, clarifying question|Vague, large, or unclear task          |
|**Solver**           |Drafts emails, messages, docs, plans inside the task           |Comment intent = “draft / write / plan”|
|**Conversationalist**|Reads comments → infers intent → routes → composes reply       |New comment from user                  |
|**Validator**        |Approves / suggests / rejects every proposed write             |Before any Todoist mutation            |
|**Notifier**         |Decides if, when, and how to nudge the user                    |State changes + scheduled scans        |

Skills (reusable LLM capabilities)
Stateless prompt + schema units that agents compose. Each one isolated and individually testable:
	•	detect_vagueness → {is_vague, missing_info[]}
	•	classify_task_type → admin / deep work / follow-up / errand / comms / research / planning
	•	infer_priority / estimate_effort / estimate_urgency / estimate_importance
	•	rewrite_title — clearer title + diff
	•	decompose_into_subtasks — only above effort threshold
	•	suggest_next_action
	•	generate_clarifying_question — single question, deduped against past asks
	•	parse_comment_intent → {intent, slots, confidence} covering all §6 commands
	•	draft_artifact — email / message / doc body
	•	summarise_task_context
	•	detect_duplicate — vector kNN + LLM judge
	•	judge_action_safety — LLM-as-judge for the Validator
Tools (side-effecting integrations)
	•	TodoistTool — read task, update fields, add comment, set due, set priority, move section, add label, add subtask. No delete. No close unless user explicitly said so.
	•	LLMTool — chat/completions with structured output, behind a gateway for routing and cost control
	•	VectorTool — upsert and query embeddings
	•	StateTool — read/write task state, AI questions, run records
	•	AuditTool — append-only log: what was suggested, what was changed, why, by which agent, at what confidence
	•	NotifyTool — channel-aware send respecting quiet hours and frequency caps
	•	TimeTool — user timezone, “tomorrow / later / next week” resolution, business hours
Per-task state machine
new → classified → {clear | awaiting_clarification} → planned → {active | blocked | waiting | stale} → completed
Tracked alongside each task:
	•	ai_pending_question_id
	•	last_ai_run_at
	•	last_user_action_at
	•	follow_up_due_at
	•	consecutive_unanswered_nudges
Data model (minimum tables)
	•	tasks — mirror of Todoist + AI-derived fields (type, effort, importance, vagueness)
	•	task_history — slowly-changing history for “how did this task evolve” (req §1)
	•	ai_questions — open questions, asked_at, answered_at, answer_text → prevents repeat asks
	•	agent_runs — every orchestrator run: inputs, outputs, confidence, latency, cost, tools used
	•	audit_log — every suggestion + action with reason and confidence
	•	user_prefs — quiet hours, auto-vs-approve mode, planning style, project mapping
	•	embeddings — vector rows for duplicate / semantic recall
Validator — the safety spine
Every mutation routes through it. It applies:
	•	Hard rules — no delete, no auto-complete, no priority jump >1 level without explicit user words, no due-date changes >30 days without confirmation
	•	Confidence gate — below threshold → downgrade from “apply” to “suggest in comment”
	•	Action dedupe — reject if same action ran in last N minutes (req §10, §15)
	•	Question dedupe — block re-asking a question already open in ai_questions
	•	LLM safety judge — for ambiguous cases
	•	Returns {approve | suggest | reject, reason, confidence} — Notifier surfaces “suggest” outcomes back to the user
Scheduled jobs
	•	Hourly — scan overdue tasks, fire follow-up nudges for unanswered AI questions (with backoff)
	•	Daily, user-local morning — generate daily review: top focus, overdue, blocked, unclear, open AI questions
	•	Nightly — stale-task detection, learning pass (which suggestions were accepted vs ignored → adjust thresholds), embedding refresh
Learning loop (req §11)
	•	Capture every suggestion’s outcome (accepted, ignored, overridden) on audit_log
	•	Nightly job aggregates per-user acceptance rates by skill and task type
	•	Adjusts confidence thresholds and prompt examples in user-scoped prompt config
	•	Feed completed-task patterns into vector store for retrieval as few-shot context
Suggested tech stack (greenfield)
	•	Runtime — Python (FastAPI for ingress, async workers)
	•	Cloud — your call; AWS / GCP / Azure all fine. Below assumes managed services
	•	Queue — managed pub/sub or SQS/SNS
	•	DB — Postgres (managed) with pgvector for embeddings — one DB, simpler ops
	•	Cache — Redis (idempotency, rate limits, short-term locks)
	•	Orchestration — LangGraph or Burr for the stateful agent graph (checkpointing + interrupts matter here)
	•	LLM gateway — LiteLLM or Portkey for routing, retries, cost tracking
	•	Observability — Langfuse for LLM traces + evals, OpenTelemetry → Grafana/Datadog for infra
	•	Hosting — containerised on Cloud Run / Fargate / equivalent; one ingress service, one worker service, one scheduler
MVP cut (delivers §16)
Ship in this order:
	1.	Ingress + queue + idempotency
	2.	Tasks mirror table + webhook → DB sync
	3.	Classifier agent (priority, project, section, type, vagueness)
	4.	Conversationalist + parse_comment_intent covering: plan, next step, due, priority, block, remind
	5.	Validator with hard rules + confidence gate
	6.	ai_questions table + single-question rule
	7.	Daily review job
	8.	audit_log from day one
Defer: Solver drafting, duplicate detection, learning loop, multi-channel notifications, subtask decomposition.
Want me to go deeper on any piece — the orchestrator graph shape, the Validator rules, the comment-intent grammar, or the data model DDL?​​​​​​​​​​​​​​​​