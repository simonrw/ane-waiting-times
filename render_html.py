#!/usr/bin/env python

from pathlib import Path
import jinja2
import glob

template_path = Path(__file__).parent / "templates"
assert template_path.is_dir()

urls = glob.iglob("plots/*.png")

with open("templates/index.html") as infile:
    template = jinja2.Template(infile.read())

with open("index.html", "w") as outfile:
    print(template.render(plots=urls), file=outfile)
