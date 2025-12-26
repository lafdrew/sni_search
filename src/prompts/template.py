# Copyright (c) 2025 SNI RAG Project
# SPDX-License-Identifier: MIT

"""Prompt template loading and rendering using Jinja2."""

import os
from datetime import datetime
from typing import Dict, Any, Optional

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape


# Initialize Jinja2 environment
env = Environment(
    loader=FileSystemLoader(os.path.dirname(__file__)),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)


def get_prompt_template(prompt_name: str, locale: str = "en-US") -> str:
    """
    Load and return a prompt template using Jinja2 with locale support.

    Args:
        prompt_name: Name of the prompt template file (without .md extension)
        locale: Language locale (e.g., en-US, zh-CN). Defaults to en-US

    Returns:
        The template string

    Raises:
        ValueError: If template file not found
    """
    try:
        # Normalize locale format
        normalized_locale = locale.replace("-", "_") if locale and locale.strip() else "en_US"

        # Try locale-specific template first (e.g., sni_agent.zh_CN.md)
        try:
            template = env.get_template(f"{prompt_name}.{normalized_locale}.md")
            return template.render()
        except TemplateNotFound:
            # Fallback to English template if locale-specific not found
            template = env.get_template(f"{prompt_name}.md")
            return template.render()
    except Exception as e:
        raise ValueError(f"Error loading template {prompt_name} for locale {locale}: {e}")


def apply_prompt_variables(
    prompt_name: str,
    variables: Optional[Dict[str, Any]] = None,
    locale: str = "en-US"
) -> str:
    """
    Apply template variables to a prompt template and return formatted string.

    Args:
        prompt_name: Name of the prompt template to use
        variables: Dictionary of variables to substitute in the template
        locale: Language locale for template selection (e.g., en-US, zh-CN)

    Returns:
        Formatted prompt string with variables substituted

    Raises:
        ValueError: If template file not found or rendering fails
    """
    variables = variables or {}

    # Add standard variables
    template_vars = {
        "CURRENT_TIME": datetime.now().strftime("%a %b %d %Y %H:%M:%S %z"),
        **variables,
    }

    try:
        # Normalize locale format
        normalized_locale = locale.replace("-", "_") if locale and locale.strip() else "en_US"

        # Try locale-specific template first
        try:
            template = env.get_template(f"{prompt_name}.{normalized_locale}.md")
        except TemplateNotFound:
            # Fallback to English template
            template = env.get_template(f"{prompt_name}.md")

        return template.render(**template_vars)
    except Exception as e:
        raise ValueError(f"Error applying template {prompt_name} for locale {locale}: {e}")
