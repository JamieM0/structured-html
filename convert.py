from jinja2 import Template
import json
import os

if(os.path("json-files") == False):
    os.mkdir("json-files")
if(os.path("search-digests") == False):
    os.mkdir("search-digests")
if(os.path("json-files") == False):
    os.mkdir("json-files")

jsonFileName = "bread_production"

# Load JSON data
with open("json-files/"+jsonFileName+".json") as f:
    data = json.load(f)

# Load HTML template
with open("Template.html") as f:
    template = Template(f.read())

# Render HTML
html_output = template.render(**data)

# Save to file
with open("outputs/"+jsonFileName+".html", "w") as f:
    f.write(html_output)