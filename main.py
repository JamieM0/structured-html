from jinja2 import Template
import json

testing = "nuclear-power"

# Load JSON data
with open("test-cases/"+testing+".json") as f:
    data = json.load(f)

# Load HTML template
with open("Template.html") as f:
    template = Template(f.read())

# Render HTML
html_output = template.render(**data)

# Save to file
with open("outputs/"+testing+".html", "w") as f:
    f.write(html_output)