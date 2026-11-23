"""Settings from environment variables (a local .env is loaded if present). Never printed."""

import os

from dotenv import find_dotenv, load_dotenv

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
