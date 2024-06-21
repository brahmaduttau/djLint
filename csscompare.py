import os
import pprint
import re

from cssutils import parseStyle


def parse_css_content(css_content):
    """Parse CSS content to extract class names and their styles."""
    # This regex matches class names and their styles.
    pattern = r"\.([a-zA-Z0-9_-]+)\s*\{(.*?)\}"
    classes_styles = re.findall(pattern, css_content, re.DOTALL)
    # Normalize styles
    normalized_classes_styles = {
        cls: parseStyle(style).cssText for cls, style in classes_styles
    }
    return normalized_classes_styles


def compare_css_styles(file_path1, file_path2):
    """Compare CSS styles in two files and return classes from the second file with matching styles.

    Args:
    ----
        file_path1 (str): Path to the first CSS file.
        file_path2 (str): Path to the second CSS file.

    Returns:
    -------
        dict: A dictionary containing classes from the first file as keys and matching classes from the second file as values.
    """
    # Read the contents of the first file
    with open(file_path1, "r") as file1:
        content1 = file1.read()

    # Read the contents of the second file
    with open(file_path2, "r") as file2:
        content2 = file2.read()

    # Parse and normalize class styles from both files
    classes_styles_file1 = parse_css_content(content1)
    classes_styles_file2 = parse_css_content(content2)

    # Find classes in the second file with styles that match any in the first file
    matching_classes = {}
    for cls2, style2 in classes_styles_file2.items():
        for cls1, style1 in classes_styles_file1.items():
            if style1 == style2:
                matching_classes[cls1] = cls2

    return matching_classes


def replace_string_in_file(content, all_classes_styles):
    for find_str, replace_str in all_classes_styles.items():
        content = content.replace(find_str, replace_str)
    return content


def replace_string_in_html_files(folder_path, all_classes_styles):
    # Walk through the folder
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".html"):
                file_path = os.path.join(root, file)
                # Read the file content
                print("Processing file:", file_path)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                updated_content = replace_string_in_file(
                    content=content, all_classes_styles=all_classes_styles
                )

                # Write the updated content back to the file
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(updated_content)


def replace_string_in_css_files(file_path, all_classes_styles):
    # Walk through the folder
    # Read the file content
    print("Processing file:", file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    updated_content = replace_string_in_file(
        content=content, all_classes_styles=all_classes_styles
    )

    # Write the updated content back to the file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(updated_content)


# Example usage
folder_path = "./transit_odp"
file_path1 = "djlint.css"
file_comapare_paths = [
    "./node_modules/govuk-frontend/dist/govuk/govuk-frontend.min.css",
    "./transit_odp/frontend/static/frontend/css/main.css",
]
for file_path2 in file_comapare_paths:
    matching_classes = compare_css_styles(file_path1, file_path2)
    pprint.pprint(matching_classes)
    replace_string_in_html_files(
        folder_path=folder_path, all_classes_styles=matching_classes
    )
    replace_string_in_css_files("./djlint.css", matching_classes)

matching_classes = {
    "bods-ec641141e0-2": "icon-container",
    "bods-cebde7d265-0": "content-box",
    "bods-a80e23cc21-0": "image-frame",
    "bods-4d03ee7d94-0": "no-border",
    "bods-c3f6d00479-0": "indented-text",
    "bods-d5791d24b9-0": "tall-section",
    "bods-d19c2e34b1-0": "end-justified",
    "bods-07725e9854-2": "large-font",
    "bods-5e23e1f18e-0": "blue-background",
    "bods-7f6e27f021-6": "empty-bar",
    "bods-68ff6e3896-8": "bold-white-text",
    "bods-5e23e1f18e-8": "blue-header",
    "bods-7f6e27f021-14": "empty-bar",
    "bods-68ff6e3896-16": "bold-white-text",
    "bods-cebde7d265-2": "content-box",
    "bods-71b0da798a-0": "top-border",
    "bods-aa72a636bb-0": "normal-weight",
    "bods-73cfce8020-2": "shifted-text",
}
replace_string_in_html_files(
    folder_path=folder_path, all_classes_styles=matching_classes
)
replace_string_in_css_files("./djlint.css", matching_classes)
