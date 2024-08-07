"""Djlint reformat html files.

Much code is borrowed from https://github.com/rareyman/HTMLBeautify, many thanks!
"""

import difflib
from pathlib import Path

from djlint.formatter.attributes import (
    ensure_double_quoted_attributes,
    normalize_whitespace_in_template_tags,
    replace_encoded_entities,
)
from djlint.formatter.compress import compress_html
from djlint.formatter.condense import clean_whitespace, condense_html
from djlint.formatter.css import format_css
from djlint.formatter.expand import expand_html
from djlint.formatter.indent import indent_html
from djlint.formatter.js import format_js
from djlint.settings import Config


def formatter(config: Config, rawcode: str) -> str:
    """Format a html string."""
    if not rawcode:
        return rawcode

    # naturalize the line breaks
    compressed = compress_html(("\n").join(rawcode.splitlines()), config)

    html_entities = replace_encoded_entities(html=compressed, config=config)

    expanded = expand_html(html_entities, config)

    condensed = clean_whitespace(expanded, config)

    indented_code = indent_html(condensed, config)

    beautified_code = condense_html(indented_code, config)

    if config.format_css:
        beautified_code = format_css(beautified_code, config)

    if config.format_js:
        beautified_code = format_js(beautified_code, config)
    beautified_code = ensure_double_quoted_attributes(beautified_code)
    beautified_code = normalize_whitespace_in_template_tags(beautified_code)
    # preserve original line endings
    line_ending = rawcode.find("\n")
    if line_ending > -1 and rawcode[max(line_ending - 1, 0)] == "\r":
        # convert \r?\n to \r\n
        beautified_code = beautified_code.replace("\r", "").replace("\n", "\r\n")

    return beautified_code


def reformat_file(config: Config, this_file: Path) -> dict:
    """Reformat html file."""
    rawcode = this_file.read_bytes().decode("utf8")

    beautified_code = formatter(config, rawcode)

    if (
        config.check is not True and beautified_code != rawcode
    ) or config.stdin is True:
        this_file.write_bytes(beautified_code.encode("utf8"))

    out = {
        str(this_file): list(
            difflib.unified_diff(rawcode.splitlines(), beautified_code.splitlines())
        )
    }
    return out
