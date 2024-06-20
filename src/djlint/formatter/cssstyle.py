"""Format attributes."""

import hashlib

import regex as re

from ..settings import Config

style_pattern = re.compile(r'style="([^"]*)"')
class_pattern = re.compile(r'class="([^"]*)"')


def add_css_classes(config: Config, css_classes: list = [], inline_styles: str = "") -> list:
    """Add CSS classes.

    Args:
    ----
        config (Config): The configuration object.
        css_classes (list, optional): The list of CSS classes. Defaults to [].
        inline_styles (str, optional): The inline styles. Defaults to "".
        this_file (str, optional): The current file. Defaults to "".

    Returns:
    -------
        str: The updated list of CSS classes.

    """
    class_name = next(
        (cls for cls, styles in config.css_rules.items() if styles == inline_styles),
        None,
    )
    if not class_name:
        rnd = hashlib.shake_256(str(inline_styles).encode()).hexdigest(5)
        class_name = f"class-{rnd}-{config.counter}"
        config.css_rules[class_name] = inline_styles
    css_classes.append(class_name)
    config.counter += 1
    return css_classes


def clean_inline_style_to_css_class(config: Config, html: str) -> str:
    """Format CSS style.

    Args:
    ----
        config (Config): The configuration object.
        html (str): The HTML string.
        this_file: The current file.

    Returns:
    -------
        str: The formatted HTML string.

    """
    matches = style_pattern.findall(html)
    css_class = [css.split() for css in class_pattern.findall(html)]
    flattened_class_list = [item for sublist in css_class for item in sublist]
    css_classes = []
    for match in matches:
        if "'" in match:
            attrib_value = match.strip("'")
        elif '"' in match:
            attrib_value = match.strip('"')
        else:
            attrib_value = match
        css_classes = add_css_classes(
            config=config,
            css_classes=flattened_class_list or [],
            inline_styles=attrib_value,
        )
        config.counter += 1

    html = re.sub(r'style="[^"]*"', '', html)
    if css_classes:
        new_class_str = 'class="' + " ".join(list(set(css_classes))) + '"'
        html= add_or_update_class(html, new_class_str)
    create_css_file(config)
    return html


def add_or_update_class(html: str, new_class_str: str) -> str:
    """Add or update class attribute.

    Args:
    ----
        html (str): The HTML string.
        new_class_str (str): The new class string.

    Returns:
    -------
        str: The formatted HTML string.

    """
    if re.search(class_pattern, html):
        updated_html = re.sub(class_pattern, new_class_str, html)
    else:
        updated_html = re.sub(r"(<\w+)", r"\1 " + new_class_str, html, 1)

    return updated_html


def create_css_file(config: Config) -> None:
    """Create CSS file.

    Args:
    ----
        config (Config): The configuration object.

    """
    with open(config.css_file_path, "a+") as f:
        for class_name, styles in config.css_rules.items():
            f.write(f".{class_name} {{{styles}}}\n")
