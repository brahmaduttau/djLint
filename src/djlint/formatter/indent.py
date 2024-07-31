"""djLint add indentation to html."""

from __future__ import annotations

import re
from functools import partial
from typing import Any, Literal

import json5 as json

from djlint.formatter.attributes import format_attributes
from djlint.formatter.cssstyle import clean_inline_style_to_css_class
from djlint.helpers import (
    inside_ignored_block,
    is_ignored_block_closing,
    is_ignored_block_opening,
    is_safe_closing_tag,
    is_script_style_block_closing,
    is_script_style_block_opening,
)


def setup_indentation(rawcode: str, config) -> tuple[list[str | Any], str]:
    """
    Setup initial variables for indentation.

    Args:
        rawcode (str): The raw code to be formatted.
        config (Config): The configuration object containing formatting options.

    Returns:
        tuple: A tuple containing the flat list of lines in the raw code and the indentation string.
    """
    rawcode_flat_list = re.split(pattern="\n", string=rawcode)
    indent = config.indent
    return rawcode_flat_list, indent


def indent_except_handlebars_golang(rawcode: str, config) -> str:
    """
    Indents the given raw code, except for handlebars, according to the provided configuration.

    Args:
        rawcode (str): The raw code to be indented.
        config (Config): The configuration object containing the formatting rules.

    Returns:
        str: The indented code.

    """

    # we can try to fix template tags. ignore handlebars
    # this should be done before indenting to line length
    # calc is preserved.
    def fix_tag_spacing(html: str, match: re.Match) -> str:
        if inside_ignored_block(config=config, html=html, match=match):
            return match.group()

        return f"{match.group(1)} {match.group(2)} {match.group(3)}"

    """
    We should have tags like this:
    {{ tag }}
    {%- tag atrib -%}
    """
    func = partial(fix_tag_spacing, rawcode)

    rawcode = re.sub(
        pattern=r"({%-?\+?)[ ]*?(\w(?:(?!%}).)*?)[ ]*?(\+?-?%})",
        repl=func,
        string=rawcode,
    )
    rawcode = re.sub(
        pattern=r"({{)[ ]*?(\w(?:(?!}}).)*?)[ ]*?(\+?-?}})", repl=func, string=rawcode
    )
    return rawcode


def indent_handlebars(rawcode, config) -> str:
    """
    Applies indentation fixes to handlebars templates in the given rawcode.

    Args:
        rawcode (str): The raw code containing handlebars templates.
        config: The configuration object.

    Returns:
        str: The modified rawcode with indentation fixes applied to handlebars templates.
    """

    def fix_handlebars_template_tags(html: str, match: re.Match) -> str:
        if inside_ignored_block(config=config, html=html, match=match):
            return match.group()

        return f"{match.group(1)} {match.group(2)}"

    func = partial(fix_handlebars_template_tags, rawcode)
    # handlebars templates
    rawcode = re.sub(pattern=r"({{#(?:each|if).+?[^ ])(}})", repl=func, string=rawcode)
    return rawcode


def compile_html_regex(
    slt_html, slt_template, always_self_closing_html, ignored_inline_blocks
) -> re.Pattern[str]:
    """
    Compiles a regex pattern for matching specific HTML structures.

    :param slt_html: Tags that should be treated as single-line tags for HTML.
    :param slt_template: Template tags to be considered.
    :param always_self_closing_html: Tags that are always self-closing.
    :param ignored_inline_blocks: Blocks to be ignored in the regex.
    :return: Compiled regex object.
    """
    pattern = rf"""^(?:[^<\s].*?)? # start of a line, optionally with some text
                    (?:
                        (?:<({slt_html})>)(?:.*?)(?:</(?:\1)>) # <span>stuff</span> >>>> match 1
                       |(?:<({slt_html})\b[^>]+?>)(?:.*?)(?:</(?:\2)>) # <span stuff>stuff</span> >>> match 2
                       |(?:<(?:{always_self_closing_html})\b[^>]*?/?>) # <img stuff />
                       |(?:<(?:{slt_html})\b[^>]*?/>) # <img />
                       |(?:{{%[ ]*?({slt_template})[ ]+?.*?%}})(?:.*?)(?:{{%[ ]+?end(?:\3)[ ]+?.*?%}}) # >>> match 3
                       |{ignored_inline_blocks}
                    )[ \t]*?
                    (?:
                    .*? # anything
                    (?: # followed by another slt
                        (?:<({slt_html})>)(?:.*?)(?:</(?:\4)>) # <span>stuff</span> >>>> match 1
                       |(?:<({slt_html})\b[^>]+?>)(?:.*?)(?:</(?:\5)>) # <span stuff>stuff</span> >>> match 2
                       |(?:<(?:{always_self_closing_html})\b[^>]*?/?>) # <img stuff />
                       |(?:<(?:{slt_html})\b[^>]*?/>) # <img />
                       |(?:{{%[ ]*?({slt_template})[ ]+?.*?%}})(?:.*?)(?:{{%[ ]+?end(?:\6)[ ]+?.*?%}}) # >>> match 3
                       |{ignored_inline_blocks}
                    )[ \t]*?
                    )*? # optional of course
                    [^<]*?$ # with no other tags following until end of line
                """
    return re.compile(
        pattern=pattern,
        flags=re.IGNORECASE | re.VERBOSE | re.MULTILINE,
    )


