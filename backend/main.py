from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from typing import Optional

from resume_analyzer import analyze_resume_rules, analyze_resume_ai

import io
from pypdf import PdfReader
from docx import Document

from fastapi.middleware.cors import CORSMiddleware


# Initialize FastAPI app
app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 나중에 도메인 제한 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define a simple route to check if the backend is running
@app.get("/hello")
def hello():
    return {"message": "KangHire AI backend is running (Groq)!"}

# Define a Pydantic model for resume input
class ResumeInput(BaseModel):
    text: str # Resume text input
    target_role: Optional[str] = None  # New optional field for target role

# Define a route to analyze resume text
@app.post("/analyze_resume")
def analyze_resume(payload: ResumeInput):
    return analyze_resume_rules(text=payload.text, target_role=payload.target_role)

    # 그 결과를 그대로 반환 (FastAPI가 JSON으로 바꿔줌)
    return analyze_resume_rules(payload.text)

# Groq based AI analysis route
@app.post("/analyze_resume_ai")
def analyze_resume_ai_endpoint(payload: ResumeInput):
    return analyze_resume_ai(text=payload.text, target_role=payload.target_role)
# Route to handle resume file upload and AI analysis


@app.post("/upload_resume_ai")
async def upload_resume_ai(file: UploadFile = File(...), target_role: str = Form("Software Developer"),):
    """
    PDF / DOCX 이력서 파일을 업로드 받아서
    텍스트를 추출한 뒤, Groq AI 분석기에 넘겨준다.
    """

    filename = (file.filename or "").lower()

    # 1) 파일 확장자 확인
    if not (filename.endswith(".pdf") or filename.endswith(".docx")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF or DOCX files are supported.",
        )

    # 2) 파일 내용을 메모리로 읽기 (bytes)
    content: bytes = await file.read()

    # 3) 확장자에 따라 텍스트 추출
    text = ""

    # PDF 처리
    if filename.endswith(".pdf"):
        # io.BytesIO: 메모리에 있는 bytes를 파일처럼 다루게 해주는 클래스
        pdf_reader = PdfReader(io.BytesIO(content))
        parts = []
        for page in pdf_reader.pages:
            page_text = page.extract_text() or ""
            parts.append(page_text)
        text = "\n".join(parts)

    # DOCX 처리
    elif filename.endswith(".docx"):
        # python-docx 는 파일 경로 또는 파일 객체가 필요해서
        # 여기서는 임시 파일로 저장하는 방법을 사용해도 되고,
        # 간단히 BytesIO로 감싸서 읽을 수도 있다.
        # 가장 안정적인 방법은 임시 파일이지만, 여기서는 간단 버전으로 구현.
        # (문제가 생기면 임시 파일 방식으로 바꿔도 됨)
        # BytesIO 로는 직접 안 되는 경우가 있어서, 실제로는 temp 파일 권장.
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        doc = Document(tmp_path)
        parts = [p.text for p in doc.paragraphs]
        text = "\n".join(parts)

    # 4) 텍스트가 비었으면 에러
    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from the file.",
        )

    # 5) 추출한 텍스트를 AI 분석기로 넘김
    result = analyze_resume_ai(text, target_role=target_role)

    return result
