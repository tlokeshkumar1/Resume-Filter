## 📮 API Endpoints (Postman Usage Guide)

### 1. **Upload Resume**

* **URL:** `http://localhost:8000/`
* **Method:** `POST`
* **Body Type:** `form-data`
* **Key:** `file` (Type: File)
* **Value:** Upload `.pdf`, `.docx`, or `.txt` resume
* **Description:** Extracts resume data and stores it in `candidates.json` as structured JSON

---

### 2. **Show All Candidates (Filtered or Unfiltered)**

* **URL:** `http://localhost:8000/showall`
* **Method:** `POST`
* **Body Type:** `x-www-form-urlencoded`
* **Key:** `prompt`
* **Value:** Any natural language filter (e.g., `Looking for who can talk Korean language`)
* **Optional:** Leave prompt empty to list all candidates
* **Description:** Returns filtered candidates using Gemini model

---

### 3. **Get Candidate by Number**

* **URL:** `http://localhost:8000/candidate`
* **Method:** `GET`
* **Params:**

  * `candidate_number` = e.g., `1`
* **Description:** Fetch details of a specific candidate

---

### 4. **Update Candidate**

* **URL:** `http://localhost:8000/candidate/{candidate_number}`
* **Method:** `PUT`
* **Body Type:** `raw` → `JSON`
* **Example Body:**

```json
{
  "name": "Updated Name",
  "skills": ["Python", "Korean"]
}
```

* **Description:** Updates a candidate’s record

---

### 5. **Delete Candidate**

* **URL:** `http://localhost:8000/candidate/{candidate_number}`
* **Method:** `DELETE`
* **Description:** Removes a candidate from the system

---

### 6. **Search by Skills**

* **URL:** `http://localhost:8000/search/skills`
* **Method:** `GET`
* **Params:**

  * `skills` = comma-separated values (e.g., `Python,Korean`)
* **Description:** Returns candidates matching all given skills

---

### 7. **Get Candidate Summary**

* **URL:** `http://localhost:8000/candidate/{candidate_number}/summary`
* **Method:** `GET`
* **Description:** AI-generated 3-sentence summary for a candidate

---

### 8. **Compare Candidates for a Job**

* **URL:** `http://localhost:8000/compare`
* **Method:** `POST`
* **Body Type:** `raw` → `JSON`
* **Example Body:**

```json
{
  "candidate_ids": [1, 2],
  "job_description": "Looking for a Python backend developer with FastAPI experience"
}
```

* **Description:** Uses Gemini to rank candidates based on job match

---

### 9. **Get Resume Statistics**

* **URL:** `http://localhost:8000/stats`
* **Method:** `GET`
* **Description:** Returns statistics like skill popularity and university distribution

---

## ✅ Notes

* All responses are in JSON
* Use `.env` file to securely store your `GOOGLE_API_KEY`
* This project does not have a frontend – test using Postman
