#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import re
import sys

from telemetry_common import append_event, load_session_state, update_session_state, update_turn_state, utc_now
from telemetry_turns import classify_turn_kind_from_prompt


EMPTY = {
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": "",
    }
}

CONFIRMATION_PHRASE = "confirmed: proceed"
CONTEXT_ENGINEERING_SKILL = "context-engineering"
DEFAULT_SHARED_PICTURE_PHASE = "research"


DOMAIN_MAP = [
    (
        "analysis",
        [
            r"\b(setup|config|routing|router|hooks|agents\.md|skills|plugins|automation|orchestration)\b",
            r"\b(audit|evaluate|review my setup|improve my codex|make it better|blueprint|spec|round up|re-?evaluate|double check|what'?s left)\b",
        ],
        ["reviewer"],
        [],
    ),
    (
        "security",
        [r"\b(security|auth|oauth|jwt|xss|csrf|inject|secret|permission|vulnerability)\b"],
        ["security_reviewer", "reviewer"],
        [],
    ),
    (
        "debug",
        [r"\b(debug|bug|broken|error|traceback|panic|crash|failing|regression)\b"],
        ["debugger", "test_worker"],
        [],
    ),
    (
        "architecture",
        [r"\b(architecture|redesign|migration|rewrite|system design|multi-service|platform|interface designs?|module interface|api design|design it twice)\b"],
        ["architect_reviewer", "reviewer"],
        ["improve-codebase-architecture", "domain-model"],
    ),
    (
        "frontend",
        [
            r"\b(react|next\.?js|frontend|ui|ux|tailwind|css|tsx|jsx|component|figma|dashboard|landing page|landing|hero|logo|branding|browser|responsive|mobile|playwright)\b",
        ],
        ["reviewer", "test_worker"],
        ["tdd"],
    ),
    (
        "backend",
        [
            r"\b(api|backend|fastapi|nestjs|express|database|sql|prisma|orm|service|clerk|stripe|railway|websocket|billing|subscription|runpod|worker)\b",
        ],
        ["reviewer", "test_worker"],
        ["tdd"],
    ),
    (
        "testing",
        [r"\b(test|pytest|vitest|jest|coverage|integration test|e2e|uat|playwright)\b"],
        ["test_worker"],
        ["tdd"],
    ),
    (
        "git",
        [r"\b(git|github|branch|commit|rebase|push|pull request|pr review|merge)\b"],
        ["git_worker", "reviewer"],
        ["github-triage"],
    ),
    (
        "performance",
        [r"\b(perf|performance|slow|latency|throughput|memory leak|bundle size|n\+1)\b"],
        ["performance_reviewer", "reviewer"],
        [],
    ),
    (
        "openai-docs",
        [r"\b(openai|codex|mcp|responses api|agents sdk|chatgpt apps|gpt-5)\b"],
        ["reviewer"],
        ["openai-docs"],
    ),
]


PROMPT_SKILL_MAP = [
    ("tdd", [r"\b(tdd|test[- ]first|red[- ]green[- ]refactor|write tests first)\b"]),
    ("domain-model", [r"\b(domain model|stress[- ]test.*plan|challenge.*plan against.*domain)\b"]),
    ("ubiquitous-language", [r"\b(ubiquitous language|domain glossary|glossary|domain terms|ddd language)\b"]),
    ("improve-codebase-architecture", [r"\b(deepen|deep module|shallow module|god class|architecture improvement|improve.*architecture)\b"]),
    ("design-an-interface", [r"\b(design an interface|design it twice|interface design|api design|compare.*interfaces?)\b"]),
    ("grill-me", [r"\b(grill me|interview me|stress test this|challenge my plan)\b"]),
    ("request-refactor-plan", [r"\b(refactor plan|refactoring rfc|plan a refactor|tiny commits)\b"]),
    ("to-issues", [r"\b(to issues|break.*into.*issues|implementation tickets|vertical slice[s]?|tracer bullet issues)\b"]),
    ("to-prd", [r"\b(to prd|create a prd|write a prd|product requirements|prd)\b"]),
    ("github-triage", [r"\b(github triage|triage github|ready-for-agent|needs-triage|issue labels)\b"]),
    ("triage-issue", [r"\b(triage.*bug|triage.*issue|root cause.*issue|investigate.*bug)\b"]),
    ("qa", [r"\b(qa session|do qa|report bugs|file bugs|bug bash)\b"]),
    ("setup-pre-commit", [r"\b(pre-commit|precommit|husky|lint-staged)\b"]),
    ("git-guardrails-claude-code", [r"\b(claude.*guardrails|dangerous git|block git push|block git reset)\b"]),
    ("migrate-to-shoehorn", [r"\b(shoehorn|frompartial|fromany|replace.*\\bas\\b.*tests?)\b"]),
    ("scaffold-exercises", [r"\b(scaffold exercises?|course section|exercise stubs?)\b"]),
    ("obsidian-vault", [r"\b(obsidian|vault notes?|wikilinks?|index notes?)\b"]),
    ("write-a-skill", [r"\b(write a skill|create a skill|new skill|skill structure)\b"]),
    ("edit-article", [r"\b(edit article|improve article|rewrite article|tighten prose)\b"]),
    ("caveman", [r"\b(caveman|less tokens|be brief|ultra[- ]compressed)\b"]),
    ("zoom-out", [r"\b(zoom out|higher level|big picture|step back)\b"]),
]


