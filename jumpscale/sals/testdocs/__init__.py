import pytest
from jumpscale.loader import j

test_template = """{% if new_line %}\n{% endif %}### {{ name }}

{{ body | replace ("  ", "")}}
"""

category_template = """{% if new_line %}\n{% endif %}### {{ category }}


"""
entry_template = """- [{{ name }}]({{ location }})

"""


class Collector:
    def __init__(self, source, target):
        self.tests_docs_locations = []
        self.target = target
        if j.sals.fs.exists(source):
            if not j.sals.fs.is_dir(source):
                source = j.sals.fs.parent(source)
            j.sals.fs.chdir(source)
        self.source = source

    def pytest_collection_modifyitems(self, items):
        """This method is a pytest hook which can modify the items has been collected.

        Args:
            items (list): Tests objects has been collected.
        """
        for item in items:
            self._generate_docs_for_item(item)

    def _generate_docs_for_item(self, item):
        """Generate a markdown docs for test scenario.

        Args:
            item (object): Test object that docs will be generated from.
        """
        doc = item._obj.__doc__
        name = item.name
        if doc:
            # Get target docs locations.
            absolute_test_location = str(item.fspath)
            relative_test_location = absolute_test_location.split(self.source)[1][1:]
            relative_test_location = relative_test_location.replace(".py", ".md")
            target_location = j.sals.fs.join_paths(self.target, relative_test_location)

            # Check if the docs exists and remove them in this case to generate a new one.
            if target_location not in self.tests_docs_locations:
                self.tests_docs_locations.append(target_location)
                if j.sals.fs.exists(target_location):
                    j.sals.fs.rmtree(target_location)

            # Write docs.
            j.sals.fs.mkdirs(j.sals.fs.parent(target_location))
            if j.sals.fs.exists(target_location):
                with open(target_location, "a") as f:
                    test_doc = j.tools.jinja2.render_template(
                        template_text=test_template, name=name, body=doc, new_line=True
                    )
                    f.write(test_doc)
            else:
                test_doc = j.tools.jinja2.render_template(
                    template_text=test_template, name=name, body=doc, new_line=False
                )
                j.sals.fs.write_file(target_location, test_doc)

            # add entry to main README.md
            location_parts = relative_test_location.split(j.sals.fs.sep)
            if len(location_parts) == 1:
                category = ""
            else:
                category = location_parts[0].capitalize()
            file_name = location_parts[-1].replace(".md", "")
            self._add_entry_to_main_readme(category, file_name, relative_test_location)

        else:
            j.logger.warning(f"Test {name} doesn't have docstring")

    def _add_entry_to_main_readme(self, category, file_name, relative_location):
        """Add an entry to the tests main README.md use for navigation.

        Args:
            category (str): Test category (e.g. sals, clients).
            file_name (str): The name of the file name.
            relative_location (str): The relative path of the test file to the main tests README.md
        """
        readme_location = j.sals.fs.join_paths(self.target, "README.md")
        readme = ""
        if j.sals.fs.exists(readme_location):
            readme = j.sals.fs.read_file(readme_location)
        if category:
            category = j.tools.jinja2.render_template(
                template_text=category_template, category=category, new_line=readme
            )
        new_entry = j.tools.jinja2.render_template(
            template_text=entry_template, name=file_name, location=relative_location
        )
        if not new_entry in readme:
            if not category.lstrip() in readme:
                readme = f"{readme}{category}"

            # Get the entry location in readme file.
            first_line_in_category = readme.find(category.lstrip()) + len(category.lstrip())
            last_line_in_category = readme.find("###", first_line_in_category) - 1
            entry_location = first_line_in_category
            if last_line_in_category < 0:
                last_line_in_category = len(readme)
            for line in readme[first_line_in_category:last_line_in_category].splitlines():
                if new_entry > line:
                    entry_location += len(line) + 1  # this one for the new line.
                else:
                    break
            new_readme = f"{readme[:entry_location]}{new_entry}{readme[entry_location:]}"
            j.sals.fs.rmtree(readme_location)
            j.sals.fs.write_file(readme_location, new_readme)


def generate_tests_docs(source, target, clean=False):
    """Generate a markdown docs for tests from its docstring.

    Args:
        source (str): Tests path.
        target (str): Target docs path.
        clean (bool): To clean the target path before start.
    """
    source = j.sals.fs.absolute(source)
    target = j.sals.fs.absolute(target)
    if clean and j.sals.fs.exists(target):
        j.sals.fs.rmtree(target)

    collector = Collector(source=source, target=target)
    pytest.main(["--collect-only", source], plugins=[collector])
