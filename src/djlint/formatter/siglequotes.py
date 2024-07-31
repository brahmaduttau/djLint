"""Module that provides a function to replace single quotes in HTML."""

import regex as re

from djlint.settings import Config


def clean_single_quotes(html: str, config: Config) -> str:
    """Compress html."""
    pattern = "{%[ \t]*?(?:trans(?:late)?|with|extends|include|now)[\\s]+?(?:(?:(?!%}|').)+?=)?'(?:(?!%}|').)*?'(?:(?!%}).)*?%}"

    def _clean_tag(match: re.Match) -> str:
        return match.group().replace("'", '"')

    html = re.sub(
        pattern=re.compile(
            pattern=pattern,
            flags=re.MULTILINE | re.VERBOSE | re.IGNORECASE,
        ),
        repl=_clean_tag,
        string=html,
    )

    return html
