from pathlib import Path
import json
import csv
from PIL import Image
import pytesseract
import docx2txt
import pdfplumber
import io
from fastapi import UploadFile

async def extract_resume_text(file: UploadFile) -> str:
    ext = Path(file.filename).suffix.lower()
    contents = await file.read()

    if ext == ".pdf":
        return extract_pdf(contents)

    if ext == ".docx":
        return docx2txt.process(contents)

    if ext == ".csv":
        return extract_csv(contents)

    if ext == ".json":
        return extract_json(contents)

    if ext in [".png", ".jpg", ".jpeg"]:
        return extract_image(contents)

    raise ValueError("Unsupported file type")

def extract_pdf(data: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def extract_csv(data: bytes) -> str:
    text = ""
    reader = csv.reader(io.StringIO(data.decode()))
    for row in reader:
        text += " ".join(row) + "\n"
    return text

def extract_image(data: bytes) -> str:
    img = Image.open(io.BytesIO(data))
    return pytesseract.image_to_string(img)

def extract_json(data: bytes) -> str:
    obj = json.loads(data)
    return json.dumps(obj, indent=2)
