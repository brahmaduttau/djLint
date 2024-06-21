"""Djlint reformat html files.

Much code is borrowed from https://github.com/rareyman/HTMLBeautify, many thanks!
"""

import difflib
from pathlib import Path

from .formatter.compress import compress_html
from .formatter.condense import clean_whitespace, condense_html
from .formatter.css import format_css
from .formatter.expand import expand_html
from .formatter.htmlentities import replace_html_escaped_entities
from .formatter.indent import indent_html
from .formatter.js import format_js
from .formatter.siglequotes import clean_single_quotes
from .settings import Config


def formatter(config: Config, rawcode: str,this_file:Path) -> str:
    """Format a html string."""
    if not rawcode:
        return rawcode

    # naturalize the line breaks
    compressed = compress_html(("\n").join(rawcode.splitlines()), config)

    expanded = expand_html(compressed, config)

    htmlcontent = replace_html_escaped_entities(expanded, config)

    condensed = clean_whitespace(htmlcontent, config)

    cleaned_quoted_code = clean_single_quotes(condensed, config)

    indented_code = indent_html(cleaned_quoted_code, config,this_file=this_file)

    beautified_code = condense_html(indented_code, config)

    if config.format_css:
        beautified_code = format_css(beautified_code, config)

    if config.format_js:
        beautified_code = format_js(beautified_code, config)

    # preserve original line endings
    line_ending = rawcode.find("\n")
    if line_ending > -1 and rawcode[max(line_ending - 1, 0)] == "\r":
        # convert \r?\n to \r\n
        beautified_code = beautified_code.replace("\r", "").replace("\n", "\r\n")

    return beautified_code


def reformat_file(config: Config, this_file: Path) -> dict:
    """Reformat html file."""
    rawcode = this_file.read_bytes().decode("utf8")

    beautified_code = formatter(config, rawcode,this_file=this_file)

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
