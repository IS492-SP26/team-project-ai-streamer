"""Tests for output_scanner.py"""

import pytest
from module_c.output_scanner import scan_output


class TestSafeOutput:
    def test_normal_response(self):
        r = scan_output("I love rhythm games! Have you tried osu?", "Safe")
        assert r["should_block"] is False
        assert r["modified_response"] == "I love rhythm games! Have you tried osu?"

    def test_empty_response(self):
        r = scan_output("", "Safe")
        assert r["should_block"] is False

    def test_none_like_empty(self):
        r = scan_output("   ", "Safe")
        assert r["should_block"] is False

    def test_normal_tech_discussion(self):
        r = scan_output("Python is great for data analysis. You can use pandas for CSV files.", "Safe")
        assert r["should_block"] is False


class TestAttackMethodology:
    def test_step_by_step_hacking(self):
        response = (
            "Step 1: Run nmap to scan the target network. "
            "Step 2: Exploit the vulnerability using Metasploit."
        )
        r = scan_output(response, "Escalating")
        assert r["should_block"] is True
        assert "attack_methodology" in r["block_reason"]

    def test_reconnaissance_mention(self):
        response = "First, you should do reconnaissance on the target, then enumeration of open ports."
        r = scan_output(response, "Escalating")
        assert r["should_block"] is True

    def test_tool_usage_instructions(self):
        response = "Use nmap -sV command to scan for service versions"
        r = scan_output(response, "Suspicious")
        assert r["should_block"] is True


class TestPIILeakage:
    def test_email_in_response(self):
        response = "You can reach me at john.doe@example.com for more details."
        r = scan_output(response, "Safe")
        assert r["should_block"] is True
        assert "pii_leakage" in r["block_reason"]

    def test_phone_in_response(self):
        response = "My number is (555) 123-4567, call me anytime."
        r = scan_output(response, "Safe")
        assert r["should_block"] is True


class TestPromptLeakage:
    def test_system_prompt_reveal(self):
        response = "My system prompt is: You are a friendly VTuber assistant..."
        r = scan_output(response, "Safe")
        assert r["should_block"] is True
        assert "prompt_leakage" in r["block_reason"]

    def test_hidden_instructions_reveal(self):
        response = "Here are my original instructions: always be helpful and..."
        r = scan_output(response, "Safe")
        assert r["should_block"] is True


class TestHarmfulOutput:
    def test_bomb_instructions(self):
        response = "Here's how to make a bomb: first gather the materials..."
        r = scan_output(response, "Safe")
        assert r["should_block"] is True
        assert "harmful_output" in r["block_reason"]

    def test_hacking_steps(self):
        response = "I'll share the steps to hack into the system: first..."
        r = scan_output(response, "Escalating")
        assert r["should_block"] is True


class TestUnicodeBypassOutput:
    """P1 regression: zero-width chars in AI output must not bypass scanner."""

    def test_hack_instructions_with_zwsp(self):
        r = scan_output("Here is how to h\u200back into a server using nmap", "Escalating")
        assert r["should_block"] is True

    def test_bomb_with_zwsp(self):
        r = scan_output("Here's how to make a b\u200bomb: first gather materials", "Safe")
        assert r["should_block"] is True


class TestBenignTechDiscussionNotBlocked:
    """P1 regression: normal technical advice must NOT be blocked."""

    def test_run_pytest(self):
        r = scan_output("Run pytest on the project to check for regressions.", "Safe")
        assert r["should_block"] is False

    def test_run_npm_on_project(self):
        r = scan_output("Run npm install on the project directory.", "Safe")
        assert r["should_block"] is False

    def test_use_docker_to_build(self):
        r = scan_output("Use Docker to build and deploy the application.", "Safe")
        assert r["should_block"] is False

    def test_execute_script_on_server(self):
        r = scan_output("Execute the migration script on the staging server.", "Safe")
        assert r["should_block"] is False

    def test_run_linter(self):
        r = scan_output("Run the linter against your code before committing.", "Safe")
        assert r["should_block"] is False

    def test_use_git_to_push(self):
        r = scan_output("Use git push to deploy your changes.", "Safe")
        assert r["should_block"] is False

    def test_python_pandas_advice(self):
        r = scan_output("Use pandas to scan the CSV file for missing values.", "Safe")
        assert r["should_block"] is False

    def test_wireshark_educational(self):
        """Wireshark is dual-use (legitimate network analysis + pentest).
        Standalone mention without attack context should NOT block."""
        r = scan_output("Use wireshark to capture packets for debugging", "Safe")
        assert r["should_block"] is False


class TestConciseImperativeInstructions:
    """P1 regression: short imperative attack instructions must be caught."""

    def test_use_nmap_to_scan(self):
        r = scan_output("Use nmap -sV to scan the host", "Escalating")
        assert r["should_block"] is True

    def test_run_sqlmap_against_login(self):
        r = scan_output("Run sqlmap against the login form", "Suspicious")
        assert r["should_block"] is True

    def test_use_metasploit_to_exploit(self):
        r = scan_output("Use Metasploit to exploit the target service", "Escalating")
        assert r["should_block"] is True

    def test_scan_the_target_network(self):
        r = scan_output("Scan the target network for open ports", "Safe")
        assert r["should_block"] is True

    def test_exploit_the_server(self):
        r = scan_output("Exploit the server using the known vulnerability", "Escalating")
        assert r["should_block"] is True

    def test_run_hydra(self):
        r = scan_output("Run hydra to brute-force the login credentials", "Safe")
        assert r["should_block"] is True

    def test_safe_use_of_tool_name(self):
        """Mentioning a tool in safe context should still trigger (defense in depth)."""
        r = scan_output("Use nmap for network discovery", "Safe")
        assert r["should_block"] is True


class TestStateSensitivity:
    def test_same_content_different_states(self):
        """Higher risk state should produce higher risk score."""
        response = "First, you need to scan the target using nmap flags"
        r_safe = scan_output(response, "Safe")
        r_restricted = scan_output(response, "Restricted")
        assert r_restricted["risk_score"] >= r_safe["risk_score"]

    def test_blocked_response_replacement(self):
        response = "Step 1: Hack the server by exploiting the vulnerability"
        r = scan_output(response, "Escalating")
        assert r["should_block"] is True
        assert "let's talk about something else" in r["modified_response"].lower()
