"""Module A — risk state machine and autonomy policy."""

from .autonomy_policy import decide_action
from .mediation import apply_mediation
from .risk_tracker import update_risk_from_module_c

__all__ = [
    "decide_action",
    "apply_mediation",
    "update_risk_from_module_c",
]
