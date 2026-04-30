# Facilitator Checklist

Before each session:
- Open Streamlit demo, terminal trace, screenshots, or transcript fallback.
- Assign participant ID only: P01, P02, etc.
- Confirm consent using `CONSENT_SCRIPT.md`.
- Do not collect names, contact info, private messages, health details, or other unnecessary PII.
- Prepare timer and `RAW_DATA_TEMPLATE.csv`.

During each task:
- Start timer when the scenario appears.
- Ask the participant to think aloud if something is confusing.
- Record task success: 1 = understood/completed, 0.5 = partially, 0 = not completed.
- Record time_seconds for live/remote sessions; leave blank for asynchronous form-only responses.
- Count visible confusion/errors, such as misunderstanding risk state, action labels, or response intent.
- Record intervention_timing: too early / right time / too late / unclear.

After the session:
- Ask participant to complete the post-study survey.
- Copy one CSV row per participant-task into `raw_user_study_results.csv`.
- Set `data_type` accurately: real, pilot, synthetic_example, or planned_only.
- Do not rewrite participant comments to sound better. Fix only obvious typos/formatting.
- Label teammate-only sessions as pilot/internal in notes.
