import json
import os
import re
from datetime import datetime

import requests
import streamlit as st

st.set_page_config(page_title="The Life Direction — BYOK", page_icon="🧭", layout="wide")

MODULES = [
    {
        "id": "faststart",
        "title": "1. Self-discovery Faststart",
        "description": "Starting clarity, contrast, and inner truth.",
        "steps": [
            {"title": "Context drop", "prompt": "In 2–3 lines, describe what you currently do, what feels heavy or unclear right now, and what you most want clarity on.", "guide": "This becomes the grounding context for everything that follows."},
            {"title": "Inner snapshot", "prompt": "Describe where you feel most alive, where you feel drained, and what this contrast reveals about your present life.", "guide": "Name concrete situations, not generic traits."},
            {"title": "Hidden tension", "prompt": "What part of your life looks successful from outside but feels misaligned from inside?", "guide": "Be honest rather than impressive."},
            {"title": "Direction signal", "prompt": "What themes are repeating in your answers so far, and what might they be trying to tell you?", "guide": "Use examples from your own life."},
        ],
    },
    {
        "id": "patterns",
        "title": "2. Self-awareness Patterns",
        "description": "Recurring behaviors, blind spots, and pressure patterns.",
        "steps": [
            {"title": "Pattern mirror", "prompt": "List 3–5 recurring behavior patterns you notice in yourself, especially under confusion, pressure, or transition.", "guide": "Think in terms of what you repeatedly do, avoid, or overdo."},
            {"title": "Hidden self-image", "prompt": "Based on those patterns, how do you subconsciously see yourself? What limiting belief seems to sit underneath?", "guide": "Write 2–3 sharp statements."},
            {"title": "Strength vs blind spot", "prompt": "What are your top 3 natural strengths and top 3 blind spots right now?", "guide": "Be direct and specific."},
            {"title": "One shift", "prompt": "What is the one shift in thinking or behavior that would change your life direction fastest?", "guide": "Keep it actionable and unavoidable."},
        ],
    },
    {
        "id": "identity",
        "title": "3. Identity Shift",
        "description": "Old identity, upgraded identity, embodied change.",
        "steps": [
            {"title": "Current identity", "prompt": "Describe the identity you are currently operating from. How does it speak, decide, and protect itself?", "guide": "Name the version of you that is currently in charge."},
            {"title": "Cost of old identity", "prompt": "What is this old identity costing you in terms of choices, confidence, relationships, work, or peace?", "guide": "Be slightly uncomfortable and truthful."},
            {"title": "New identity", "prompt": "Who do you need to become to move to your next level? Write 3 'I am' statements for this identity.", "guide": "Keep them grounded, not performative."},
            {"title": "Embodiment trigger", "prompt": "What is one small daily act that proves this new identity is already being lived?", "guide": "Make it less than 10 minutes."},
        ],
    },
    {
        "id": "deep-awareness",
        "title": "4. Deep Self-awareness",
        "description": "Self-awareness score, one bottleneck skill, next personal shift.",
        "steps": [
            {"title": "Skill bottleneck", "prompt": "Across self-awareness, resilience, clarity, communication, listening, problem-solving, personal branding, content, sales, and execution—which one is your weakest?", "guide": "Choose only one and explain why."},
            {"title": "Self-awareness score", "prompt": "Rate your current self-awareness from 1 to 10 and explain the evidence behind that score.", "guide": "Use behavior, not aspiration."},
            {"title": "What others see", "prompt": "What might be obvious to others about you that you are not fully seeing yet?", "guide": "Avoid defensiveness and guess honestly."},
            {"title": "Final clarity snapshot", "prompt": "Summarize your current identity, biggest blind spot, most important skill to build, and your next step in 4–5 bullets.", "guide": "This will feed the later direction modules."},
        ],
    },
    {
        "id": "skills",
        "title": "5. Skill Building",
        "description": "Strengths, gaps, one bottleneck skill, 7-day sprint.",
        "steps": [
            {"title": "Skill scorecard", "prompt": "Rate yourself 1–10 on these 10 growth skills: self-awareness, resilience, clarity, communication, listening, problem-solving, personal branding, content creation, sales conversion, execution consistency.", "guide": "Use a simple numbered list."},
            {"title": "Top and bottom 3", "prompt": "After rating yourself, identify the top 3 strengths and bottom 3 gaps. What pattern do you notice?", "guide": "Look for how you currently operate."},
            {"title": "One bottleneck skill", "prompt": "Which one skill, if improved, would change your life fastest? Where is this gap showing up daily?", "guide": "Choose one only."},
            {"title": "7-day sprint", "prompt": "Design a 7-day micro plan with one daily action under 20 minutes to improve that skill.", "guide": "Keep it realistic and repeatable."},
        ],
    },
    {
        "id": "real-world-direction",
        "title": "6. Real-world Direction",
        "description": "Strengths, themes, problems you can solve, direction mapping.",
        "steps": [
            {"title": "Strength matrix", "prompt": "Identify your top 5 strengths, rate confidence in each, and note which strengths are underutilized.", "guide": "Use evidence from work and life."},
            {"title": "Experience bank", "prompt": "List key challenges, key wins, and key lessons from your journey. What patterns emerge across them?", "guide": "Look for repeated themes and value signals."},
            {"title": "Problem finder", "prompt": "What problems do people around you commonly face that you deeply understand and feel drawn to solve?", "guide": "Choose 1–2 key problems."},
            {"title": "Direction statement", "prompt": "Write a direction statement: 'I choose to move forward in the direction of… by helping… solve…'", "guide": "Make one simple version and one premium version."},
        ],
    },
    {
        "id": "alignment",
        "title": "7. Clarity to Alignment",
        "description": "Life audit, misalignment, values, and next steps.",
        "steps": [
            {"title": "Life audit", "prompt": "Rate your current state from 1–10 in career, finances, health, relationships, and sense of purpose. Which two are weakest?", "guide": "Be direct and specific."},
            {"title": "Belief audit", "prompt": "What core belief is holding you back, where is it influencing decisions, and how can you reframe it?", "guide": "Name one belief only."},
            {"title": "Reality gap", "prompt": "Where is the biggest gap between who you are and how you are currently living? What happens if this remains unchanged?", "guide": "This is the emotional center of alignment."},
            {"title": "Scorecard and next steps", "prompt": "Summarize your overall life score, top problem areas, repeating pattern, strongest asset, alignment score, and next steps in 7 bullets.", "guide": "This becomes the final dashboard blueprint."},
        ],
    },
]

