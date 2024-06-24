"""Test html dd tag.

poetry run pytest tests/test_html/test_tag_dd.py
"""

import pytest

from src.djlint.reformat import formatter
from tests.conftest import printer

test_data = [
    pytest.param(
        ("<dd>text</dd>"),
        ("<dd>\n" "    text\n" "</dd>\n"),
        id="dd_tag",
    ),
]


@pytest.mark.parametrize(("source", "expected"), test_data)
def test_base(source, expected, basic_config):
    output = formatter(basic_config, source)

    printer(expected, source, output)
    assert expected == output
