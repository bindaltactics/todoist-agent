-- Extensions
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pgmq";

-- tasks: Todoist mirror + AI-derived fields
CREATE TABLE tasks (
    id                          TEXT PRIMARY KEY,           -- Todoist task ID
    user_id                     TEXT        NOT NULL,
    project_id                  TEXT,
    section_id                  TEXT,
    parent_id                   TEXT,
    title                       TEXT        NOT NULL,
    description                 TEXT,
    priority                    INTEGER     DEFAULT 1 CHECK (priority BETWEEN 1 AND 4),
    due_date                    TIMESTAMPTZ,
    labels                      TEXT[]      DEFAULT '{}',
    status                      TEXT        NOT NULL DEFAULT 'new',
    -- AI-derived
    ai_task_type                TEXT,       -- admin | deep_work | follow_up | errand | comms | research | planning
    ai_effort                   TEXT,       -- low | medium | high
    ai_urgency                  INTEGER,    -- 1–5
    ai_importance               INTEGER,    -- 1–5
    ai_is_vague                 BOOLEAN     DEFAULT FALSE,
    -- State tracking (per-task state machine)
    ai_pending_question_id      UUID,
    last_ai_run_at              TIMESTAMPTZ,
    last_user_action_at         TIMESTAMPTZ,
    follow_up_due_at            TIMESTAMPTZ,
    consecutive_unanswered_nudges INTEGER   DEFAULT 0,
    -- Timestamps
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    todoist_created_at          TIMESTAMPTZ,
    todoist_updated_at          TIMESTAMPTZ
);

-- task_history: append-only record of field changes
CREATE TABLE task_history (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id     TEXT        NOT NULL REFERENCES tasks(id),
    changed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    changed_by  TEXT        NOT NULL DEFAULT 'system',  -- system | user | ai
    field_name  TEXT        NOT NULL,
    old_value   JSONB,
    new_value   JSONB
);

-- ai_questions: one open question per task at a time (enforced by application logic)
CREATE TABLE ai_questions (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         TEXT        NOT NULL REFERENCES tasks(id),
    question_text   TEXT        NOT NULL,
    asked_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    answered_at     TIMESTAMPTZ,
    answer_text     TEXT,
    agent_run_id    UUID
);

-- agent_runs: full record of every orchestrator invocation
CREATE TABLE agent_runs (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id     TEXT,
    event_id    TEXT,
    agent_name  TEXT        NOT NULL,
    inputs      JSONB       NOT NULL DEFAULT '{}',
    outputs     JSONB,
    confidence  NUMERIC(4,3),
    latency_ms  INTEGER,
    cost_usd    NUMERIC(10,6),
    tools_used  TEXT[]      DEFAULT '{}',
    status      TEXT        NOT NULL DEFAULT 'running',  -- running | completed | failed
    error       TEXT,
    started_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- audit_log: append-only; outcome filled in later by the learning loop
CREATE TABLE audit_log (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         TEXT,
    agent_run_id    UUID,
    action_type     TEXT        NOT NULL,   -- suggest | apply | reject
    action_detail   JSONB       NOT NULL DEFAULT '{}',
    reason          TEXT,
    confidence      NUMERIC(4,3),
    outcome         TEXT,                   -- accepted | ignored | overridden
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- user_prefs: per-user settings; auto_apply=false means every write needs approval
CREATE TABLE user_prefs (
    user_id             TEXT    PRIMARY KEY,
    quiet_hours_start   TIME,
    quiet_hours_end     TIME,
    timezone            TEXT    NOT NULL DEFAULT 'UTC',
    auto_apply          BOOLEAN NOT NULL DEFAULT FALSE,
    planning_style      TEXT    DEFAULT 'balanced',
    project_mapping     JSONB   DEFAULT '{}',
    reminder_lead_hours INTEGER DEFAULT 24,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- embeddings: pgvector rows for duplicate detection and semantic recall
CREATE TABLE embeddings (
    id              UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         TEXT    NOT NULL REFERENCES tasks(id),
    content_type    TEXT    NOT NULL,   -- title | description | context
    content         TEXT    NOT NULL,
    embedding       vector(1536),       -- text-embedding-3-small / ada-002 dimension
    model           TEXT    NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX ON tasks (user_id);
CREATE INDEX ON tasks (status);
CREATE INDEX ON tasks (follow_up_due_at) WHERE follow_up_due_at IS NOT NULL;
CREATE INDEX ON task_history (task_id, changed_at);
CREATE INDEX ON ai_questions (task_id) WHERE answered_at IS NULL;
CREATE INDEX ON agent_runs (task_id, started_at);
CREATE INDEX ON audit_log (task_id, created_at);
CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create pgmq queue for inbound webhook events
SELECT pgmq.create('webhook_events');
