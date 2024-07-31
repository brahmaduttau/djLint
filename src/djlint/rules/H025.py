"""rule H025: Check for orphans html tags."""

import copy
from typing import Any, dict, list

import regex as re

from djlint.helpers import (
    inside_ignored_linter_block,
    inside_ignored_rule,
    overlaps_ignored_block,
)
from djlint.lint import get_line
from djlint.settings import Config


def run(
    rule: dict[str, Any],
    config: Config,
    html: str,
    filepath: str,
    line_ends: list[dict[str, int]],
    *args: Any,
    **kwargs: Any,
) -> list[dict[str, str]]:
    """Check for orphans html tags."""
    errors: list[dict[str, str]] = []
    open_tags: list[re.Match] = []
    orphan_tags: list[re.Match] = []

    for match in re.finditer(
        re.compile(
            r"<(/?(\w+))\s*(" + config.attribute_pattern + r"|\s*)*\s*?>",
            re.VERBOSE,
        ),
        html,
    ):
        if match.group(1) and not re.search(
            re.compile(rf"^/?{config.always_self_closing_html_tags}\b", re.I | re.X),
            match.group(1),
        ):
            # close tags should equal open tags
            if match.group(1)[0] != "/":
                open_tags.insert(0, match)
            else:
                for i, tag in enumerate(copy.deepcopy(open_tags)):
                    if tag.group(2) == match.group(1)[1:]:
                        open_tags.pop(i)
                        break
                else:
                    # there was no open tag matching the close tag
                    orphan_tags.append(match)

    for match in open_tags + orphan_tags:
        if (
            overlaps_ignored_block(config, html, match) is False
            and inside_ignored_rule(config, html, match, rule["name"]) is False
            and inside_ignored_linter_block(config, html, match) is False
        ):
            errors.append(
                {
                    "code": rule["name"],
                    "line": get_line(match.start(), line_ends),
                    "match": match.group().strip()[:20],
                    "message": rule["message"],
                }
            )
    return errors