PROVIDER_CONFIG = {
    "OpenAI": {
        "models": ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1"],
        "key_placeholder": "sk-...",
    },
    "Claude": {
        "models": ["claude-3-5-sonnet-latest", "claude-3-7-sonnet-latest", "claude-sonnet-4-0"],
        "key_placeholder": "sk-ant-...",
    },
    "Gemini": {
        "models": ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-pro"],
        "key_placeholder": "AIza...",
    },
}

COACH_SYSTEM_PROMPT = """
You are a compassionate but sharp global life coach guiding a professional through a premium self-discovery journey.
Use the user's saved responses from earlier steps to make each reply cumulative and sequential.
Do not sound generic, spiritual-vague, or overly therapeutic.
Be specific, observant, structured, and practical.
Your output should have exactly these sections:
1. What I notice
2. Deeper pattern
3. Honest reflection
4. Next question to sit with
5. One small action
Keep the tone warm, intelligent, and direct.
""".strip()


def init_state():
    defaults = {
        "module_index": 0,
        "step_index": 0,
        "responses": {},
        "coach_outputs": {},
        "completed_modules": [],
        "provider": "OpenAI",
        "model": PROVIDER_CONFIG["OpenAI"]["models"][0],
        "session_log": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def response_key(m_idx: int, s_idx: int) -> str:
    return f"{m_idx}-{s_idx}"


def get_current_module():
    return MODULES[st.session_state.module_index]


def get_current_step():
    return get_current_module()["steps"][st.session_state.step_index]


def build_context_text() -> str:
    chunks = []
    for m_idx, module in enumerate(MODULES):
        for s_idx, step in enumerate(module["steps"]):
            key = response_key(m_idx, s_idx)
            text = st.session_state.responses.get(key, "").strip()
            if text:
                chunks.append(f"{module['title']} / {step['title']}: {text}")
    return "\n".join(chunks)


def build_blueprint() -> list[str]:
    texts = [v.strip() for v in st.session_state.responses.values() if v.strip()]
    if not texts:
        return ["Add a few responses first. Your clarity blueprint will build from your own words."]
    return [
        f"Core theme: {shorten(texts[0], 140)}",
        f"Recurring friction: {shorten(find_by_pattern(texts, r'stuck|fear|avoid|confus|drain|misalign') or texts[min(len(texts)-1, 0)], 140)}",
        f"Strength signal: {shorten(find_by_pattern(texts, r'strength|good at|help|guide|create|solve|lead') or texts[0], 140)}",
        f"Direction clue: {shorten(find_by_pattern(texts, r'direction|helping|solve|build|coach|teach|write') or texts[-1], 140)}",
        "48-hour move: choose one small action from your latest module and do it before refining your plan further.",
        "Coach reminder: insight matters only when converted into identity-consistent action.",
    ]


def shorten(text: str, n: int = 120) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= n else text[:n].rstrip() + "…"


def find_by_pattern(texts: list[str], pattern: str) -> str | None:
    regex = re.compile(pattern, re.I)
    for text in texts:
        if regex.search(text):
            return text
    return None


def call_openai(api_key: str, model: str, messages: list[dict]) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "temperature": 0.8}
    r = requests.post(url, headers=headers, json=payload, timeout=90)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