def should_indent(
    item,
    is_block_raw,
    slt_html,
    slt_template,
    always_self_closing_html,
    config,
) -> list[Any] | bool:
    """
    Checks if the item matches the specified HTML regex and is not a raw block,
    then indents the item accordingly.

    :param item: The string item to check and possibly indent.
    :param is_block_raw: Boolean indicating if the current block is raw.
    :param indent: The string used for indentation (e.g., spaces or tabs).
    :param indent_level: The current indentation level.
    :param slt_html: Tags that should be treated as single-line tags for HTML.
    :param slt_template: Template tags to be considered.
    :param always_self_closing_html: Tags that are always self-closing.
    :param ignored_inline_blocks: Blocks to be ignored in the regex.
    :param config: Configuration object containing settings.
    :return: The possibly indented item.
    """
    compiled_regex = compile_html_regex(
        slt_html=slt_html,
        slt_template=slt_template,
        always_self_closing_html=always_self_closing_html,
        ignored_inline_blocks=config.ignored_inline_blocks,
    )
    return re.findall(pattern=compiled_regex, string=item) and not is_block_raw


def check_formatting_conditions(item, is_block_raw, in_set_tag, config) -> bool:
    """
    Checks if the item should be formatted based on the provided conditions.

    :param item: The string item to check.
    :param is_block_raw: Boolean indicating if the current block is raw.
    :param in_set_tag: Boolean indicating if we are inside a set tag.
    :param config: Configuration object containing settings.
    :return: True if the item meets all conditions for formatting, False otherwise.
    """
    if (
        config.no_set_formatting is False
        and re.search(
            pattern=re.compile(
                pattern=r"^(?!.*\{\%).*%\}.*$",
                flags=re.IGNORECASE | re.MULTILINE | re.VERBOSE,
            ),
            string=item,
        )
        and is_block_raw is False
        and in_set_tag is True
    ):
        return True
    else:
        return False


def check_closing_conditions(
    item, is_block_raw, in_set_tag, config
) -> Any | Literal[False] | None:
    """
    Checks if the item should be formatted based on the provided conditions.

    :param item: The string item to check.
    :param is_block_raw: Boolean indicating if the current block is raw.
    :param in_set_tag: Boolean indicating if we are inside a set tag.
    :param config: Configuration object containing settings.
    :return: True if the item meets all conditions for formatting, False otherwise.
    """
    pattern = re.compile(
        pattern=r"^[ ]*}|^[ ]*]", flags=re.IGNORECASE | re.MULTILINE | re.VERBOSE
    )
    return (
        not config.no_set_formatting
        and re.search(pattern=pattern, string=item)
        and not is_block_raw
        and in_set_tag
    )


