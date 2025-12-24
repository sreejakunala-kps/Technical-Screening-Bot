"""
Code Evaluation Module
Handles code execution, testing, and assessment report generation
"""

import ast
import re
from typing import List, Dict, Any
import traceback


def evaluate_code_submission(
    code: str,
    language: str,
    test_cases: List[Dict],
    question_id: str
) -> Dict[str, Any]:
    """
    Evaluates submitted code against test cases
    
    Args:
        code: The code to evaluate
        language: Programming language (python, javascript, etc.)
        test_cases: List of test cases with input/output
        question_id: Unique question identifier
    
    Returns:
        Evaluation result dictionary
    """
    
    result = {
        "questionId": question_id,
        "language": language,
        "syntaxValid": True,
        "syntaxError": None,
        "testsPassed": 0,
        "testsTotal": len(test_cases),
        "testResults": [],
        "codeQuality": {
            "readability": 0,
            "efficiency": 0,
            "style": 0
        },
        "score": 0,
        "feedback": []
    }
    
    # Check syntax first
    if language.lower() == "python":
        syntax_check = check_python_syntax(code)
        result["syntaxValid"] = syntax_check["valid"]
        result["syntaxError"] = syntax_check.get("error")
        
        if not syntax_check["valid"]:
            result["feedback"].append(f"Syntax Error: {syntax_check['error']}")
            return result
    
    # Run test cases
    for i, test_case in enumerate(test_cases):
        test_result = run_test_case(code, language, test_case, i)
        result["testResults"].append(test_result)
        
        if test_result["passed"]:
            result["testsPassed"] += 1
    
    # Calculate code quality metrics
    result["codeQuality"] = assess_code_quality(code, language)
    
    # Calculate overall score
    result["score"] = calculate_score(result)
    
    # Generate feedback
    result["feedback"] = generate_feedback(result)
    
    return result


def check_python_syntax(code: str) -> Dict[str, Any]:
    """
    Checks Python code for syntax errors
    """
    try:
        ast.parse(code)
        return {"valid": True}
    except SyntaxError as e:
        return {
            "valid": False,
            "error": f"Line {e.lineno}: {e.msg}"
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }


def run_test_case(
    code: str,
    language: str,
    test_case: Dict,
    test_number: int
) -> Dict[str, Any]:
    """
    Runs a single test case against the code
    """
    result = {
        "testNumber": test_number + 1,
        "input": test_case.get("input", ""),
        "expectedOutput": test_case.get("output", ""),
        "actualOutput": None,
        "passed": False,
        "error": None,
        "executionTime": 0
    }
    
    try:
        if language.lower() == "python":
            # Execute Python code (simplified - in production use sandboxing)
            parsed_input = test_case.get("parsedInput", [])
            expected_output = test_case.get("parsedOutput")
            
            # Create execution environment
            local_vars = {}
            exec(code, {}, local_vars)
            
            # Find the function to test
            function_name = None
            for name, obj in local_vars.items():
                if callable(obj) and not name.startswith('_'):
                    function_name = name
                    break
            
            if function_name:
                func = local_vars[function_name]
                actual_output = func(*parsed_input)
                
                result["actualOutput"] = str(actual_output)
                result["passed"] = compare_outputs(actual_output, expected_output)
            else:
                result["error"] = "No function found in code"
        
        else:
            # For other languages, mark as not implemented
            result["error"] = f"{language} execution not implemented yet"
    
    except Exception as e:
        result["error"] = f"Runtime error: {str(e)}"
        result["actualOutput"] = None
    
    return result


def compare_outputs(actual: Any, expected: Any) -> bool:
    """
    Compares actual and expected outputs
    """
    # Handle different types
    if type(actual) != type(expected):
        # Try string comparison
        return str(actual) == str(expected)
    
    # Direct comparison
    return actual == expected