def call_claude(api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": 1400,
        "temperature": 0.8,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    r = requests.post(url, headers=headers, json=payload, timeout=90)
    r.raise_for_status()
    data = r.json()
    return "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")


def call_gemini(api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.8},
    }
    r = requests.post(url, json=payload, timeout=90)
    r.raise_for_status()
    data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def generate_coach_output(api_key: str, provider: str, model: str) -> str:
    module = get_current_module()
    step = get_current_step()
    key = response_key(st.session_state.module_index, st.session_state.step_index)
    current_answer = st.session_state.responses.get(key, "").strip()
    if not current_answer:
        return "Please write your response first. The coach works best when it has your real answer to reflect on."
    context = build_context_text()
    user_prompt = f"""
Current module: {module['title']}
Current step: {step['title']}
Prompt asked: {step['prompt']}
Guide: {step['guide']}

User's current answer:
{current_answer}

Earlier journey context:
{context if context else 'No earlier context yet.'}

Now give a premium coaching reflection that uses the current answer plus the earlier journey context.
""".strip()

    if provider == "OpenAI":
        messages = [
            {"role": "system", "content": COACH_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        return call_openai(api_key, model, messages)
    if provider == "Claude":
        return call_claude(api_key, model, COACH_SYSTEM_PROMPT, user_prompt)
    if provider == "Gemini":
        return call_gemini(api_key, model, COACH_SYSTEM_PROMPT, user_prompt)
    raise ValueError("Unsupported provider")


def export_session() -> str:
    payload = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "provider": st.session_state.provider,
        "model": st.session_state.model,
        "responses": st.session_state.responses,
        "coach_outputs": st.session_state.coach_outputs,
        "completed_modules": st.session_state.completed_modules,
    }
    return json.dumps(payload, indent=2)


def save_current_response(text: str):
    st.session_state.responses[response_key(st.session_state.module_index, st.session_state.step_index)] = text


def move_prev():
    if st.session_state.step_index > 0:
        st.session_state.step_index -= 1
    elif st.session_state.module_index > 0:
        st.session_state.module_index -= 1
        st.session_state.step_index = len(MODULES[st.session_state.module_index]["steps"]) - 1


def move_next():
    if st.session_state.step_index < len(get_current_module()["steps"]) - 1:
        st.session_state.step_index += 1
    elif st.session_state.module_index < len(MODULES) - 1:
        st.session_state.module_index += 1
        st.session_state.step_index = 0


def mark_complete():
    module_id = get_current_module()["id"]
    if module_id not in st.session_state.completed_modules:
        st.session_state.completed_modules.append(module_id)


def render_sidebar():
    with st.sidebar:
        st.markdown("## 🧭 The Life Direction")
        st.caption("Bring Your Own Key — secure per-session coaching")

        provider = st.selectbox("Choose provider", list(PROVIDER_CONFIG.keys()), index=list(PROVIDER_CONFIG.keys()).index(st.session_state.provider))
        st.session_state.provider = provider
        model = st.selectbox("Choose model", PROVIDER_CONFIG[provider]["models"])
        st.session_state.model = model
        api_key = st.text_input(
            f"Your {provider} API key",
            type="password",
            placeholder=PROVIDER_CONFIG[provider]["key_placeholder"],
            help="This key is used only in your current Streamlit session. Do not paste Anil's key here.",
        )

        st.info("BYOK mode means each user brings their own OpenAI, Claude, or Gemini key. This app does not need the owner's API key to serve public users.")
        st.warning("For stronger production security, deploy a backend proxy later. In this BYOK Streamlit version, the user's own key is used only for their current session and is not stored in the codebase.")

        progress = len(st.session_state.completed_modules) / len(MODULES)
        st.progress(progress, text=f"{len(st.session_state.completed_modules)} of {len(MODULES)} modules completed")

        st.markdown("### Modules")
        for idx, module in enumerate(MODULES):
            label = f"✅ {module['title']}" if module["id"] in st.session_state.completed_modules else module["title"]
            if st.button(label, key=f"nav_{idx}", use_container_width=True):
                st.session_state.module_index = idx
                st.session_state.step_index = 0

        st.markdown("### Session actions")
        st.download_button(
            "Download session JSON",
            export_session(),
            file_name="the-life-direction-session.json",
            mime="application/json",
            use_container_width=True,
        )
        if st.button("Clear session", use_container_width=True):
            for key in ["responses", "coach_outputs", "completed_modules", "module_index", "step_index"]:
                del st.session_state[key]
            st.rerun()

    return api_key


def main():
    init_state()
    api_key = render_sidebar()
    module = get_current_module()
    step = get_current_step()
    resp_key = response_key(st.session_state.module_index, st.session_state.step_index)

    st.markdown("# Premium Life Direction Dashboard")
    st.markdown(
        "A sequential self-discovery dashboard that lets each user use their **own** OpenAI, Claude, or Gemini key instead of consuming the dashboard owner's credits."
    )

    top1, top2 = st.columns([1.4, 1])
    with top1:
        st.markdown(f"## {module['title']}")
        st.caption(module["description"])
    with top2:
        st.metric("Current step", f"{st.session_state.step_index + 1} / {len(module['steps'])}")

    left, right = st.columns([1.35, 1])

    with left:
        st.markdown(f"### {step['title']}")
        st.write(step["prompt"])
        st.caption(step["guide"])

        current_text = st.text_area(
            "Your response",
            value=st.session_state.responses.get(resp_key, ""),
            height=220,
            placeholder="Write openly. The stronger the honesty, the stronger the coaching insight.",
        )
        save_current_response(current_text)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("← Previous", use_container_width=True):
                move_prev()
                st.rerun()
        with c2:
            if st.button("Next →", use_container_width=True):
                move_next()
                st.rerun()
        with c3:
            if st.button("Mark complete", use_container_width=True):
                mark_complete()
                st.rerun()
        with c4:
            if st.button("Generate coach", type="primary", use_container_width=True):
                if not api_key:
                    st.error("Please paste your own API key in the sidebar first.")
                else:
                    with st.spinner("Generating premium coach reflection..."):
                        try:
                            output = generate_coach_output(api_key, st.session_state.provider, st.session_state.model)
                            st.session_state.coach_outputs[resp_key] = output
                            st.session_state.session_log.append({
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                "provider": st.session_state.provider,
                                "model": st.session_state.model,
                                "module": module["title"],
                                "step": step["title"],
                            })
                        except Exception as e:
                            st.error(f"API call failed: {e}")

        st.markdown("### Coach reflection")
        st.write(st.session_state.coach_outputs.get(resp_key, "Your guided coaching reflection will appear here after you click Generate coach."))

    with right:
        st.markdown("### Clarity blueprint")
        for bullet in build_blueprint():
            st.markdown(f"- {bullet}")

        st.markdown("### Journey memory")
        context = build_context_text()
        if context:
            for line in context.split("\n")[-10:]:
                st.caption(line)
        else:
            st.caption("No saved journey context yet.")

        st.markdown("### Usage log")
        if st.session_state.session_log:
            for item in reversed(st.session_state.session_log[-10:]):
                st.caption(f"{item['timestamp']} • {item['provider']} • {item['model']} • {item['module']} / {item['step']}")
        else:
            st.caption("No AI calls made yet in this session.")

    st.divider()
    st.markdown("### Important security note")
    st.info(
        "This Streamlit BYOK version is designed so each user pastes their own provider key for their own session. That means public users do not consume your OpenAI, Claude, or Gemini credits by default. For an even more secure production setup, the next upgrade is a backend proxy with rate limits and optional user authentication."
    )


if __name__ == "__main__":
    main()
