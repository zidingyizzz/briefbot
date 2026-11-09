"""YAML config loading with ${ENV_VAR} / ${ENV_VAR:-default} interpolation."""
import os
import re

import yaml

_ENV_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


def _interpolate(value):
    """Recursively replace ${VAR} / ${VAR:-default} in strings from the environment."""
    if isinstance(value, str):
        def repl(match):
            var, default = match.group(1), match.group(2)
            env_val = os.environ.get(var)
            if env_val:  # non-empty value wins
                return env_val
            if default is not None:  # ${VAR:-default} form
                return default
            return ""  # unset and no default -> empty, channels will fail loudly
        return _ENV_RE.sub(repl, value)
    if isinstance(value, dict):
        return {k: _interpolate(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate(v) for v in value]
    return value


def load_config(path):
    """Load, interpolate and validate a config file. Raises ValueError on bad configs."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    cfg = _interpolate(raw)
    validate(cfg)
    return cfg


def validate(cfg):
    problems = []
    jobs = cfg.get("jobs")
    if not jobs or not isinstance(jobs, list):
        problems.append("config must define a non-empty `jobs` list")
        raise ValueError("Invalid configuration:\n- " + "\n- ".join(problems))
    for idx, job in enumerate(jobs):
        label = job.get("name") or f"jobs[{idx}]"
        if not job.get("name"):
            problems.append(f"{label}: `name` is required")
        if not job.get("sources"):
            problems.append(f"{label}: at least one entry in `sources` is required")
        if not job.get("channels"):
            problems.append(f"{label}: at least one entry in `channels` is required")
    if problems:
        raise ValueError("Invalid configuration:\n- " + "\n- ".join(problems))
