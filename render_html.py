#!/usr/bin/env python

import jinja2
import glob

plots = glob.iglob("plots/*.png")
urls = (f"/{plot}" for plot in plots)

with open("templates/index.html") as infile:
    template = jinja2.Template(infile.read())

with open("index.html", "w") as outfile:
    print(template.render(plots=urls), file=outfile)
