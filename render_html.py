#!/usr/bin/env python

from pathlib import Path
import jinja2
import glob

template_path = Path(__file__).parent / "templates"
assert template_path.is_dir()

plots = glob.iglob("plots/*.png")
urls = (f"/{plot}" for plot in plots)

with open("templates/index.html") as infile:
    template = jinja2.Template(infile.read())

with open("index.html", "w") as outfile:
    print(template.render(plots=urls), file=outfile)
