import io
import json
import os
import random
import re
from typing import List, Dict, Any
from pypdf import PdfReader
from docx import Document
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import time

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_AVAILABLE = bool(GEMINI_API_KEY)
print(f"🤖 Gemini AI: {'Available' if GEMINI_AVAILABLE else 'Not configured (set GEMINI_API_KEY environment variable)'}")
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        print("✅ Gemini AI configured successfully")
    except ImportError:
        print("⚠️ google-generativeai not installed. Run: pip install google-generativeai")
        GEMINI_API_KEY = ""
else:
    print("ℹ️ No GEMINI_API_KEY found in environment. Using fallback questions.")

app = FastAPI(title="AI Coding Skill Assessment Agent")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class CodeSubmission(BaseModel):
    questionId: str
    code: str
    language: str
    testCases: List[Dict]

class BulkSubmission(BaseModel):
    candidateName: str
    submissions: List[CodeSubmission]
    resumeText: Optional[str] = ""
    jdText: Optional[str] = ""
def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    Extracts text from PDF, DOCX, or TXT files
    
    Args:
        file_content: Binary file content
        filename: Original filename with extension
    
    Returns:
        Extracted text as string
    """
    text = ""
    try:
        if filename.lower().endswith(".pdf"):
            reader = PdfReader(io.BytesIO(file_content))
            for page in reader.pages:
                text += page.extract_text() + "\n"

        elif filename.lower().endswith(".docx"):
            doc = Document(io.BytesIO(file_content))
            for para in doc.paragraphs:
                text += para.text + "\n"

        elif filename.lower().endswith(".txt"):
            text = file_content.decode('utf-8', errors='ignore')

    except Exception as e:
        print(f"❌ Extraction error: {e}")
        return ""

    return text.strip()
def auto_parse_testcase(testcase: Dict) -> Dict:
    """
    Parses a test case and adds parsed input/output
    """
    raw_input = testcase.get("input", "")
    raw_output = testcase.get("output", "")
    
    # Parse input
    try:
        # Try to evaluate as Python expression
        parsed_input = eval(f"({raw_input})")
        parsed_input = list(parsed_input) if isinstance(parsed_input, tuple) else [parsed_input]
    except:
        # If parsing fails, keep as string
        parsed_input = [raw_input]
    
    # Parse output
    try:
        if raw_output.lower() in ["true", "false"]:
            parsed_output = raw_output.lower() == "true"
        else:
            parsed_output = eval(raw_output)
    except:
        parsed_output = raw_output
    
    return {
        "input": raw_input,
        "output": raw_output,
        "parsedInput": parsed_input,
        "parsedOutput": parsed_output
    }


def generate_sample_test_cases() -> List[Dict]:
    """Generates generic test cases as fallback"""
    return [
        {
            "input": "[1,2,3]",
            "output": "[1,2,3]",
            "parsedInput": [[1,2,3]],
            "parsedOutput": [1,2,3]
        },
        {
            "input": "[]",
            "output": "[]",
            "parsedInput": [[]],
            "parsedOutput": []
        }
    ]


def generate_questions_with_gemini(resume_text: str, jd_text: str, num_questions: int = 3) -> List[Dict]:
    """
    Uses Gemini AI to generate personalized coding questions based on experience level
    NO HINTS included in questions
    
    Args:
        resume_text: Candidate's resume content
        jd_text: Job description content
        num_questions: Number of questions to generate
    
    Returns:
        List of question dictionaries with test cases (NO hints)
    """
    
    if not GEMINI_API_KEY:
        print("⚠️ No Gemini API key found. Using fallback questions.")
        return []
    
    try:
        import google.generativeai as genai
        
        # Analyze experience level
        experience_level = analyze_experience_level(resume_text)
        print(f"📊 Detected Experience Level: {experience_level}")
        
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Create detailed prompt for question generation (NO HINTS)
        prompt = f"""You are an expert technical interviewer creating coding assessment questions.

**CANDIDATE RESUME:**
{resume_text[:2000]}

**JOB DESCRIPTION:**
{jd_text[:2000]}

**CANDIDATE EXPERIENCE LEVEL:** {experience_level}

CRITICAL REQUIREMENTS:
1. You MUST generate EXACTLY 3 coding questions
2. Questions MUST match the candidate's experience level ({experience_level})
3. For Entry Level: Focus on fundamental concepts, basic data structures, simple algorithms
4. For Mid Level: Include problem-solving, optimization, multiple approaches
5. For Senior Level: Complex algorithms, system design considerations, scalability
6. DO NOT include hints - candidates should solve independently

