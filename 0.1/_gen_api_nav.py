"""Generate API reference pages and the literate-nav summary for them.

Run by ``mkdocs-gen-files`` during every ``mkdocs build``. For each public
submodule of ``helakit``, write a page that asks ``mkdocstrings`` to render
the module, then list the page in ``api/SUMMARY.md`` so ``literate-nav``
can build the sidebar.
"""

from __future__ import annotations

from pathlib import Path

import mkdocs_gen_files

PUBLIC_MODULES: tuple[str, ...] = (
    "helakit",
    "helakit.nic",
    "helakit.phone",
    "helakit.postal",
)

nav_lines: list[str] = []

for module in PUBLIC_MODULES:
    page_path = Path("api") / f"{module}.md"
    title = module
    with mkdocs_gen_files.open(page_path, "w") as fd:
        fd.write(f"# `{title}`\n\n::: {module}\n")
    nav_lines.append(f"- [{title}]({module}.md)\n")

with mkdocs_gen_files.open("api/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav_lines)