def check_item_conditions(
    config, item, is_block_raw, is_safe_closing_tag, slt_html
) -> Any | bool:
    """
    Checks if the item meets specific conditions based on the configuration,
    whether it's a raw block, if it's a safe closing tag, and specific HTML patterns.

    :param config: Configuration object containing settings and patterns.
    :param item: The string item to check.
    :param is_block_raw: Boolean indicating if the current block is raw.
    :param is_safe_closing_tag: Function to check if the item is a safe closing tag.
    :param slt_html: String containing HTML tags to check in the item.
    :return: True if the item meets all conditions for processing, False otherwise.
    """
    tag_unindent_search = re.search(
        config.tag_unindent,
        item,
        re.IGNORECASE | re.MULTILINE | re.VERBOSE,
    )
    slt_pattern_1 = rf"(<({slt_html})>)(.*?)(</(\2)>[^<]*?$)"
    slt_pattern_2 = rf"(<({slt_html})\b[^>]+?>)(.*?)(</(\2)>[^<]*?$)"

    return (
        tag_unindent_search
        and not is_block_raw
        and not is_safe_closing_tag(config, item)
        and not re.findall(
            pattern=slt_pattern_1,
            string=item,
            flags=re.IGNORECASE | re.VERBOSE | re.MULTILINE,
        )
        and not re.findall(
            pattern=slt_pattern_2,
            string=item,
            flags=re.IGNORECASE | re.VERBOSE | re.MULTILINE,
        )
    )


def check_html_tags(item, slt_html):
    """
    Checks if the item contains specific HTML tags defined in slt_html.

    :param item: The string item to check.
    :param slt_html: String containing HTML tags to check in the item.
    :return: True if the item contains any of the specified HTML tags, False otherwise.
    """
    pattern1 = rf"(^<({slt_html})>)(.*?)(</(\2)>)"
    pattern2 = rf"(^<({slt_html})\b[^>]+?>)(.*?)(</(\2)>)"

    # Find all occurrences based on both patterns
    matches = re.findall(
        pattern=pattern1, string=item, flags=re.IGNORECASE | re.VERBOSE | re.MULTILINE
    ) or re.findall(
        pattern=re.compile(
            pattern=pattern2, flags=re.IGNORECASE | re.VERBOSE | re.MULTILINE
        ),
        string=item,
    )

    return len(matches) > 0


def check_unindent_condition(config, item, is_block_raw) -> bool:
    """
    Checks if the item matches the unindent line pattern from the config
    and if the block is not raw.

    :param config: Configuration object containing the unindent line pattern.
    :param item: The string item to check.
    :param is_block_raw: Boolean indicating if the current block is raw.
    :return: True if the item matches the unindent pattern and the block is not raw, False otherwise.
    """
    pattern = r"^" + str(config.tag_unindent_line)
    match = re.search(
        pattern=pattern, string=item, flags=re.IGNORECASE | re.MULTILINE | re.VERBOSE
    )
    return match is not None and not is_block_raw


def check_set_formatting_condition(
    config, item, is_block_raw, in_set_tag
) -> None | bool:
    """
    Checks if the item should be formatted based on the 'set' tag conditions,
    considering the configuration and the state of the block and tag.

    :param config: Configuration object containing settings.
    :param item: The string item to check.
    :param is_block_raw: Boolean indicating if the current block is raw.
    :param in_set_tag: Boolean indicating if we are inside a set tag.
    :return: True if the item meets all conditions for formatting, False otherwise.
    """
    pattern = r"^([ ]*{%[ ]*?set)(?!.*%}).*$"
    return (
        not config.no_set_formatting
        and re.search(
            pattern=re.compile(
                pattern=pattern, flags=re.IGNORECASE | re.MULTILINE | re.VERBOSE
            ),
            string=item,
        )
        and not is_block_raw
        and not in_set_tag
    )


def check_complex_condition(
    config, item, is_block_raw, in_set_tag
) -> Any | Literal[False] | None:
    """
    Checks if the item meets a complex set of conditions involving configuration settings,
    regular expression search, and boolean flags.

    :param config: Configuration object containing settings.
    :param item: The string item to check.
    :param is_block_raw: Boolean indicating if the current block is raw.
    :param in_set_tag: Boolean indicating if we are inside a set tag.
    :return: True if all conditions are met, False otherwise.
    """
    pattern = r"(\{(?![^{}]*%[}\s])(?=[^{}]*$)|\[(?=[^\]]*$))"
    return (
        not config.no_set_formatting
        and re.search(
            pattern=re.compile(
                pattern=pattern, flags=re.IGNORECASE | re.MULTILINE | re.VERBOSE
            ),
            string=item,
        )
        and not is_block_raw
        and in_set_tag
    )