**TASK:**
Generate exactly 3 personalized coding questions that:
1. Match the candidate's {experience_level} experience and skills from resume
2. Are directly relevant to the job requirements
3. Test practical problem-solving abilities appropriate to their level
4. Include multiple test cases for validation
5. Progress appropriately in complexity for their experience level
6. NO HINTS PROVIDED - candidates work independently

**OUTPUT FORMAT (JSON only, no markdown):**
{{
  "questions": [
    {{
      "id": "uniqueFunctionName1",
      "title": "Question 1 Title",
      "category": "Data Structures",
      "description": "Clear problem statement with examples and constraints. Include: Problem description, at least 2 examples with explanations, constraints list.",
      "functionName": "functionName1",
      "testCases": [
        {{"input": "test input as string", "output": "expected output as string"}},
        {{"input": "test input 2", "output": "expected output 2"}},
        {{"input": "test input 3", "output": "expected output 3"}},
        {{"input": "edge case input", "output": "edge case output"}}
      ]
    }},
    {{
      "id": "uniqueFunctionName2",
      "title": "Question 2 Title",
      "category": "Algorithms",
      "description": "Clear problem statement with examples and constraints",
      "functionName": "functionName2",
      "testCases": [
        {{"input": "test input as string", "output": "expected output as string"}},
        {{"input": "test input 2", "output": "expected output 2"}},
        {{"input": "test input 3", "output": "expected output 3"}},
        {{"input": "edge case input", "output": "edge case output"}}
      ]
    }},
    {{
      "id": "uniqueFunctionName3",
      "title": "Question 3 Title",
      "category": "Problem Solving",
      "description": "Clear problem statement with examples and constraints",
      "functionName": "functionName3",
      "testCases": [
        {{"input": "test input as string", "output": "expected output as string"}},
        {{"input": "test input 2", "output": "expected output 2"}},
        {{"input": "test input 3", "output": "expected output 3"}},
        {{"input": "edge case input", "output": "edge case output"}}
      ]
    }}
  ]
}}

