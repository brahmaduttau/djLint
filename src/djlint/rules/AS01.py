"""Validate accessibility of HTML content."""

from typing import Any, Dict, List

from bs4 import BeautifulSoup
from joblib import Memory
from py_w3c.validators.html.validator import HTMLValidator

from djlint.settings import Config

location = "./cachedir"
memory = Memory(location, verbose=0)


class AccessibilityError(Exception):
    """Exception raised for accessibility errors."""


def check_alt_att_on_img(html: str):
    """Check if the 'alt' attribute is present and not empty on image tags in the HTML.

    Args:
    ----
        html (str): The HTML content to be checked.

    Returns:
    -------
        list: A list of accessibility exceptions found.

    """
    exceptions_list = []
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all("img"):
        if not tag.has_attr("alt"):
            exceptions_list.append(
                AccessibilityError(
                    "AccessibilityError",
                    tag,
                    "Missing alt attribute on tag image",
                    tag.sourceline,
                    tag.sourcepos,
                )
            )
        elif tag["alt"] == "":
            exceptions_list.append(
                AccessibilityError(
                    "AccessibilityError",
                    tag,
                    "Empty alt description",
                    tag.sourceline,
                    tag.sourcepos,
                )
            )
    return exceptions_list


def check_for_h1(html: str):
    """Check if the HTML contains the header tag H1.

    Args:
    ----
        html (str): The HTML content to be checked.

    Returns:
    -------
        list: A list of accessibility exceptions found.

    """
    exceptions_list = []
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("h1")
    if tag is None:
        exceptions_list.append(
            AccessibilityError(
                "AccessibilityError", "", "Missing header tag H1 on document", "", ""
            )
        )
    return exceptions_list


def check_hs_hierarchy(html: str):
    """Check if the HTML contains the header tag H1.

    Args:
    ----
        html (str): The HTML content to be checked.

    Returns:
    -------
        list: A list of accessibility exceptions found.

    """
    exceptions_list = []

    head_tags = {
        "h1": False,
        "h2": False,
        "h3": False,
        "h4": False,
        "h5": False,
        "h6": False,
    }
    existing_tags = []

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(True):
        if tag.name in head_tags and not any(
            tag.name in name for name in existing_tags
        ):
            existing_tags.append((tag.name, tag))

    for name, code_fragment in existing_tags:
        head_tags[name] = True
        for value in head_tags:
            if value != name:
                if head_tags[value] is False:
                    exceptions_list.append(
                        AccessibilityError(
                            "AccessibilityError",
                            code_fragment,
                            f"Suspected hierarchical order, consider reviewing it, Tag {name} appeared first even without the existence of the {value} tag",
                            code_fragment.sourceline,
                            code_fragment.sourcepos,
                        )
                    )
            else:
                break

    return exceptions_list


def validate_html(html: str):
    """Check if the HTML contains the header tag H1.

    Args:
    ----
        html (str): The HTML content to be checked.

    Returns:
    -------
        list: A list of accessibility exceptions found.

    """
    vld = HTMLValidator()
    vld.validate_fragment(str(html))
    exceptions_list = []

    for error in vld.errors:
        exceptions_list.append(
            AccessibilityError(
                "StaticHTMLValidation",
                error["extract"].replace("\n", ""),
                error["message"],
                error["hiliteStart"],
                error["hiliteLength"],
            )
        )
    return exceptions_list


def map_functions():
    """Check if the HTML contains the header tag H1.

    Args:
    ----
        html (str): The HTML content to be checked.

    Returns:
    -------
        list: A list of accessibility exceptions found.

    """
    validate_html_cached = memory.cache(validate_html)
    functions = {
        "alt_att_check": check_alt_att_on_img,
        "contains_h1": check_for_h1,
        "headers_tag_hierarchy": check_hs_hierarchy,
        "static_validation_html": validate_html_cached,
    }
    return functions


def check_accessibility(html: str, exclude=()):
    """Check if the HTML contains the header tag H1.

    Args:
    ----
        html (str): The HTML content to be checked.
        exclude (tuple): A tuple of function names to exclude from the accessibility check.

    Returns:
    -------
        list: A list of accessibility exceptions found.

    """
    functions_to_check = [
        fn for name, fn in map_functions().items() if name not in exclude
    ]
    exceptions = []
    for func in functions_to_check:
        exceptions.extend(func(html))
    if exceptions:
        return exceptions


def run(
    rule: Dict[str, Any],
    config: Config,
    html: str,
    filepath: str,
    line_ends: List[Dict[str, int]],
    *args: Any,
    **kwargs: Any,
) -> List[Dict[str, str]]:
    """Check for orphans html tags."""
    errors: List[Dict[str, str]] = []

    acc_errors: list[AccessibilityError] = check_accessibility(html, exclude=())
    errors = []
    for err in acc_errors:
        errors.append(
            {
                "code": rule["name"],
                "line": err.message,
                "match": err.code_fragment,
                "message": rule["message"],
            }
        )
