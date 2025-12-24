from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import time
from utils import extract_text_from_file, generate_mock_questions
from evaluator import evaluate_code_submission, generate_assessment_report

# Try to import AI capabilities
try:
    from utils import GEMINI_API_KEY
    GEMINI_AVAILABLE = bool(GEMINI_API_KEY)
    print(f"🤖 Gemini AI: {'Available' if GEMINI_AVAILABLE else 'Not configured (set GEMINI_API_KEY environment variable)'}")
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Gemini AI not installed. Using fallback question generation.")

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

@app.post("/evaluate-code")
async def evaluate_code(submission: CodeSubmission):
    """
    Evaluates a single code submission against test cases.
    
    Returns detailed evaluation including:
        - Syntax check
        - Test case results
        - Code quality metrics
        - Performance analysis
    """
    try:
        evaluation = evaluate_code_submission(
            code=submission.code,
            language=submission.language,
            test_cases=submission.testCases,
            question_id=submission.questionId
        )
        
        return {
            "status": "success",
            "questionId": submission.questionId,
            "evaluation": evaluation
        }
    
    except Exception as e:
        print(f"❌ Evaluation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation error: {str(e)}"
        )

@app.post("/submit-assessment")
async def submit_assessment(bulk: BulkSubmission):
    """
    Submits complete assessment with all question answers.
    Generates comprehensive evaluation report.
    
    Returns:
        - Overall score
        - Per-question breakdown
        - Strengths and weaknesses
        - Hiring recommendation
    """
    try:
        # Evaluate each submission
        evaluations = []
        for submission in bulk.submissions:
            eval_result = evaluate_code_submission(
                code=submission.code,
                language=submission.language,
                test_cases=submission.testCases,
                question_id=submission.questionId
            )
            evaluations.append({
                "questionId": submission.questionId,
                "evaluation": eval_result
            })
        
        # Generate comprehensive assessment report
        report = generate_assessment_report(
            candidate_name=bulk.candidateName,
            evaluations=evaluations,
            resume_context=bulk.resumeText,
            jd_context=bulk.jdText
        )
        
        return {
            "status": "success",
            "candidateName": bulk.candidateName,
            "report": report,
            "evaluations": evaluations
        }
    
    except Exception as e:
        print(f"❌ Assessment error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Assessment submission error: {str(e)}"
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