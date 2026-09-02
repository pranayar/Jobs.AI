import json
import os
import fitz

from llama_cpp import Llama


MODEL_PATH = "models/Qwen2.5-1.5B-Instruct-Q4_K_M.gguf"


# Load Qwen once when Flask starts
print("Loading Qwen 2.5...")

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=4096,
    n_threads=4,
    verbose=False
)

print("Qwen 2.5 loaded.")


def extract_pdf_text(pdf_path):
    """
    Extract all text from the uploaded resume.
    """

    document = fitz.open(pdf_path)

    text = ""

    for page in document:
        text += page.get_text() + "\n"

    document.close()

    return text.strip()


def clean_json_response(response):
    """
    Clean Qwen's response and convert it into JSON.
    """

    response = response.strip()

    # Remove markdown code fences
    if response.startswith("```"):
        response = response.replace("```json", "")
        response = response.replace("```", "")
        response = response.strip()

    # Find JSON object if Qwen added extra text
    start = response.find("{")
    end = response.rfind("}")

    if start != -1 and end != -1:
        response = response[start:end + 1]

    return json.loads(response)


def analyze_resume(pdf_path):

    resume_text = extract_pdf_text(pdf_path)

    if not resume_text:
        raise ValueError("Could not extract any text from the PDF.")

    prompt = f"""
You are Jobs.AI, an AI resume analyzer.

Analyze the resume below.

Give an overall resume score from 0 to 100.

Evaluate the resume based on:

1. Resume length
2. Relevant keywords
3. Technical skills
4. Work experience
5. Education
6. Projects
7. Certifications
8. Resume sections
9. Quantifiable achievements
10. Overall clarity and completeness

Also extract all useful information from the resume.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "score": 0,
    "score_summary": "",
    "personal_info": {{
        "name": "",
        "email": "",
        "phone": "",
        "location": ""
    }},
    "experience": [
        {{
            "job_title": "",
            "company": "",
            "duration": "",
            "description": ""
        }}
    ],
    "education": [
        {{
            "degree": "",
            "institution": "",
            "year": ""
        }}
    ],
    "skills": [],
    "projects": [],
    "certifications": [],
    "resume_length": {{
        "pages": 0,
        "assessment": ""
    }},
    "strengths": [],
    "weaknesses": [],
    "missing_keywords": [],
    "recommendations": []
}}

Rules:

- score must be an integer between 0 and 100.
- Extract information only when it exists in the resume.
- Do not invent experience, skills, education or certifications.
- Keep descriptions concise.
- skills should contain individual technical and professional skills.
- recommendations should be practical.
- missing_keywords should contain potentially useful keywords based on the candidate's existing profile, but do not claim the candidate has those skills.

RESUME:

{resume_text}
"""

    result = llm.create_chat_completion(
        messages=[
            {
                "role": "system",
                "content": "You are a precise resume analysis engine. Return valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=2000,
        temperature=0.1
    )

    response = result["choices"][0]["message"]["content"]

    return clean_json_response(response)