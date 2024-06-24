"""Tests for Aurelia.

poetry run pytest tests/test_html/test_aurelia.py
"""

import pytest

from src.djlint.reformat import formatter
from tests.conftest import printer

test_data = [
    pytest.param(
        ("<template>\n" '    <i class.bind="icon"></i>\n' "</template>\n"),
        ("<template>\n" '    <i class.bind="icon"></i>\n' "</template>\n"),
        id="aurelia",
    ),
]


@pytest.mark.parametrize(("source", "expected"), test_data)
def test_base(source, expected, basic_config):
    output = formatter(basic_config, source)

    printer(expected, source, output)
    assert expected == output
