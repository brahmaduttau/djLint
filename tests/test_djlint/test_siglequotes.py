
"""Module containing unit tests for the clean_single_quotes function."""

from src.djlint.formatter.singlequotes import clean_single_quotes
from src.djlint.settings import Config


def test_clean_single_quotes():
    html = "<div class='container'>Hello, World!</div>"
    expected_output = '<div class="container">Hello, World!</div>'
    config = Config()

    result = clean_single_quotes(html, config)

    assert result == expected_output
