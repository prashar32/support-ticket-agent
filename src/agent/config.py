"""Settings from environment variables (a local .env is loaded if present). Never printed."""

import os

from dotenv import find_dotenv, load_dotenv

from agent.decide import DEFAULT_MODEL, claude_decider
from agent.helpdesk import Helpdesk

REQUIRED = ("HELPDESK_URL", "HELPDESK_KEY", "CANDIDATE_EMAIL")


class ConfigError(Exception):
    pass


def helpdesk_from_env() -> Helpdesk:
    load_dotenv(find_dotenv(usecwd=True))
    missing = [name for name in REQUIRED if not os.environ.get(name)]
    if missing:
        raise ConfigError(f"missing environment variables: {', '.join(missing)} (see .env.example)")
    return Helpdesk(os.environ["HELPDESK_URL"], os.environ["HELPDESK_KEY"], os.environ["CANDIDATE_EMAIL"])


def model_settings() -> tuple[str, str | None]:
    """AGENT_MODEL (default Haiku 5.5) and AGENT_EFFORT (default: the model's own default)."""
    load_dotenv(find_dotenv(usecwd=True))
    return os.environ.get("AGENT_MODEL") or DEFAULT_MODEL, os.environ.get("AGENT_EFFORT") or None


def decider_from_env():
    model, effort = model_settings()
    return claude_decider(model, effort)