def assess_code_quality(code: str, language: str) -> Dict[str, int]:
    """
    Assesses code quality metrics (simplified heuristics)
    
    Returns scores out of 100 for:
    - Readability
    - Efficiency
    - Style
    """
    quality = {
        "readability": 70,  # Base score
        "efficiency": 70,
        "style": 70
    }
    
    if language.lower() == "python":
        lines = code.split('\n')
        
        # Readability checks
        has_comments = any('#' in line for line in lines)
        has_docstring = '"""' in code or "'''" in code
        avg_line_length = sum(len(line) for line in lines) / max(len(lines), 1)
        
        if has_comments:
            quality["readability"] += 10
        if has_docstring:
            quality["readability"] += 10
        if avg_line_length < 100:
            quality["readability"] += 10
        
        # Efficiency checks (simple heuristics)
        has_loops = any(keyword in code for keyword in ['for ', 'while '])
        has_list_comp = '[' in code and 'for' in code
        
        if has_list_comp:
            quality["efficiency"] += 15
        
        # Style checks
        follows_pep8_naming = not re.search(r'def [A-Z]', code)  # Function names lowercase
        has_proper_spacing = '  ' in code  # Has indentation
        
        if follows_pep8_naming:
            quality["style"] += 15
        if has_proper_spacing:
            quality["style"] += 15
    
    # Cap at 100
    for key in quality:
        quality[key] = min(quality[key], 100)
    
    return quality


def calculate_score(evaluation: Dict) -> int:
    """
    Calculates overall score based on evaluation criteria
    
    Weighting:
    - Test cases passed: 50%
    - Code quality: 30%
    - Syntax: 20%
    """
    score = 0
    
    # Test cases (50%)
    if evaluation["testsTotal"] > 0:
        test_score = (evaluation["testsPassed"] / evaluation["testsTotal"]) * 50
        score += test_score
    
    # Code quality (30%)
    quality = evaluation["codeQuality"]
    avg_quality = (quality["readability"] + quality["efficiency"] + quality["style"]) / 3
    score += (avg_quality / 100) * 30
    
    # Syntax (20%)
    if evaluation["syntaxValid"]:
        score += 20
    
    return int(score)


def generate_feedback(evaluation: Dict) -> List[str]:
    """
    Generates human-readable feedback based on evaluation
    """
    feedback = []
    
    # Test results feedback
    passed = evaluation["testsPassed"]
    total = evaluation["testsTotal"]
    
    if passed == total:
        feedback.append(f"✅ Excellent! All {total} test cases passed.")
    elif passed > total / 2:
        feedback.append(f"✓ Good progress: {passed}/{total} test cases passed.")
    else:
        feedback.append(f"⚠️ Only {passed}/{total} test cases passed. Review the failing cases.")
    
    # Code quality feedback
    quality = evaluation["codeQuality"]
    
    if quality["readability"] < 70:
        feedback.append("💡 Tip: Add comments and use descriptive variable names for better readability.")
    
    if quality["efficiency"] < 70:
        feedback.append("⚡ Consider optimizing your algorithm for better time/space complexity.")
    
    if quality["style"] < 70:
        feedback.append("📝 Follow coding style conventions (e.g., PEP 8 for Python).")
    
    # Overall assessment
    score = evaluation["score"]
    if score >= 90:
        feedback.append("🎉 Outstanding performance!")
    elif score >= 75:
        feedback.append("👍 Good work! Minor improvements possible.")
    elif score >= 60:
        feedback.append("📚 Fair attempt. Focus on correctness and code quality.")
    else:
        feedback.append("🔧 Needs improvement. Review the problem requirements and test cases.")
    
    return feedback


