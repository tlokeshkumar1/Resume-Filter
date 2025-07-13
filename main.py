import os
import json
import re
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import List
import requests
from PyPDF2 import PdfReader
import docx2txt

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
CANDIDATE_FILE = "candidates.json"

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Load or create candidate file
if not os.path.exists(CANDIDATE_FILE):
    with open(CANDIDATE_FILE, "w") as f:
        json.dump([], f)

def read_candidates():
    with open(CANDIDATE_FILE, "r") as f:
        return json.load(f)

def write_candidates(candidates):
    with open(CANDIDATE_FILE, "w") as f:
        json.dump(candidates, f, indent=2)

def extract_text_from_file(file: UploadFile) -> str:
    if file.filename.endswith(".pdf"):
        reader = PdfReader(file.file)
        return "\n".join(page.extract_text() for page in reader.pages)
    elif file.filename.endswith(".docx"):
        return docx2txt.process(file.file)
    else:
        return file.file.read().decode("utf-8")

def call_gemini(prompt: str, content: str) -> dict:
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [{"parts": [{"text": f"{prompt}\n\n{content}"}]}]
    }
    response = requests.post(f"{GEMINI_URL}?key={GOOGLE_API_KEY}", headers=headers, json=body)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Gemini API error")
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]

def extract_json(text):
    try:
        # Find the first JSON-like object in the text
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            return None
    except Exception as e:
        return None

@app.post("/")
async def upload_resume(file: UploadFile = File(...)):
    raw_text = extract_text_from_file(file)
    prompt = "Strictly return a valid JSON object matching this format. Do not include any explanation, markdown, or text outside of the JSON: " + """
    {
      "name": "", "phone_number": "", "email": "", "summary": "", "location": "", 
      "skills": [], "education": [], "experience": [], "projects": [], 
      "certifications": [], "languages": [], 
      "profiles": {"linkedin": "", "github": "", "portfolio": "", "twitter": "", "other": ""}
    }
    """
    result_text = call_gemini(prompt, raw_text)
    candidate_data = extract_json(result_text)

    if not candidate_data:
        raise HTTPException(status_code=500, detail="Failed to parse Gemini response as JSON")

    candidates = read_candidates()
    candidate_number = len(candidates) + 1
    candidate_data["candidate_number"] = candidate_number
    candidates.append(candidate_data)
    write_candidates(candidates)

    return {
        "message": "Successfully uploaded and parsed.",
        "data": candidate_data
    }

@app.post("/showall")
async def show_all(prompt: str = Form(None)):
    candidates = read_candidates()
    if not prompt:
        return {"total": len(candidates), "candidates": candidates}

    combined_text = json.dumps(candidates, indent=2)
    user_prompt = f"Filter the candidates for: {prompt}. Show suitable candidates with name and candidate_number."
    result = call_gemini(user_prompt, combined_text)
    return {"query": prompt, "result": result}

@app.get("/candidate")
async def get_candidate(candidate_number: int):
    candidates = read_candidates()
    for c in candidates:
        if c["candidate_number"] == candidate_number:
            return c
    raise HTTPException(status_code=404, detail="Candidate not found")

@app.put("/candidate/{candidate_number}")
async def update_candidate(candidate_number: int, updated_data: dict):
    candidates = read_candidates()
    for i, c in enumerate(candidates):
        if c["candidate_number"] == candidate_number:
            updated_data["candidate_number"] = candidate_number
            candidates[i] = updated_data
            write_candidates(candidates)
            return {"message": "Candidate updated"}
    raise HTTPException(status_code=404, detail="Candidate not found")

@app.delete("/candidate/{candidate_number}")
async def delete_candidate(candidate_number: int):
    candidates = read_candidates()
    candidates = [c for c in candidates if c["candidate_number"] != candidate_number]
    write_candidates(candidates)
    return {"message": f"Candidate {candidate_number} deleted"}

@app.get("/search/skills")
async def skill_search(skills: str = Query(...)):
    skills_list = [s.strip().lower() for s in skills.split(",")]
    candidates = read_candidates()
    matched = []
    for c in candidates:
        if all(skill in [s.lower() for s in c.get("skills", [])] for skill in skills_list):
            matched.append(c)
    return {"query_skills": skills_list, "matched": matched}

@app.get("/candidate/{candidate_number}/summary")
async def candidate_summary(candidate_number: int):
    candidates = read_candidates()
    for c in candidates:
        if c["candidate_number"] == candidate_number:
            prompt = "Write a 3-sentence professional summary based on this candidate's profile."
            return {"summary": call_gemini(prompt, json.dumps(c, indent=2))}
    raise HTTPException(status_code=404, detail="Candidate not found")

@app.post("/compare")
async def compare_candidates(data: dict):
    candidate_ids = data.get("candidate_ids", [])
    job_description = data.get("job_description", "")
    candidates = read_candidates()
    selected = [c for c in candidates if c["candidate_number"] in candidate_ids]
    if not selected:
        raise HTTPException(status_code=404, detail="No matching candidates")

    prompt = f"Compare these candidates against the job description and rank them accordingly: {job_description}"
    return {"comparison": call_gemini(prompt, json.dumps(selected, indent=2))}

@app.get("/stats")
async def get_statistics():
    candidates = read_candidates()
    total = len(candidates)
    skill_counter = {}
    university_counter = {}
    for c in candidates:
        for s in c.get("skills", []):
            skill_counter[s] = skill_counter.get(s, 0) + 1
        for edu in c.get("education", []):
            uni = edu.get("university")
            if uni:
                university_counter[uni] = university_counter.get(uni, 0) + 1
    return {
        "total_candidates": total,
        "common_skills": skill_counter,
        "university_distribution": university_counter
    }
