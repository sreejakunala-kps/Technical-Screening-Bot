"""
AI-Powered Coding Assessment Utilities with Gemini AI
Generates personalized coding questions using LLM analysis
"""

import io
import json
import os
import random
import re
from typing import List, Dict, Any
from pypdf import PdfReader
from docx import Document

# Configure Gemini AI
GEMINI_API_KEY = "AIzaSyBC7-w6LUFDxTUIQGZh34p4c3exuJpuQQY"

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

# Fallback question pool (used when AI is not available)
FALLBACK_QUESTION_POOL = [
    {
        "title": "Two Sum Target",
        "fn": "twoSum",
        "keywords": ["array", "list", "search", "hashtable"],
        "category": "Arrays & Hashing",
        "description": """Given an array of integers `nums` and an integer `target`, return the indices of the two numbers that add up to `target`.

You may assume that each input has exactly one solution, and you may not use the same element twice.

**Example:**
- Input: nums = [2,7,11,15], target = 9
- Output: [0,1]
- Explanation: nums[0] + nums[1] = 2 + 7 = 9

**Constraints:**
- 2 <= nums.length <= 10^4
- Each input has exactly one solution"""
    },
    {
        "title": "Valid Parentheses",
        "fn": "validParentheses",
        "keywords": ["string", "stack", "brackets"],
        "category": "Stack",
        "description": """Given a string `s` containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.

An input string is valid if:
1. Open brackets must be closed by the same type of brackets
2. Open brackets must be closed in the correct order
3. Every close bracket has a corresponding open bracket of the same type

**Example:**
- Input: s = "()"
- Output: true

**Constraints:**
- 1 <= s.length <= 10^4
- s consists of parentheses only '()[]{}'"""
    },
    {
        "title": "Reverse Linked List",
        "fn": "reverseList",
        "keywords": ["linked list", "pointers", "recursion"],
        "category": "Linked Lists",
        "description": """Given the head of a singly linked list, reverse the list and return the reversed list.

**Example:**
- Input: head = [1,2,3,4,5]
- Output: [5,4,3,2,1]

**Constraints:**
- The number of nodes in the list is in the range [0, 5000]
- -5000 <= Node.val <= 5000

**Follow-up:** Can you solve it both iteratively and recursively?"""
    },
    {
        "title": "Longest Substring Without Repeating Characters",
        "fn": "longestSubstring",
        "keywords": ["hashmap", "string", "sliding window"],
        "category": "Sliding Window",
        "description": """Given a string `s`, find the length of the longest substring without repeating characters.

**Example:**
- Input: s = "abcabcbb"
- Output: 3
- Explanation: The answer is "abc", with length 3

**Constraints:**
- 0 <= s.length <= 5 * 10^4
- s consists of English letters, digits, symbols and spaces"""
    },
    {
        "title": "Binary Search",
        "fn": "binarySearch",
        "keywords": ["binary search", "array", "algorithm"],
        "category": "Binary Search",
        "description": """Given an array of integers `nums` which is sorted in ascending order, and an integer `target`, write a function to search `target` in `nums`. If `target` exists, return its index. Otherwise, return -1.

You must write an algorithm with O(log n) runtime complexity.

**Example:**
- Input: nums = [-1,0,3,5,9,12], target = 9
- Output: 4
- Explanation: 9 exists in nums and its index is 4

**Constraints:**
- 1 <= nums.length <= 10^4
- All integers in nums are unique
- nums is sorted in ascending order"""
    },
    {
        "title": "Merge Two Sorted Arrays",
        "fn": "mergeSorted",
        "keywords": ["array", "two pointers", "merge"],
        "category": "Arrays",
        "description": """You are given two integer arrays `nums1` and `nums2`, sorted in non-decreasing order. Merge `nums2` into `nums1` as one sorted array and return the result.

**Example:**
- Input: nums1 = [1,2,3,0,0,0], m = 3, nums2 = [2,5,6], n = 3
- Output: [1,2,2,3,5,6]

**Constraints:**
- nums1.length == m + n
- nums2.length == n
- 0 <= m, n <= 200"""
    }
]