def check_indent_condition(config, item, is_block_raw) -> bool:
    """
    Checks if the item matches the indentation pattern from the config
    and if the block is not raw.

    :param config: Configuration object containing the indentation pattern.
    :param item: The string item to check.
    :param is_block_raw: Boolean indicating if the current block is raw.
    :return: True if the item matches the indentation pattern and the block is not raw, False otherwise.
    """
    pattern = r"^(?:" + str(config.tag_indent) + r")"
    return (
        re.search(
            pattern=re.compile(
                pattern=pattern, flags=re.IGNORECASE | re.MULTILINE | re.VERBOSE
            ),
            string=item,
        )
        is not None
        and not is_block_raw
    )


def apply_indentation_substitution(config, tmp, func) -> str:
    """
    Applies a regular expression substitution to a given string (tmp) using a function (func)
    for each match. The substitution targets HTML tags specified in the config.indent_html_tags
    with specific patterns within the tags.

    :param config: Configuration object containing indent_html_tags specifying which HTML tags to target.
    :param tmp: The string to perform the substitution on.
    :param func: The function to apply to each match. It takes a match object and returns a string.
    :return: The modified string after applying the substitution.
    """
    pattern = rf"(\s*?)(<(?:{config.indent_html_tags})\b)((?:\"[^\"]*\"|'[^']*'|{{[^}}]*}}|[^'\">{{}}\/])+?)(\s?/?>)"
    return re.sub(
        pattern=re.compile(pattern=pattern, flags=re.VERBOSE | re.IGNORECASE),
        repl=func,
        string=tmp,
    )


def apply_set_tag_substitution(beautified_code, func) -> str:
    """
    Applies a regular expression substitution to a given string (beautified_code) using a function (func)
    for each match. The substitution targets Jinja2 'set' tags, adjusting their formatting.

    :param beautified_code: The string to perform the substitution on, typically the code to be beautified.
    :param func: The function to apply to each match. It takes a match object and returns a string.
    :return: The modified string after applying the substitution.
    """
    pattern = r"([ ]*)({%-?)[ ]*(set)[ ]+?((?:(?!%}).)*?)(-?%})"
    return re.sub(
        pattern=re.compile(
            pattern=pattern, flags=re.IGNORECASE | re.MULTILINE | re.VERBOSE | re.DOTALL
        ),
        repl=func,
        string=beautified_code,
    )


def apply_custom_substitution(beautified_code, func) -> str:
    """
    Applies a regular expression substitution to a given string (beautified_code) using a function (func)
    for each match. The substitution targets a specific pattern involving Jinja2 template expressions.

    :param beautified_code: The string to perform the substitution on, typically the code to be beautified.
    :param func: The function to apply to each match. It takes a match object and returns a string.
    :return: The modified string after applying the substitution.
    """
    pattern = r"([ ]*)({{-?\+?)[ ]*?((?:(?!}}).)*?\w)(\((?:\"[^\"]*\"|'[^']*'|[^\)])*?\)[ ]*)((?:\[[^\]]*?\]|\.[^\s]+)[ ]*)?((?:(?!}}).)*?-?\+?}})"
    return re.sub(
        pattern=re.compile(
            pattern=pattern, flags=re.IGNORECASE | re.MULTILINE | re.VERBOSE | re.DOTALL
        ),
        repl=func,
        string=beautified_code,
    )


# try to fix internal formatting of set tag
def format_data(config, contents: str, tag_size: int, leading_space) -> str:
    """
    Format the given contents based on the provided configuration.

    Args:
        config: The configuration object containing formatting options.
        contents (str): The contents to be formatted.
        tag_size (int): The size of the tag.
        leading_space: The leading space to be added to each line.

    Returns:
        str: The formatted contents.

    Raises:
        None

    """
    try:
        # try to format the contents as json
        data = json.loads(contents)
        contents = json.dumps(
            data, trailing_commas=False, ensure_ascii=False, quote_keys=True
        )

        if tag_size + len(contents) >= config.max_line_length:
            # if the line is too long we can indent the json
            contents = json.dumps(
                data,
                indent=config.indent_size,
                trailing_commas=False,
                ensure_ascii=False,
                quote_keys=True,
            )

    except Exception as e:
        # was not json.. try to eval as set
        print(e)
        try:
            # if contents is a python keyword, do not evaluate it.
            evaluated = str(eval(contents)) if contents not in ["object"] else contents
            # need to unwrap the eval
            contents = (
                evaluated[1:-1]
                if contents[:1] != "(" and evaluated[:1] == "("
                else evaluated
            )
        except Exception as e:
            print(e)
            contents = contents.strip()

    return (f"\n{leading_space}").join(contents.splitlines())


