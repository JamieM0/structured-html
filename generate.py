import os
import sys

from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Dict, Any
import requests
import json
import re
from typing import List, Dict, Optional

if(os.path("json-files") == False):
    os.mkdir("json-files")
if(os.path("search-digests") == False):
    os.mkdir("search-digests")
if(os.path("json-files") == False):
    os.mkdir("json-files")

# Define the Pydantic models matching your schema
class Breadcrumb(BaseModel):
    label: str
    url: str
class Status(BaseModel):
    label: str
    progress: int
class Company(BaseModel):
    name: str
    description: str
    url: str
class TimelineEntry(BaseModel):
    year: int
    event: str
class Section(BaseModel):
    title: str
    type: str
    content: List[Any] = Field(..., description="Can be strings, company objects, timeline entries, etc.")

class AutomationArticle(BaseModel):
    title: str
    breadcrumbs: List[Dict[str, str]]
    status: Dict[str, Any]
    sections: List[Dict[str, Any]]
    metadata: Dict[str, str]

class AutomationStep(BaseModel):
    component: str
    technologies: List[str]
    implementation: List[str]
    challenges: List[str]
    solutions: List[str]
    reference_links: List[str] = Field(
        description="URLs to relevant patents/research"
    )

class InstructionSection(BaseModel):
    type: str = "instructions"
    title: str = "Technical Implementation Plan"
    content: List[AutomationStep]

def clean_generated_json(raw_json: dict) -> dict:
    """Fix common formatting issues in generated JSON"""
    for section in raw_json.get("sections", []):
        if section["type"] == "companies":
            section["content"] = [{
                "name": item.strip("* -") if isinstance(item, str) else item.get("name"),
                "description": "" if isinstance(item, str) else item.get("description", ""),
                "url": "#" if isinstance(item, str) else item.get("url", "#")
            } for item in section["content"]]

        if section["type"] == "timeline":
            section["content"] = [{
                "year": int(re.search(r"\d{4}", str(item)).group(0)) if isinstance(item, str) else item.get("year"),
                "event": re.sub(r"^\*\s*", "", str(item)) if isinstance(item, str) else item.get("event")
            } for item in section["content"]]

    return raw_json

