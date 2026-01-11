import os
import httpx

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

async def call_openai(
    prompt: str,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 400,
    timeout: float = 1800.0
) -> str:
    """
    Call OpenAI's Chat Completions API using httpx.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set in environment")

    url = f"{OPENAI_API_BASE}/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
                timeout=timeout
            )

            # For better debugging when things go wrong
            if response.status_code != 200:
                print("OpenAI error response:", response.text)
                response.raise_for_status()

            data = response.json()

            if "choices" not in data or not data["choices"]:
                raise ValueError("OpenAI returned empty choices")

            content = data["choices"][0]["message"]["content"]
            return content.strip()

    except httpx.TimeoutException:
        raise TimeoutError("OpenAI request timed out after {} seconds".format(timeout))
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text if e.response else str(e)
        raise RuntimeError(f"OpenAI returned error {e.response.status_code}: {error_detail}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error calling OpenAI: {str(e)}")

# Backwards-compatible alias: keep call_ollama name available for existing imports
async def call_ollama(prompt: str, model: str = DEFAULT_MODEL, temperature: float = 0.7, max_tokens: int = 400, timeout: float = 1800.0) -> str:
    """Compatibility wrapper so existing code that imports `call_ollama` keeps working."""
    return await call_openai(prompt, model=model, temperature=temperature, max_tokens=max_tokens, timeout=timeout)

async def generate_resume_prompt(resume: str, job_description: str) -> str:
    return f"Given this {resume} out of 100 show me the match percentage between this resume and job description. Only output a score and a summary  of if the candidate has soft, strong or medium alignment to core technical requirements, list these requirements out. Note if the years of experience matches the job description. Note any soft skills the candidate should focus on based on the job description. Do this under 100 words or less. {job_description}"

async def generate_sw_prompt(resume: str, job_description: str) -> str:
    return f"Given this {resume} give me the strengths and weaknesses of this resume. Do this under 100 words or less. Format: Strengths: [List of Strengths] Weaknesses: [List of Weaknesses] {job_description}"

async def generate_match_prompt(resume: str, job_description:str) -> str:
    return f"Given this {resume} give me 3 specific tips to improve the resume to better match the and for each tip generate 3 resume bullet points in xyz format. Do this under 100 words or less. So give me 3 tips in one sentence, and three resume bullet points {job_description}"