def format_set(config, html: str, match: re.Match) -> str:
    """
    Formats a set tag in the HTML code.

    Args:
        config: The configuration settings.
        html: The HTML code.
        match: The regular expression match object.

    Returns:
        The formatted set tag.

    """
    if inside_ignored_block(config=config, html=html, match=match):
        return match.group()

    leading_space = match.group(1)
    open_bracket = match.group(2)
    tag = match.group(3)
    close_bracket = match.group(5)
    contents = match.group(4).strip()
    contents_split = contents.split("=", 1)

    if len(contents_split) > 1:
        contents = (
            contents_split[0].strip()
            + " = "
            + format_data(
                config=config,
                contents=contents_split[-1],
                tag_size=len(f"{open_bracket} {tag}  {close_bracket}"),
                leading_space=leading_space,
            )
        )

    return f"{leading_space}{open_bracket} {tag} {contents} {close_bracket}"


def format_function(config, html: str, match: re.Match) -> str:
    """
    Format a function call in HTML code.

    Args:
        config (dict): The configuration settings.
        html (str): The HTML code.
        match (re.Match): The regular expression match object.

    Returns:
        str: The formatted function call.

    """
    if inside_ignored_block(config=config, html=html, match=match):
        return match.group()

    leading_space = match.group(1)
    open_bracket = match.group(2)
    tag = match.group(3).strip()
    index = (match.group(5) or "").strip()
    close_bracket = match.group(6)
    contents = format_data(
        config=config,
        contents=match.group(4).strip()[1:-1],
        tag_size=len(f"{open_bracket} {tag}() {close_bracket}"),
        leading_space=leading_space,
    )

    return f"{leading_space}{open_bracket} {tag}({contents}){index} {close_bracket}"