def generate_automation_article(topic: str, search_str: str) -> AutomationArticle:
    # Construct the prompt with format instructions

    prompt = f"""Generate a technical analysis of automating {topic} using this report generated from search data:
    {search_str}

    Create 5-7 highly specific technical steps in the instructions section. For each step:
    1. Name the core technology/component
    2. Explain its implementation specifics
    3. List required hardware/software
    4. Note key technical parameters

    Example for bread automation:
    {{
      "type": "instructions",
      "title": "Technical Implementation Plan",
      "content": [
        "Precision ingredient dosing system - Requires load cells (accuracy ±0.1g) and PID-controlled valves, integrated via ROS2 middleware",
        "AI-driven dough development monitoring - Uses hyperspectral imaging (900-1700nm range) with CNN models trained on 10k+ gluten network samples",
        "Closed-loop proofing control - Combines IoT humidity sensors (95% ±1% accuracy) with reinforcement learning adjustment of chamber conditions",
        "Autonomous batch transition - Collaborative robots (ISO/TS 15066 compliant) with vacuum grippers for tray handling",
        "Self-optimizing baking system - Multi-zone IR ovens with real-time crust analysis using NIR spectroscopy"
      ]
    }}

    Output must use this exact JSON structure:
    {{
      "title": "Automated [TOPIC]",
      "breadcrumbs": [{{"label": "...", "url": "/..."}}, ...],
      "status": {{"label": "...", "progress": 0-100}},
      "sections": [
        // MUST INCLUDE THESE 4 SECTIONS:
        {{
          "type": "instructions",
          "title": "Technical Implementation Plan",
          "content": [ // 5-7 detailed technical strings
            "Component - Technical specifics (key parameters)",
            ...
          ]
        }},
        {{
          "type": "companies",
          "title": "Key Innovators",
          "content": [{{"name": "...", "description": "...", "url": "#"}}]
        }},
        {{
          "type": "challenges",
          "title": "Technical Challenges",
          "content": ["Challenge 1", "Challenge 2", ...]
        }},
        {{
          "type": "timeline",
          "title": "Development Timeline",
          "content": [{{"year": 2025, "event": "..."}}]
        }},
        // OPTIONAL SECTIONS (include only if relevant):
        {{
          "type": "safety",
          "title": "Safety Considerations",
          "content": ["Requirement 1", "Requirement 2", ...]
        }}
      ],
      "metadata": {{
        "last_updated": "Month Year",
        "recent_source": "Month Year"
      }}
    }}
    
    Formatting Rules:
    - Include ALL 4 required sections (instructions, companies, challenges, timeline)
    - Add optional sections ONLY if relevant to the topic
    - Never use markdown bullets (*) in content arrays
    - Progress percentage must be 0-100

    Content Guidelines:
    - Instructions: Practical steps to achieve automation
    - Companies: Real organizations with descriptions
    - Challenges: Technical not economic/political
    - Timeline: Specific years with concrete milestones
    - Safety: Only for dangerous applications (e.g., nuclear, chemicals)
    
    Example for "bread":
    {{
      "title": "Automated Bread Production",
      "breadcrumbs": [{{"label": "Food", "url": "/food"}}, ...],
      "status": {{"label": "Partially Automated", "progress": 65}},
      "sections": [
        {{
            "type": "instructions",
            "title": "Technical Implementation Plan",
            "content": [
                "Precision ingredient dosing system - Requires load cells (accuracy ±0.1g) and PID-controlled valves, integrated via ROS2 middleware",
                "AI-driven dough development monitoring - Uses hyperspectral imaging (900-1700nm range) with CNN models trained on 10k+ gluten network samples",
                "Closed-loop proofing control - Combines IoT humidity sensors (95% ±1% accuracy) with reinforcement learning adjustment of chamber conditions",
                "Autonomous batch transition - Collaborative robots (ISO/TS 15066 compliant) with vacuum grippers for tray handling",
                "Self-optimizing baking system - Multi-zone IR ovens with real-time crust analysis using NIR spectroscopy"
            ]
        }},
        {{
          "type": "companies",
          "title": "Industry Leaders",
          "content": [{{"name": "BreadBot", "description": "Commercial bakery robots", "url": "#"}}]
        }},
        {{
          "type": "challenges",
          "title": "Key Challenges", 
          "content": ["Gluten network monitoring", "Crust formation control"]
        }},
        {{
          "type": "timeline",
          "title": "Development Timeline",
          "content": [{{"year": 2025, "event": "First fully autonomous bakery"}}]
        }}
      ],
      "metadata": {{...}}
    }}

    Now analyze: {topic}
    
    """

    prompt += """
    CRITICAL FORMATTING RULES:
    1. NEVER use markdown code blocks (```json)
    2. ALWAYS include opening { and closing }
    3. Remove all line breaks inside JSON values
    4. Use double quotes consistently

    BAD EXAMPLE:
    ```json
    {
      "title": "Automated
     Bread Production"
    }
    GOOD EXAMPLE:
    {
    "title": "Automated Bread Production",
    "breadcrumbs": [...]
    }
    
    The result MUST satisfy all of the following content criteria:
    Clearly outlines the biggest technical roadblocks to full automation.
    Explains how current solutions work and where they fall short.
    Gives a feasibility rating (e.g., “Definitely possible!") backed by evidence.
    Provides a clear roadmap for automating the process, broken into logical steps.
    Includes beginner-friendly shortcuts or simplified approaches for testing ideas.
    Flags tools or resources that are affordable and easy to access.
    Highlights unsolved problems that matter most for achieving automation.
    Summarises recent breakthroughs and links to papers/patents.
    Identifies who’s working on solutions (labs, startups) and how to collaborate.
    Gives timeline estimates tied to trends (e.g., "Robotic arms are getting 20% cheaper yearly").
    Explains key signals that could speed up or slow down progress.
    Avoids jargon or explains it plainly (e.g., "ROS2 = robot brain software").
    Uses visuals (diagrams, progress bars) to show how close we are to automation.
    Passes the "grandma test": Could someone without a background in the topic get the gist?
    Ensure that the content doesn’t patronise the reader, and that complex concepts aren’t overly simplistic
    Option to learn more about a topic.
    Highlights existing products, and related people and companies in the field.
    Discusses who wins and loses if this gets automated (jobs, industries).
    Compares costs of automation vs. doing things manually.
    Sources are recent and trustworthy (no outdated blogs or shady forums).
    Logs changes over time (e.g., "2023: Added self-cleaning oven tech").

    """

    for attempt in range(3):  # Retry up to 3 times
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.1:8b-instruct-q5_K_M",  # Try more reliable model
                    "prompt": prompt,
                    "format": "json",
                    "stream": True,
                    "options": {
                        "temperature": 0.5,
                        "num_ctx": 8000,
                        "num_predict": 2000
                    }
                },
                stream=True
            )
            response.raise_for_status()

            # Build complete response
            full_response = ""
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if not chunk.get("done"):
                        full_response += chunk.get("response", "")

            # Clean response
            full_response = full_response.strip("` \n")
            if not full_response.startswith("{"):
                full_response = "{" + full_response.split("{", 1)[-1]
            if not full_response.endswith("}"):
                full_response = full_response.split("}", 1)[0] + "}"

            # Validate with Pydantic V2+
            return AutomationArticle.model_validate_json(full_response)

        except (json.JSONDecodeError, ValidationError) as e:
            print(f"Attempt {attempt+1} failed. Retrying...")
            print(f"Raw response: {full_response}")
            continue

    raise ValueError(f"Failed after 3 attempts. Final response: {full_response}")

if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python generate.py \"Nuclear Power\" \"leettools_search_output.txt\" [output_filename.json]")
        sys.exit(1)

    output_file_prefix = "json-files/"
    topic = sys.argv[1]
    search_str_prefix = "search-digests/"
    search_str_main = sys.argv[2]
    search_str = search_str_prefix + search_str_main
    output_file_main = sys.argv[3] if len(sys.argv) == 4 else f"{topic.lower().replace(' ', '_')}.json"
    output_file = output_file_prefix + output_file_main

    if(search_str=="" or search_str_main==""):
        print("Search file not found.")
        sys.exit(1)
    try:
        article = generate_automation_article(topic, search_str)

        with open(output_file, "w") as f:
            f.write(article.model_dump_json(indent=2))
        print(f"Successfully generated {output_file}")
    except Exception as e:
        print(f"Critical failure: {str(e)}")
        sys.exit(1)