def generate_assessment_report(
    candidate_name: str,
    evaluations: List[Dict],
    resume_context: str = "",
    jd_context: str = ""
) -> Dict[str, Any]:
    """
    Generates a comprehensive assessment report
    
    Args:
        candidate_name: Name of the candidate
        evaluations: List of evaluation results for each question
        resume_context: Resume text for context
        jd_context: Job description for context
    
    Returns:
        Complete assessment report
    """
    
    total_score = 0
    total_tests_passed = 0
    total_tests = 0
    
    question_summaries = []
    
    for eval_data in evaluations:
        evaluation = eval_data.get("evaluation", {})
        
        total_score += evaluation.get("score", 0)
        total_tests_passed += evaluation.get("testsPassed", 0)
        total_tests += evaluation.get("testsTotal", 0)
        
        question_summaries.append({
            "questionId": evaluation.get("questionId", "unknown"),
            "score": evaluation.get("score", 0),
            "testsPassed": evaluation.get("testsPassed", 0),
            "testsTotal": evaluation.get("testsTotal", 0),
            "feedback": evaluation.get("feedback", [])
        })
    
    avg_score = total_score / len(evaluations) if evaluations else 0
    
    # Determine recommendation
    if avg_score >= 85:
        recommendation = "Strong Hire - Candidate demonstrates excellent coding skills"
        level = "Senior/Lead"
    elif avg_score >= 70:
        recommendation = "Hire - Candidate shows solid technical abilities"
        level = "Mid-level"
    elif avg_score >= 55:
        recommendation = "Consider - Some potential but needs development"
        level = "Junior"
    else:
        recommendation = "Not Recommended - Significant skill gaps identified"
        level = "Entry-level with training"
    
    report = {
        "candidateName": candidate_name,
        "overallScore": round(avg_score, 1),
        "totalTestsPassed": total_tests_passed,
        "totalTests": total_tests,
        "passRate": round((total_tests_passed / total_tests * 100) if total_tests > 0 else 0, 1),
        "questionSummaries": question_summaries,
        "strengths": generate_strengths(evaluations),
        "weaknesses": generate_weaknesses(evaluations),
        "recommendation": recommendation,
        "suggestedLevel": level,
        "detailedAnalysis": generate_detailed_analysis(evaluations)
    }
    
    return report


def generate_strengths(evaluations: List[Dict]) -> List[str]:
    """
    Identifies candidate strengths from evaluations
    """
    strengths = []
    
    for eval_data in evaluations:
        evaluation = eval_data.get("evaluation", {})
        
        if evaluation.get("testsPassed", 0) == evaluation.get("testsTotal", 0):
            strengths.append("Excellent problem-solving accuracy")
        
        quality = evaluation.get("codeQuality", {})
        if quality.get("readability", 0) > 85:
            strengths.append("Clean, readable code")
        if quality.get("efficiency", 0) > 85:
            strengths.append("Optimized algorithms")
        if quality.get("style", 0) > 85:
            strengths.append("Good coding style and conventions")
    
    return list(set(strengths)) if strengths else ["Shows basic understanding of programming concepts"]


def generate_weaknesses(evaluations: List[Dict]) -> List[str]:
    """
    Identifies areas for improvement from evaluations
    """
    weaknesses = []
    
    for eval_data in evaluations:
        evaluation = eval_data.get("evaluation", {})
        
        if not evaluation.get("syntaxValid", True):
            weaknesses.append("Syntax errors present")
        
        pass_rate = evaluation.get("testsPassed", 0) / max(evaluation.get("testsTotal", 1), 1)
        if pass_rate < 0.5:
            weaknesses.append("Logic errors affecting correctness")
        
        quality = evaluation.get("codeQuality", {})
        if quality.get("readability", 100) < 60:
            weaknesses.append("Code readability needs improvement")
        if quality.get("efficiency", 100) < 60:
            weaknesses.append("Algorithm optimization needed")
    
    return list(set(weaknesses)) if weaknesses else []


def generate_detailed_analysis(evaluations: List[Dict]) -> str:
    """
    Generates detailed written analysis of performance
    """
    analysis = []
    
    for i, eval_data in enumerate(evaluations, 1):
        evaluation = eval_data.get("evaluation", {})
        
        question_id = evaluation.get("questionId", f"Question {i}")
        score = evaluation.get("score", 0)
        tests_passed = evaluation.get("testsPassed", 0)
        tests_total = evaluation.get("testsTotal", 0)
        
        analysis.append(
            f"**{question_id}**: Scored {score}/100 with {tests_passed}/{tests_total} test cases passing. "
        )
    
    return " ".join(analysis)