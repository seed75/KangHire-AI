from typing import List, Dict
from groq import Groq
import json
import os
from typing import Optional, Dict
# from openai import OpenAI, RateLimitError

# client = OpenAI()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# 직무별 주요 스킬 세트
SKILLS_BY_ROLE: Dict[str, List[str]] = {
    "software developer": [
        "python", "java", "javascript", "react", "node", "git", "sql", "docker",
        "aws", "linux", "rest api",
    ],
    "frontend developer": [
        "html", "css", "javascript", "typescript", "react", "redux",
        "tailwind", "vite", "next.js", "figma",
    ],
    "backend developer": [
        "python", "java", "node", "django", "flask", "spring boot",
        "mysql", "postgresql", "mongodb", "docker", "aws",
    ],
    "data analyst": [
        "sql", "excel", "power bi", "tableau", "python", "pandas", "numpy",
        "statistics", "data visualization",
    ],
    "ui/ux designer": [
        "figma", "sketch", "wireframe", "prototype", "user research",
        "a/b testing", "information architecture",
    ],
    "marketing specialist": [
        "seo", "google ads", "facebook ads", "analytics",
        "copywriting", "content marketing",
    ],
    "customer service": [
        "customer support", "communication", "crm", "ticketing system",
        "conflict resolution", "problem solving",
    ],
    "project manager": [
        "project management", "scrum", "agile", "jira",
        "risk management", "stakeholder management",
    ],
    "general": [
        "communication", "teamwork", "problem solving",
        "time management", "leadership",
    ],
}

def _normalize_role(target_role: Optional[str]) -> str:
    """
    사용자가 선택한 역할 문자열을 받아서,
    내부 딕셔너리 key(software developer, data analyst, ...) 중 하나로 매핑.
    """
    if not target_role:
        return "software developer"

    role = target_role.lower().strip()

    if "front" in role:
        return "frontend developer"
    if "back" in role:
        return "backend developer"
    if "data" in role:
        return "data analyst"
    if "ui" in role or "ux" in role or "design" in role:
        return "ui/ux designer"
    if "market" in role:
        return "marketing specialist"
    if "customer" in role or "support" in role or "service" in role:
        return "customer service"
    if "project" in role or "pm" in role:
        return "project manager"
    if "develop" in role:
        return "software developer"

    return "general"


# 2. 규칙 기반 이력서 분석
def analyze_resume_rules(text: str, target_role: Optional[str] = None) -> Dict[str, object]:
    """
    규칙 기반 이력서 분석기 (직무 기반).
    선택한 target_role 에 따라 다른 스킬 세트를 사용한다.
    """

    lowered = text.lower()

    # 기본 역할은 Software Developer
    role = (target_role or "software developer").lower().strip()

    # 역할 문자열로 key 판단
    if "front" in role:
        role_key = "frontend developer"
    elif "back" in role:
        role_key = "backend developer"
    elif "data" in role:
        role_key = "data analyst"
    elif "ui" in role or "ux" in role or "design" in role:
        role_key = "ui/ux designer"
    elif "market" in role:
        role_key = "marketing specialist"
    elif "customer" in role or "support" in role or "service" in role:
        role_key = "customer service"
    elif "project" in role or "pm" in role:
        role_key = "project manager"
    elif "develop" in role:
        role_key = "software developer"
    else:
        role_key = "general"

    keywords = SKILLS_BY_ROLE.get(role_key, SKILLS_BY_ROLE["general"])

    found = []
    missing = []

    for kw in keywords:
        if kw.lower() in lowered:
            found.append(kw)
        else:
            missing.append(kw)

    # 점수 계산
    score = int(len(found) / len(keywords) * 100) if keywords else 0

    summary = (
        f"'{target_role or role_key}' 역할 기준으로 {len(keywords)}개 스킬 중 "
        f"{len(found)}개가 이력서에서 확인되었습니다."
    )

    return {
        "summary": summary,
        "skills_found": found,
        "skills_missing": missing,
        "score": score,
    }

# 3. Groq 기반 AI 이력서 분석
# Free AI analysis fuction using Groq
def analyze_resume_ai(text: str, target_role: Optional[str] = None) -> Dict[str, object]:
    """
    무료 Groq AI 기반 이력서 분석기.
    LLaMA 3.3-70B 모델을 사용해 JSON 응답을 직접 생성한다.
    target_role 을 기준으로 이력서를 평가한다.
    """

    role_for_prompt = (target_role or "Software Developer").strip()

    # system 프롬프트: JSON 구조 + 역할 정보 포함
    system_prompt = f"""
You are an AI resume coach.

- The user is applying for this target role: "{role_for_prompt}".
- Read the resume text and evaluate it specifically for that role.
- Focus on skills, experience, and keywords that are relevant to that job title.

You MUST respond ONLY with a strict JSON object.
NO extra text. NO explanation outside JSON.

The JSON structure MUST be:

{{
  "summary": "string (in Korean, 1~2 sentences)",
  "skills_found": ["string"],
  "skills_missing": ["string"],
  "score": 0,
  "recommendations": ["string"]
}}

Rules:
- summary: in English, 이력서와 목표 직무의 적합도를 1~2문장으로 요약.
- skills_found: 이력서에 실제로 등장하는 기술/역량 키워드만 넣기.
- skills_missing: 목표 직무에 비해 부족해 보이는 기술/키워드.
- score: 0~100 사이 정수. 100에 가까울수록 해당 역할에 잘 맞는 이력서.
- recommendations: in English, 구체적인 개선 제안을 2~5개 작성.
"""

    user_prompt = f"Here is the resume text:\n\n{text}"

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )

        raw_output = response.choices[0].message.content or ""

        # 1차: 그대로 JSON 파싱 시도
        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError:
            # 2차: 문자열에서 { ... } 부분만 잘라서 다시 시도
            try:
                start = raw_output.find("{")
                end = raw_output.rfind("}") + 1
                cleaned = raw_output[start:end]
                data = json.loads(cleaned)
            except Exception:
                # 그래도 안 되면 fallback 구조
                data = {
                    "summary": "Failed to parse AI response.",
                    "skills_found": [],
                    "skills_missing": [],
                    "score": 0,
                    "recommendations": [],
                    "raw_output": raw_output,
                }

        return data

    except Exception as e:
        # Groq 호출 자체가 실패했을 때
        return {
            "summary": "An error occurred during AI analysis.",
            "skills_found": [],
            "skills_missing": [],
            "score": 0,
            "recommendations": [],
            "error": str(e),
        }