**REQUIREMENTS:**
- You MUST return EXACTLY 3 questions in the questions array
- Each question must have 4-6 test cases including edge cases
- Questions should be appropriate for {experience_level} candidates
- Make descriptions clear, professional, and include examples
- Function names should be camelCase
- Return ONLY valid JSON, no extra text or markdown
- DO NOT include markdown code blocks or backticks
- DO NOT include any difficulty field, level field, or hints field
- NO HINTS - candidates solve independently"""

        # Generate questions using Gemini
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up response - remove markdown code blocks if present
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)
        response_text = response_text.strip()
        
        # Parse JSON response
        try:
            ai_response = json.loads(response_text)
            questions = ai_response.get("questions", [])
            
            if not questions:
                print("⚠️ AI returned empty questions. Using fallback.")
                return []
            
            # Process questions - NO HINTS
            processed_questions = []
            for q in questions[:num_questions]:
                # Parse test cases
                test_cases = []
                for tc in q.get("testCases", []):
                    parsed_tc = auto_parse_testcase(tc)
                    test_cases.append(parsed_tc)
                
                # Build question object WITHOUT hints or difficulty
                question_obj = {
                    "id": q.get("id", f"question_{random.randint(1000, 9999)}"),
                    "title": q.get("title", "Coding Challenge"),
                    "category": q.get("category", "General"),
                    "description": q.get("description", "Solve the coding problem."),
                    "functionName": q.get("functionName", q.get("id", "solution")),
                    "testCases": test_cases if test_cases else generate_sample_test_cases()
                    # NO hints field
                }
                
                processed_questions.append(question_obj)
            
            print(f"✅ Generated {len(processed_questions)} AI-powered questions for {experience_level} (no hints)")
            return processed_questions
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse error: {e}")
            print(f"Response was: {response_text[:200]}")
            return []
    
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return []


def generate_mock_questions(context: str, num_questions: int = 3) -> List[Dict]:
    """
    Main function to generate coding questions
    Uses Gemini AI if available, otherwise falls back to preset questions
    NO HINTS in any questions
    
    Args:
        context: Combined resume and job description text
        num_questions: Number of questions to generate (default: 3)
    
    Returns:
        List of question dictionaries with test cases (NO hints)
    """
    
    # Try to split context into resume and JD
    parts = context.split("JOB DESCRIPTION:")
    if len(parts) == 2:
        resume_text = parts[0].replace("RESUME:", "").strip()
        jd_text = parts[1].strip()
    else:
        # If not split, use entire context for both
        resume_text = context[:len(context)//2]
        jd_text = context[len(context)//2:]
    
    # Try AI generation first
    if GEMINI_API_KEY:
        print("🤖 Attempting Gemini AI question generation (no hints)...")
        ai_questions = generate_questions_with_gemini(resume_text, jd_text, num_questions=3)
        if ai_questions:
            return ai_questions
    
    # Fallback to preset questions
    print("📋 Questions not printed")
    



# Health Check
@app.get("/")
async def root():
    return {
        "status": "active",
        "service": "AI Coding Assessment Agent",
        "version": "1.0.0",
        "ai_enabled": GEMINI_AVAILABLE
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "ai_available": GEMINI_AVAILABLE
    }

@app.post("/analyze-application")
async def analyze_application(
    resume: UploadFile = File(...), 
    jd: UploadFile = File(...),
    use_ai: bool = True
):
    """
    Analyzes resume and job description to generate personalized coding questions.
    
    Args:
        resume: Resume file (PDF/DOCX/TXT)
        jd: Job description file (PDF/DOCX/TXT)
        use_ai: Whether to use AI for question generation (default: True)
    
    Returns:
        - status: success/error
        - resume_name: uploaded resume filename
        - jd_name: uploaded JD filename
        - questions: list of generated coding challenges
        - ai_powered: whether AI was used
    """
    
    # Validate file formats
    valid_extensions = ('.pdf', '.docx', '.txt')
    if not resume.filename.lower().endswith(valid_extensions):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid Resume format. Accepted: {valid_extensions}"
        )
    
    if not jd.filename.lower().endswith(valid_extensions):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid Job Description format. Accepted: {valid_extensions}"
        )
    
    try:
        # Read file contents
        resume_content = await resume.read()
        jd_content = await jd.read()
        
        # Extract text from documents
        print(f"📄 Extracting text from {resume.filename}...")
        resume_text = extract_text_from_file(resume_content, resume.filename)
        
        print(f"📄 Extracting text from {jd.filename}...")
        jd_text = extract_text_from_file(jd_content, jd.filename)
        
        if not resume_text:
            raise HTTPException(status_code=400, detail="Failed to extract text from resume")
        
        if not jd_text:
            raise HTTPException(status_code=400, detail="Failed to extract text from job description")
        
        print(f"✅ Extracted {len(resume_text)} chars from resume, {len(jd_text)} chars from JD")
        
        # Simulate processing time
        time.sleep(0.5)
        
        # Generate questions using AI or fallback
        print("🔄 Generating coding questions...")
        combined_context = f"RESUME:\n{resume_text}\n\nJOB DESCRIPTION:\n{jd_text}"
        questions = generate_mock_questions(combined_context, num_questions=3)
        
        ai_powered = GEMINI_AVAILABLE and use_ai
        
        return {
            "status": "success",
            "resume_name": resume.filename,
            "jd_name": jd.filename,
            "resume_text": resume_text[:500],  # Preview
            "jd_text": jd_text[:500],  # Preview
            "questions": questions,
            "ai_powered": ai_powered,
            "message": f"Generated {len(questions)} {'AI-powered' if ai_powered else 'rule-based'} coding challenges"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing application: {str(e)}"
        )



@app.post("/submit-answer")
async def submit_answer(payload: dict):
    """
    Legacy endpoint - saves individual answer submission.
    Use /evaluate-code for detailed evaluation.
    """
    print(f"✅ Code submitted for: {payload.get('questionId', 'unknown')}")
    print(f"Language: {payload.get('language', 'javascript')}")
    print(f"Code length: {len(payload.get('code', ''))} characters")
    
    return {
        "status": "success",
        "message": "Code submission received",
        "questionId": payload.get("questionId")
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Starting AI Coding Assessment Backend")
    print("="*60)
    print(f"📡 Server: http://localhost:8000")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print(f"🤖 AI Status: {'Enabled' if GEMINI_AVAILABLE else 'Disabled (using fallback)'}")
    print("="*60 + "\n")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=True  # Auto-reload on code changes (dev only)
    )