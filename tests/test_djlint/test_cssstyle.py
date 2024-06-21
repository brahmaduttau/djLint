"""Module containing tests for the cssstyle formatter."""

import pytest

from src.djlint.formatter.cssstyle import (
    add_css_classes,
    add_or_update_class,
    clean_inline_style_to_css_class,
    create_css_file,
    remove_duplicate_classes,
)


@pytest.fixture()
def config():
    class Config:
        def __init__(self):
            self.css_rules = {}
            self.counter = 0
            self.css_file_path = "test.css"
    return Config()

def test_add_css_classes(config):
    css_classes = ["class1", "class2"]
    inline_styles = "color: red;"
    this_file = "test.html"
    expected = ["class1", "class2", "random-0"]

    result = add_css_classes(config, css_classes, inline_styles, this_file)

    assert result == expected
    assert config.css_rules["random-0"] == "color: red;"
    assert config.counter == 1

def test_clean_inline_style_to_css_class(config):
    html = '<div style="color: red;">'
    this_file = "test.html"
    expected = '<div class="random-0">'

    result = clean_inline_style_to_css_class(config, html, this_file)

    assert result == expected
    assert config.css_rules["random-0"] == "color: red;"
    assert config.counter == 1

def test_add_or_update_class():
    html = '<div class="old-class">'
    new_class_str = 'class="new-class"'
    expected = '<div class="new-class">'

    result = add_or_update_class(html, new_class_str)

    assert result == expected

def test_create_css_file(config):
    config.css_rules = {
        "class1": "color: red;",
        "class2": "font-size: 12px;",
    }
    expected = ".class1 {color: red;}\n.class2 {font-size: 12px;}\n"

    create_css_file(config)

    with open(config.css_file_path, "r") as f:
        result = f.read()

    assert result == expected

def test_remove_duplicate_classes():
    css_file_path = "test.css"
    css_content = ".class1 {color: red;}\n.class2 {font-size: 12px;}\n.class1 {color: blue;}\n"
    expected = ".class1 {color: red;}\n.class2 {font-size: 12px;}\n"

    with open(css_file_path, "w") as f:
        f.write(css_content)

    remove_duplicate_classes(css_file_path)

    with open(css_file_path, "r") as f:
        result = f.read()

    assert result == expected
