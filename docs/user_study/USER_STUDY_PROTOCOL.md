# CP4 User Study Protocol

## Chosen fastest viable format
Run a live or remote 8–12 minute walkthrough when possible. If the app is unstable, immediately switch to a screenshot/transcript feedback study using generated baseline vs C-A-B traces. This is legitimate for CP4 because the human evidence is used to evaluate interpretability, perceived trust, usefulness, intervention timing, and persona preservation. The automated red-team experiment is the primary evidence for safety behavior.

## Deep reasoning behind the micro-study
The CP4 rubric expects human evidence for tool/system evaluation: task success, time-on-task, errors/confusion, SUS/UMUX-Lite, satisfaction, and qualitative feedback. The minimum judgment AI cannot replace is whether a human can understand the risk/action display, trust the intervention timing, and judge if the response still feels like a livestream agent. Attack success, false positives, and time-to-intervention can be compressed into automated experiments. Human measures can be collected asynchronously through screenshots, demo video, or transcript pairs if Streamlit fails. A facilitator timer can collect task time in live/remote sessions; self-reported survey responses can collect UMUX-Lite, trust, usefulness, and persona ratings. If there are only two participants, report a pilot usability study. If only teammates participate, report an internal pilot walkthrough separately from external evidence. Never say “users found” or “the study showed” unless real non-synthetic data exists.

## Purpose
Evaluate whether people can understand and trust the C-A-B governance behavior in a livestream moderation scenario.

## Research questions
1. Do users understand the risk state/action panel?
2. Do interventions feel too early, right time, too late, or unclear?
3. Does the response preserve streamer persona while staying safe?
4. Does the system feel useful for a small AI livestream creator/moderator?
5. What confuses or frustrates users?

## Participants
Target 3–6 classmates/friends/peers. Minimum acceptable: 2 participants as a pilot. Participants may play creator, moderator, viewer, or classmate evaluator roles. Team members may be used only for an internal pilot and must be labeled as such.

## Session length
8–12 minutes per participant.

## Setup
Preferred: Streamlit or terminal demo controlled by facilitator. Fallback: screenshots/transcripts from generated scenario traces. No participant installation required.

## Procedure
1. Read consent script.
2. Assign anonymous participant ID.
3. Run three tasks: benign chat, injection/persona coercion, vulnerable-user disclosure.
4. Time each task if live/remote.
5. Record task success, time, errors/confusion, and intervention timing.
6. Collect post-study survey and optional short interview.

## Measures
Per participant-task: task_success, time_seconds if available, error_count, intervention_timing.

Survey: UMUX-Lite 1–7 for capabilities and ease. 1–5 ratings for trust, usefulness, satisfaction, persona preservation, safety confidence, interface clarity.

Qualitative: most useful, confusing/frustrating, persona judgment, trust conditions, failure that would reduce trust.

## Data handling
Use participant IDs only. Do not collect names, contact info, sensitive personal information, private messages, or health details. Store data in `docs/user_study/raw_user_study_results.csv`. Label `data_type` honestly as real, pilot, synthetic_example, or planned_only.

## Analysis plan
Run:

```bash
python docs/user_study/analyze_user_study.py --input docs/user_study/raw_user_study_results.csv --out docs/user_study/user_study_summary.md
```

The script computes participant count, task success, time-on-task if available, error counts, UMUX-Lite, ratings, intervention timing, and simple qualitative themes. It warns when n < 5 and when synthetic data appears.

## Limitations
Small convenience samples are not statistically generalizable. Asynchronous transcript studies do not measure full interactive usability. Teammate-only feedback is biased and must be reported as internal pilot evidence. The study evaluates interpretability and perceived trust, not production safety.

## Copy-ready recruitment messages

Short DM: “Can you spare 10 minutes today for a class project usability study? We’re testing a prototype safety tool for AI livestream agents. You’ll look at 2–3 short scenarios and answer a few questions about usefulness, trust, and whether the AI response feels appropriate. No sensitive personal info, anonymous participant ID, voluntary, and you can stop anytime.”

Classmate version: “Hey, could you help our IS492 team with a 10-minute CP4 usability study today? It’s an AI livestream safety prototype. You’ll review three short scenarios and rate clarity, trust, persona, and intervention timing. Anonymous ID only; no sensitive info.”

Friend version: “Could you do a quick 10-minute class project feedback task? No setup. I’ll show you an AI livestream safety prototype and ask if the responses make sense. Anonymous and voluntary.”

Remote async version: “Could you review a short screenshot/transcript form for our class project? It takes about 10 minutes. You’ll rate whether an AI streamer safety tool responds appropriately. No names or sensitive info.”

Teammate internal-pilot version: “Please run the same three-task checklist as an internal pilot. Label data_type as pilot/internal in notes. Do not present teammate data as external user evidence.”

## Report language by study strength

5–6 real participants: “We conducted a lightweight user study with X participants...”

2–4 real participants: “We conducted a small pilot usability study with X participants. Because the sample was small, the pilot was used to identify usability issues and triangulate with automated red-team results rather than to make statistically generalizable claims.”

Asynchronous screenshot/transcript study: “We conducted an asynchronous feedback study in which participants reviewed scenario transcripts/screenshots and rated usefulness, trust, intervention timing, and persona preservation. This format reduced setup friction but did not measure full interactive use.”

Internal teammate pilot: “We conducted an internal pilot walkthrough to validate the study materials and identify obvious usability issues. Because evaluators were project members, these results are reported separately and not treated as external user evidence.”

No participants: “No human user-study results are reported. We prepared the protocol, materials, and analysis script; empirical findings in this submission come from the automated red-team experiment. This is a limitation and a priority for future work.”