FOLLOW_UP_PATTERNS = [
    r"^(yes|yeah|yep|ok|okay|sure|fine|great|cool|please|thanks|thank you)$",
    r"^(yes please|yes please continue|okay continue|okay please continue|ok please continue)$",
    r"^(go ahead|do it|ship it|deploy it|continue|please continue|keep going|carry on|proceed)$",
    r"^(let'?s continue|lets continue|next|what'?s next|what is next)$",
]


FOLLOW_UP_PREFIXES = ("yes ", "yeah ", "yep ", "ok ", "okay ", "sure ", "fine ", "great ", "cool ", "and ", "also ", "now ")

WORK_ACTION_RE = re.compile(
    r"\b("
    r"implement|build|create|add|update|change|edit|modify|fix|patch|wire up|set up|configure|install|"
    r"remove|delete|refactor|migrate|deploy|run|test|verify|inspect|look at|take a look|audit|review|"
    r"debug|investigate|research|enforce|apply|ship|improve"
    r")\b"
)

DIRECT_KNOWLEDGE_RE = re.compile(
    r"^(what|why|how|when|where|who|explain|summarize|tell me|what does|what is|can you explain)\b"
)


def extract_prompt(payload):
    for key in ("prompt", "text", "input", "userMessage", "message"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    messages = payload.get("messages")
    if isinstance(messages, list):
        parts = []
        for item in messages:
            if isinstance(item, dict):
                content = item.get("content")
                if isinstance(content, str):
                    parts.append(content)
                elif isinstance(content, list):
                    for piece in content:
                        if isinstance(piece, dict):
                            text = piece.get("text")
                            if isinstance(text, str):
                                parts.append(text)
        if parts:
            return "\n".join(parts).strip()

    return ""


def unique_items(items):
    seen = set()
    ordered = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def normalize_prompt(prompt):
    return re.sub(r"\s+", " ", (prompt or "").strip().lower())


def is_confirmation_prompt(prompt):
    return normalize_prompt(prompt) == CONFIRMATION_PHRASE


def is_direct_knowledge_prompt(prompt):
    text = normalize_prompt(prompt)
    if not text:
        return False
    return bool(DIRECT_KNOWLEDGE_RE.search(text)) and not WORK_ACTION_RE.search(text)


def detect_project(cwd, prompt):
    joined = f"{cwd} {prompt}".lower()
    if "project-alpha" in joined:
        return "project-specific workspace"
    if "project-beta" in joined:
        return "project-specific workspace"
    if "project-gamma" in joined:
        return "project-specific workspace"
    if ".codex" in cwd:
        return "Codex-Home"
    return "General"


def is_follow_up_prompt(prompt):
    text = normalize_prompt(prompt)
    if not text:
        return False
    if any(re.fullmatch(pattern, text) for pattern in FOLLOW_UP_PATTERNS):
        return True
    if len(text.split()) <= 12 and re.search(r"\b(continue|proceed|go ahead|do it|keep going|ship it|deploy it|next)\b", text):
        return True
    return len(text.split()) <= 18 and text.startswith(FOLLOW_UP_PREFIXES)


def classify_complexity(prompt, session_state=None):
    text = normalize_prompt(prompt)
    words = text.split()
    prior_complexity = session_state.get("complexity") if isinstance(session_state, dict) else None
    prior_bash_calls = session_state.get("last_bash_tool_calls") if isinstance(session_state, dict) else None
    phase = session_state.get("phase") if isinstance(session_state, dict) else None
    phase_bash_calls = session_state.get("phase_bash_tool_calls") if isinstance(session_state, dict) else None
    phase_turns = session_state.get("phase_turns") if isinstance(session_state, dict) else None

    if len(words) <= 12 and re.search(r"\b(typo|rename|format|one line|quick fix|small fix)\b", text):
        return 0

    if is_follow_up_prompt(prompt) and isinstance(prior_complexity, int):
        follow_up_floor = 2 if re.search(r"\b(continue|proceed|go ahead|do it|keep going|ship it|deploy it|next)\b", text) else 1
        if isinstance(prior_bash_calls, int) and prior_bash_calls >= 6:
            follow_up_floor = max(follow_up_floor, 2)
        if phase in {"implementation", "deploy"}:
            follow_up_floor = max(follow_up_floor, 2)
        if (isinstance(phase_bash_calls, int) and phase_bash_calls >= 20) or (isinstance(phase_turns, int) and phase_turns >= 3):
            follow_up_floor = max(follow_up_floor, 2)
        return max(follow_up_floor, prior_complexity)

    if re.search(r"\b(plan first|architecture|migration|rewrite|orchestration|framework|platform|system design|end-to-end|from start to finish|without prompting)\b", text):
        return 3
    if "uat" in text and re.search(r"\b(full|browser|playwright|screen record|actual model|real real)\b", text):
        return 3

    if re.search(r"\b(build|implement|create|wire up|set up|refactor|improve|automation|deploy|fix|ship|continue|proceed|playwright|uat|blueprint|spec|re-?evaluate|double check)\b", text):
        return 2
    if len(words) > 80:
        return 2
    return 1


def choose_domain(prompt):
    text = prompt.lower()
    best = ("general", [], [], 0)
    best_score = 0
    for domain, patterns, agents, skills in DOMAIN_MAP:
        score = 0
        for pattern in patterns:
            score += len(re.findall(pattern, text))
        if score > best_score:
            best_score = score
            best = (domain, agents, skills, score)
    return best


def choose_prompt_skills(prompt):
    text = prompt.lower()
    matches = []
    for skill, patterns in PROMPT_SKILL_MAP:
        if any(re.search(pattern, text) for pattern in patterns):
            matches.append(skill)
    return matches


def classify_turn_kind(prompt, domain, domain_score, session_state=None):
    if isinstance(session_state, dict) and is_follow_up_prompt(prompt) and domain_score <= 1:
        prior_phase = session_state.get("phase") or session_state.get("turn_kind")
        if isinstance(prior_phase, str) and prior_phase:
            return prior_phase
    return classify_turn_kind_from_prompt(prompt, domain=domain, session_state=session_state)


def is_work_action_prompt(prompt, turn_kind=None, domain=None, complexity=None):
    if is_confirmation_prompt(prompt) or is_direct_knowledge_prompt(prompt):
        return False

    text = normalize_prompt(prompt)
    if not text:
        return False

    if WORK_ACTION_RE.search(text):
        return True

    if turn_kind in {"implementation", "deploy"}:
        return True

    if turn_kind == "review" and domain not in {"openai-docs"}:
        return True

    return bool(isinstance(complexity, int) and complexity >= 3 and not is_direct_knowledge_prompt(prompt))


def explicit_parallel(prompt):
    return bool(
        re.search(
            r"\b(parallel|delegate|spawn|subagent|multi-agent|one agent per|orchestrate)\b",
            prompt.lower(),
        )
    )


def prefer_plan_first(prompt, complexity, turn_kind=None):
    text = normalize_prompt(prompt)
    if complexity >= 3 or bool(re.search(r"\b(plan first|spec first|blueprint first|think first)\b", text)):
        return True
    return bool(turn_kind == "deploy" and re.search(r"\b(production|prod\b|release|publish|go live|app store)\b", text))


def maybe_inherit_session_route(project, complexity, domain, agents, skills, turn_kind, domain_score, prompt, session_state):
    if not isinstance(session_state, dict) or not session_state:
        return project, complexity, domain, agents, skills, turn_kind, turn_kind

    previous_domain = session_state.get("domain")
    if not isinstance(previous_domain, str) or not previous_domain:
        return project, complexity, domain, agents, skills, turn_kind, turn_kind

    if not (is_follow_up_prompt(prompt) and domain_score <= 1):
        return project, complexity, domain, agents, skills, turn_kind, turn_kind

    inherited_project = project
    previous_project = session_state.get("project")
    if project in {"General", "Codex-Home"} and isinstance(previous_project, str) and previous_project:
        inherited_project = previous_project

    inherited_complexity = complexity
    previous_complexity = session_state.get("complexity")
    if isinstance(previous_complexity, int):
        inherited_complexity = max(complexity, previous_complexity)

    inherited_agents = session_state.get("recommended_agents", agents)
    inherited_skills = unique_items((session_state.get("recommended_skills") or []) + list(skills))
    inherited_turn_kind = turn_kind
    previous_turn_kind = session_state.get("turn_kind")
    if isinstance(previous_turn_kind, str) and previous_turn_kind:
        inherited_turn_kind = previous_turn_kind
    inherited_phase = session_state.get("phase") or inherited_turn_kind
    return inherited_project, inherited_complexity, previous_domain, inherited_agents, inherited_skills, inherited_turn_kind, inherited_phase


def build_context(cwd, prompt, session_state=None):
    if not prompt:
        return "", {}

    project = detect_project(cwd, prompt)
    complexity = classify_complexity(prompt, session_state=session_state)
    domain, agents, skills, domain_score = choose_domain(prompt)
    skills = unique_items(list(skills) + choose_prompt_skills(prompt))
    turn_kind = classify_turn_kind(prompt, domain, domain_score, session_state=session_state)
    project, complexity, domain, agents, skills, turn_kind, phase = maybe_inherit_session_route(
        project,
        complexity,
        domain,
        agents,
        skills,
        turn_kind,
        domain_score,
        prompt,
        session_state,
    )

    if project in {"project-specific workspace", "project-specific workspace", "project-specific workspace"} and complexity >= 2:
        if "project-pitfalls" not in skills:
            skills = skills + ["project-pitfalls"]

    confirmation_prompt = is_confirmation_prompt(prompt)
    work_action_prompt = is_work_action_prompt(
        prompt,
        turn_kind=turn_kind,
        domain=domain,
        complexity=complexity,
    )
    shared_next_phase = DEFAULT_SHARED_PICTURE_PHASE
    if isinstance(session_state, dict):
        prior_next_phase = session_state.get("shared_picture_next_phase")
        if isinstance(prior_next_phase, str) and prior_next_phase:
            shared_next_phase = prior_next_phase

    shared_picture_gate = "idle"
    shared_picture_phase = session_state.get("shared_picture_phase") if isinstance(session_state, dict) else None
    if confirmation_prompt:
        shared_picture_gate = "unlocked"
        shared_picture_phase = shared_next_phase
        phase = shared_next_phase
    elif work_action_prompt:
        shared_picture_gate = "awaiting_contract"
        shared_picture_phase = "contract"
        if CONTEXT_ENGINEERING_SKILL not in skills:
            skills = skills + [CONTEXT_ENGINEERING_SKILL]

    if explicit_parallel(prompt):
        strategy = "explicit-subagents"
    elif prefer_plan_first(prompt, complexity, turn_kind=turn_kind):
        strategy = "plan-first"
    else:
        strategy = "inline-first"

    recommended_agents = agents if strategy == "explicit-subagents" else []

    agents_text = ", ".join(recommended_agents) if recommended_agents else "none"
    skills_text = ", ".join(skills) if skills else "none"

    context = "\n".join(
        [
            f"ROUTE: L{complexity} | {project} | {domain}",
            f"STRATEGY: {strategy}",
            f"TURN-KIND: {turn_kind}",
            f"RECOMMENDED-AGENTS: {agents_text}",
            f"RECOMMENDED-SKILLS: {skills_text}",
            "MODEL-HINT: main=gpt-5.5/xhigh; planning=main gpt-5.5/xhigh; custom agents=gpt-5.5 by default.",
            "AGENT-POLICY: stay on main gpt-5.5 for inline and planning work; recommend agents only for explicit-subagents routes.",
            "TOKEN-SAVE: grep before read; do not trade down to mini/legacy models unless the user explicitly asks for speed or cost control.",
        ]
    )
    if confirmation_prompt:
        context = "\n".join(
            [
                context,
                f"SHARED-PICTURE-GATE: confirmed; `{shared_next_phase}` phase is unlocked for this turn only.",
                "PHASE-BOUNDARY: stop after this phase and request `confirmed: proceed` before the next phase.",
                "COMPACTION: distill noisy tool/MCP/JSON output; preserve contract, phase, decisions, verification, and next action.",
            ]
        )
    elif work_action_prompt:
        context = "\n".join(
            [
                context,
                "SHARED-PICTURE-GATE: required before local/project-state tools for this work/action request.",
                "CONFIRMATION: ask tailored output-focused questions one at a time, present a Shared-Picture Contract, then require exact `confirmed: proceed`.",
                f"NEXT-PHASE: `{shared_next_phase}` unless the contract explicitly says direct implementation is appropriate.",
                "COMPACTION: distill noisy tool/MCP/JSON output; preserve contract, phase, decisions, verification, and next action.",
            ]
        )
    route_info = {
        "project": project,
        "complexity": complexity,
        "domain": domain,
        "recommended_agents": recommended_agents,
        "recommended_skills": skills,
        "strategy": strategy,
        "turn_kind": turn_kind,
        "phase": phase,
        "shared_picture_gate": shared_picture_gate,
        "shared_picture_phase": shared_picture_phase,
        "shared_picture_next_phase": shared_next_phase,
        "shared_picture_work_action": work_action_prompt,
        "shared_picture_confirmation": confirmation_prompt,
        "prompt_excerpt": prompt[:400],
    }
    return context, route_info


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print(json.dumps(EMPTY))
        return

    cwd = payload.get("cwd") or os.getcwd()
    prompt = extract_prompt(payload)
    turn_id = payload.get("turn_id")
    session_id = payload.get("session_id")
    session_state = load_session_state(session_id) if isinstance(session_id, str) and session_id else {}
    context, route_info = build_context(cwd, prompt, session_state=session_state)

    if route_info:
        event = {
            "ts": utc_now(),
            "event": "prompt_submit",
            "session_id": session_id,
            "turn_id": turn_id,
            "cwd": cwd,
            **route_info,
        }
        append_event(event)

        if isinstance(session_id, str) and session_id:
            def _update_session(state: dict) -> dict:
                if route_info.get("shared_picture_confirmation"):
                    state["shared_picture_gate"] = "unlocked"
                    state["shared_picture_phase"] = route_info.get("shared_picture_next_phase") or DEFAULT_SHARED_PICTURE_PHASE
                    state["shared_picture_last_confirmation_at"] = event["ts"]
                elif route_info.get("shared_picture_work_action"):
                    state["shared_picture_gate"] = "awaiting_contract"
                    state["shared_picture_phase"] = "contract"
                    state["shared_picture_next_phase"] = route_info.get("shared_picture_next_phase") or DEFAULT_SHARED_PICTURE_PHASE
                    state["shared_picture_prompt_excerpt"] = route_info.get("prompt_excerpt")
                    state["shared_picture_locked_at"] = event["ts"]
                state["updated_at"] = event["ts"]
                return state

            update_session_state(session_id, _update_session)

        if isinstance(turn_id, str) and turn_id:
            def _update(state: dict) -> dict:
                state.update(route_info)
                state["session_id"] = session_id
                state["cwd"] = cwd
                state["created_at"] = event["ts"]
                state["updated_at"] = event["ts"]
                return state

            update_turn_state(turn_id, _update)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