def process_indentation(rawcode_flat_list, indent, config) -> Any:
    """
    Processes the indentation of the given raw code.

    Args:
        rawcode_flat_list (list[str]): The list of raw code lines.
        indent (str): The string used for indentation.
        config (Config): The configuration object.

    Returns:
        str: The beautified code with proper indentation.
    """

    beautified_code = ""
    indent_level = 0
    in_set_tag = False
    is_raw_first_line = False
    in_script_style_tag = False
    is_block_raw = False

    slt_html = config.indent_html_tags

    # here using all tags cause we allow empty tags on one line
    always_self_closing_html = config.always_self_closing_html_tags

    # here using all tags cause we allow empty tags on one line
    slt_template = config.optional_single_line_template_tags

    # nested ignored blocks..
    ignored_level = 0

    for item in rawcode_flat_list:
        # if a raw tag first line
        if not is_block_raw and is_ignored_block_opening(config=config, item=item):
            is_raw_first_line = True

        # if a raw tag then start ignoring
        if is_ignored_block_opening(config=config, item=item):
            is_block_raw = True
            ignored_level += 1

        if is_script_style_block_opening(config=config, item=item):
            in_script_style_tag = True

        if is_safe_closing_tag(config=config, item=item):
            ignored_level -= 1
            ignored_level = max(ignored_level, 0)
            if is_block_raw is True and ignored_level == 0:
                is_block_raw = False

        if (
            re.findall(
                rf"^\s*?(?:{config.ignored_inline_blocks})",
                item,
                flags=re.IGNORECASE | re.VERBOSE | re.MULTILINE,
            )
            and is_block_raw is False
        ):
            tmp = (indent * indent_level) + item + "\n"

        # if a one-line, inline tag, just process it, only if line starts w/ it
        # or if it is trailing text

        elif should_indent(
            item=item,
            is_block_raw=is_block_raw,
            slt_html=slt_html,
            slt_template=slt_template,
            always_self_closing_html=always_self_closing_html,
            config=config,
        ):
            tmp = (indent * indent_level) + item + "\n"

        # closing set tag
        elif check_formatting_conditions(
            item=item, is_block_raw=is_block_raw, in_set_tag=in_set_tag, config=config
        ):
            indent_level = max(indent_level - 1, 0)
            in_set_tag = False
            tmp = (indent * indent_level) + item + "\n"

        # closing curly brace inside a set tag
        elif check_closing_conditions(
            item=item, is_block_raw=is_block_raw, in_set_tag=in_set_tag, config=config
        ):
            indent_level = max(indent_level - 1, 0)
            tmp = (indent * indent_level) + item + "\n"

        # if unindent, move left
        elif check_item_conditions(
            item=item,
            is_block_raw=is_block_raw,
            is_safe_closing_tag=is_safe_closing_tag,
            slt_html=slt_html,
            config=config,
        ):
            # block to catch inline block followed by a non-break tag
            if check_html_tags(item=item, slt_html=slt_html):
                # unindent after instead of before
                tmp = (indent * indent_level) + item + "\n"
                indent_level = max(indent_level - 1, 0)
            else:
                indent_level = max(indent_level - 1, 0)
                tmp = (indent * indent_level) + item + "\n"

        elif check_unindent_condition(
            config=config, item=item, is_block_raw=is_block_raw
        ):
            tmp = (indent * (indent_level - 1)) + item + "\n"
        # if indent, move right
        # opening set tag
        elif check_set_formatting_condition(
            config=config, item=item, is_block_raw=is_block_raw, in_set_tag=in_set_tag
        ):
            tmp = (indent * indent_level) + item + "\n"
            indent_level = indent_level + 1
            in_set_tag = True
        # opening curly brace inside a set tag
        elif check_complex_condition(
            config=config, item=item, is_block_raw=is_block_raw, in_set_tag=in_set_tag
        ):
            tmp = (indent * indent_level) + item + "\n"
            indent_level = indent_level + 1

        elif check_indent_condition(
            config=config, item=item, is_block_raw=is_block_raw
        ):
            tmp = (indent * indent_level) + item + "\n"
            indent_level = indent_level + 1

        elif is_raw_first_line is True or (
            is_safe_closing_tag(config=config, item=item) and is_block_raw is False
        ):
            tmp = (indent * indent_level) + item + "\n"

        elif is_block_raw is True or not item.strip():
            tmp = item + "\n"

        # otherwise, just leave same level
        elif not config.preserve_leading_space:
            # if we are not trying to preserve indenting
            # on text, the add it now.
            tmp = (indent * indent_level) + item + "\n"
        else:
            tmp = item + "\n"

        # if a opening raw tag then start ignoring.. only if there is no closing tag
        # on the same line
        if is_ignored_block_opening(config=config, item=item):
            is_block_raw = True
            is_raw_first_line = False

        # if a normal tag, we can try to expand attributes
        elif is_block_raw is False:
            # get leading space, and attributes
            func = partial(format_attributes, config, item)
            tmp = apply_indentation_substitution(config=config, tmp=tmp, func=func)

        tmp = clean_inline_style_to_css_class(config=config, html=tmp)

        # turn off raw block if we hit end - for one line raw blocks, but not an inline raw
        if is_ignored_block_closing(config=config, item=item) and (
            in_script_style_tag is False
            or (
                in_script_style_tag
                and is_script_style_block_closing(config=config, item=item)
            )
        ):
            in_script_style_tag = False
            if not is_safe_closing_tag(config=config, item=item):
                ignored_level -= 1
                ignored_level = max(ignored_level, 0)
            if ignored_level == 0:
                is_block_raw = False

        beautified_code = beautified_code + tmp

    if config.no_set_formatting is False:
        func = partial(format_set, config, beautified_code)
        # format set contents
        beautified_code = apply_set_tag_substitution(
            beautified_code=beautified_code, func=func
        )
    if config.no_function_formatting is False:
        func = partial(format_function, config, beautified_code)
        # format function contents
        beautified_code = apply_custom_substitution(
            beautified_code=beautified_code, func=func
        )

    if not config.preserve_blank_lines:
        beautified_code = beautified_code.lstrip()

    return beautified_code.rstrip() + "\n"


def indent_html(rawcode: str, config) -> str:
    """
    Indents the HTML code according to the specified configuration.

    Args:
        rawcode (str): The raw HTML code to be indented.
        config: The configuration object containing the indentation settings.

    Returns:
        str: The indented HTML code.
    """
    if config.profile not in ["handlebars", "golang"]:
        rawcode = indent_except_handlebars_golang(rawcode=rawcode, config=config)
    elif config.profile == "handlebars":
        rawcode = indent_handlebars(rawcode=rawcode, config=config)

    rawcode_flat_list, indent = setup_indentation(rawcode=rawcode, config=config)
    beautified_code = process_indentation(
        rawcode_flat_list=rawcode_flat_list, indent=indent, config=config
    )

    return beautified_code
