import os
import httpx

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

async def call_ollama(prompt: str, model: str = DEFAULT_MODEL) -> str:
    url = f"{OLLAMA_HOST}/api/generate"  # updated endpoint
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=120.0)
        response.raise_for_status()
        data = response.json()
        # extract the text from the first choice
        return data["choices"][0]["text"]

async def generate_resume_prompt(resume: str, job_description: str) -> str:
    return f"Given this f{resume} out of 100 show me the match percentage between this resume and job description. Only output a score and a summary  of if the candidate has soft, strong or medium alignment to core technical requirements, list these requirements out. Note if the years of experience matches the job description. Note any soft skills the candidate should focus on based on the job description. Do this under 100 words or less. {job_description}"

async def generate_sw_prompt(resume: str, job_description: str) -> str:
    return f"Given this f{resume} give me the strengths and weaknesses of this resume. Do this under 100 words or less. Format: Strengths: [List of Strengths] Weaknesses: [List of Weaknesses] {job_description}"

async def generate_match_prompt(resume: str, job_description:str) -> str:
    return f"Given this f{resume} give me 3 specific tips to improve the resume to better match the and for each tip generate 3 resume bullet points in xyz format. Do this under 100 words or less. So give me 3 tips in one sentence, and three resume bullet points {job_description}"