FALLBACK_TEST_CASES = {
    "twoSum": [
        {"input": "[2,7,11,15], 9", "output": "[0,1]"},
        {"input": "[3,2,4], 6", "output": "[1,2]"},
        {"input": "[5,5], 10", "output": "[0,1]"}
    ],
    "validParentheses": [
        {"input": "\"()[]{}\"", "output": "true"},
        {"input": "\"(]\"", "output": "false"},
        {"input": "\"((()))\"", "output": "true"},
        {"input": "\"(){}}{\"", "output": "false"}
    ],
    "reverseList": [
        {"input": "[1,2,3,4,5]", "output": "[5,4,3,2,1]"},
        {"input": "[1,2]", "output": "[2,1]"},
        {"input": "[]", "output": "[]"}
    ],
    "longestSubstring": [
        {"input": "\"abcabcbb\"", "output": "3"},
        {"input": "\"bbbbb\"", "output": "1"},
        {"input": "\"pwwkew\"", "output": "3"},
        {"input": "\"\"", "output": "0"}
    ],
    "binarySearch": [
        {"input": "[-1,0,3,5,9,12], 9", "output": "4"},
        {"input": "[-1,0,3,5,9,12], 2", "output": "-1"},
        {"input": "[5], 5", "output": "0"}
    ],
    "mergeSorted": [
        {"input": "[1,2,3,0,0,0], 3, [2,5,6], 3", "output": "[1,2,2,3,5,6]"},
        {"input": "[1], 1, [], 0", "output": "[1]"},
        {"input": "[0], 0, [1], 1", "output": "[1]"}
    ]
}


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


def analyze_experience_level(resume_text: str) -> str:
    """
    Analyzes resume to determine candidate's experience level
    
    Args:
        resume_text: Candidate's resume content
    
    Returns:
        Experience level: "Entry Level", "Mid Level", or "Senior Level"
    """
    resume_lower = resume_text.lower()
    
    # Count years of experience mentioned
    year_patterns = [
        r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
        r'(\d+)\+?\s*yrs?\s+(?:of\s+)?experience',
        r'experience.*?(\d+)\+?\s*years?',
    ]
    
    years = []
    for pattern in year_patterns:
        matches = re.findall(pattern, resume_lower)
        years.extend([int(y) for y in matches])
    
    max_years = max(years) if years else 0
    
    # Check for senior indicators
    senior_keywords = ['senior', 'lead', 'principal', 'architect', 'manager', 'director', 'head of']
    senior_count = sum(1 for kw in senior_keywords if kw in resume_lower)
    
    # Check for mid-level indicators
    mid_keywords = ['mid-level', 'intermediate', 'developer ii', 'engineer ii']
    mid_count = sum(1 for kw in mid_keywords if kw in resume_lower)
    
    # Determine experience level
    if max_years >= 5 or senior_count >= 2:
        return "Senior Level"
    elif max_years >= 2 or mid_count >= 1:
        return "Mid Level"
    else:
        return "Entry Level"


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


def generate_fallback_questions(context: str, num_questions: int = 3) -> List[Dict]:
    """
    Generates questions from fallback pool when AI is unavailable
    NO HINTS included
    """
    print("📦 Using fallback question pool")
    
    context_lower = context.lower()
    
    # Analyze experience level from context
    experience_level = analyze_experience_level(context)
    print(f"📊 Detected Experience Level: {experience_level}")
    
    # Find relevant questions based on keywords
    found_keywords = set()
    for q in FALLBACK_QUESTION_POOL:
        for kw in q["keywords"]:
            if kw in context_lower:
                found_keywords.add(kw)
    
    # Prioritize matching questions
    relevant = [
        q for q in FALLBACK_QUESTION_POOL 
        if any(kw in found_keywords for kw in q["keywords"])
    ]
    
    # Select questions
    pool = relevant if relevant else FALLBACK_QUESTION_POOL
    selected = random.sample(pool, min(num_questions, len(pool)))
    
    # Build question objects WITHOUT hints or difficulty
    questions = []
    for q in selected:
        fn = q["fn"]
        test_cases = FALLBACK_TEST_CASES.get(fn, [])
        
        parsed_cases = []
        for tc in test_cases:
            parsed_cases.append(auto_parse_testcase(tc))
        
        questions.append({
            "id": fn,
            "title": q["title"],
            "category": q["category"],
            "description": q.get("description", f"Solve the problem: {q['title']}. Implement the solution efficiently."),
            "functionName": fn,
            "testCases": parsed_cases
            # NO hints field
        })
    
    return questions


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
    print("📋 Using fallback question generation (no hints)...")
    return generate_fallback_questions(context, num_questions=3)