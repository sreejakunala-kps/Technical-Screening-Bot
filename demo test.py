"""
Demo Script - Test Dynamic Question Generation
Upload resume and JD files to generate personalized coding questions
"""

import os
from utils import (
    extract_text_from_file,
    generate_mock_questions,
    generate_questions_with_gemini
)


def read_file_content(filepath: str) -> bytes:
    """Read file content as bytes"""
    with open(filepath, 'rb') as f:
        return f.read()


def test_question_generation():
    """
    Test the question generation with sample files
    You can replace these with actual resume and JD files
    """
    
    print("=" * 70)
    print("AI CODING ASSESSMENT - DYNAMIC QUESTION GENERATION TEST")
    print("=" * 70)
    
    # Option 1: Use sample text (if you don't have files)
    print("\n📝 Option 1: Using sample text")
    print("-" * 70)
    
    sample_resume = """
    JANE SMITH
    Software Engineer
    jane.smith@email.com | (555) 123-4567
    
    PROFESSIONAL SUMMARY
    Experienced software engineer with 4+ years of expertise in Python, Java, and JavaScript.
    Strong background in data structures, algorithms, and full-stack development.
    Proven track record of building scalable web applications and RESTful APIs.
    
    TECHNICAL SKILLS
    • Languages: Python, Java, JavaScript, SQL
    • Frameworks: Django, Flask, Spring Boot, React
    • Tools: Git, Docker, AWS, PostgreSQL
    • Expertise: Data Structures, Algorithms, System Design, API Development
    
    WORK EXPERIENCE
    
    Senior Software Engineer | Tech Corp | 2021 - Present
    • Developed and maintained 15+ RESTful APIs serving 1M+ users
    • Optimized database queries resulting in 40% performance improvement
    • Implemented caching strategies using Redis
    • Led code reviews and mentored junior developers
    
    Software Engineer | StartupXYZ | 2019 - 2021
    • Built full-stack web applications using Python Django and React
    • Designed and implemented microservices architecture
    • Worked with agile methodologies and CI/CD pipelines
    
    EDUCATION
    B.S. in Computer Science | State University | 2019
    
    PROJECTS
    • E-commerce Platform: Built scalable backend with payment integration
    • Data Analytics Dashboard: Real-time data processing with 10K+ concurrent users
    """
    
    sample_jd = """
    BACKEND DEVELOPER POSITION
    Company: InnovateTech Solutions
    
    JOB DESCRIPTION
    We're seeking a talented Backend Developer to join our engineering team.
    You'll work on building high-performance APIs and scalable backend services.
    
    RESPONSIBILITIES
    • Design and develop RESTful APIs and microservices
    • Optimize database queries and improve system performance
    • Implement caching and data processing pipelines
    • Write clean, maintainable, and well-tested code
    • Collaborate with frontend developers and product team
    • Participate in code reviews and system design discussions
    
    REQUIRED QUALIFICATIONS
    • 3+ years of professional software development experience
    • Strong proficiency in Python or Java
    • Deep understanding of data structures and algorithms
    • Experience with relational databases (PostgreSQL, MySQL)
    • Knowledge of API design principles and best practices
    • Experience with version control (Git)
    
    PREFERRED QUALIFICATIONS
    • Experience with cloud platforms (AWS, GCP, Azure)
    • Knowledge of caching systems (Redis, Memcached)
    • Understanding of microservices architecture
    • Experience with containerization (Docker, Kubernetes)
    • Familiarity with message queues (RabbitMQ, Kafka)
    
    TECHNICAL CHALLENGES YOU'LL SOLVE
    • Scale APIs to handle millions of requests per day
    • Design efficient data models and database schemas
    • Implement real-time data processing systems
    • Optimize query performance and reduce latency
    • Build robust error handling and monitoring systems
    """
    
    # Create context
    context = f"RESUME:{sample_resume}\n\nJOB DESCRIPTION:{sample_jd}"
    
    print("\n🤖 Generating 3 personalized questions based on candidate experience...")
    print("This will take 10-20 seconds...\n")
    
    # Generate questions
    questions = generate_mock_questions(context, num_questions=3)
    
    # Display results
    print("\n" + "=" * 70)
    print(f"✅ SUCCESSFULLY GENERATED {len(questions)} QUESTIONS")
    print("=" * 70)
    
    for i, question in enumerate(questions, 1):
        print(f"\n{'='*70}")
        print(f"📌 QUESTION {i}: {question['title']}")
        print(f"{'='*70}")
        print(f"📂 Category: {question['category']}")
        print(f"🔧 Function Name: {question['functionName']}")
        
        # These fields are removed - no longer displayed
        # if 'difficulty' in question:
        #     print(f"🎯 Difficulty: {question['difficulty']}")
        
        if 'timeComplexity' in question:
            print(f"⏱️  Time Complexity: {question['timeComplexity']}")
        if 'spaceComplexity' in question:
            print(f"💾 Space Complexity: {question['spaceComplexity']}")
        
        print(f"\n📝 DESCRIPTION:")
        print("-" * 70)
        print(question['description'])
        
        print(f"\n🧪 TEST CASES ({len(question['testCases'])} total):")
        print("-" * 70)
        for j, tc in enumerate(question['testCases'], 1):
            print(f"  Test {j}:")
            print(f"    Input:  {tc['input']}")
            print(f"    Output: {tc['output']}")
            if 'explanation' in tc and tc['explanation']:
                print(f"    Why:    {tc['explanation']}")
            print()
        
        if question.get('hints'):
            print(f"💡 HINTS:")
            print("-" * 70)
            for hint in question['hints']:
                print(f"  • {hint}")
            print()
    
    # Save to JSON file
    print("\n" + "=" * 70)
    print("💾 SAVING QUESTIONS TO FILE")
    print("=" * 70)
    
    import json
    output_file = "generated_questions.json"
    
    with open(output_file, 'w') as f:
        json.dump({
            "total_questions": len(questions),
            "generated_for": {
                "resume_preview": sample_resume[:200] + "...",
                "jd_preview": sample_jd[:200] + "..."
            },
            "questions": questions
        }, f, indent=2)
    
    print(f"✅ Questions saved to: {output_file}")
    print(f"📊 Total questions: {len(questions)}")
    print(f"📈 Total test cases: {sum(len(q['testCases']) for q in questions)}")
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print("\nNext Steps:")
    print("1. Check generated_questions.json for full details")
    print("2. Use these questions in your assessment platform")
    print("3. Questions are automatically tailored to candidate's experience level")
    print("4. No difficulty labels - just personalized challenges")
    print("=" * 70)


def test_with_files(resume_path: str, jd_path: str):
    """
    Test with actual resume and JD files
    
    Args:
        resume_path: Path to resume file (PDF/DOCX/TXT)
        jd_path: Path to job description file (PDF/DOCX/TXT)
    """
    
    print("=" * 70)
    print("TESTING WITH UPLOADED FILES")
    print("=" * 70)
    
    # Extract text from files
    print(f"\n📄 Reading resume from: {resume_path}")
    resume_content = read_file_content(resume_path)
    resume_text = extract_text_from_file(resume_content, resume_path)
    print(f"✅ Extracted {len(resume_text)} characters from resume")
    
    print(f"\n📄 Reading JD from: {jd_path}")
    jd_content = read_file_content(jd_path)
    jd_text = extract_text_from_file(jd_content, jd_path)
    print(f"✅ Extracted {len(jd_text)} characters from JD")
    
    # Generate questions
    print("\n🤖 Generating personalized questions based on experience level...")
    questions = generate_questions_with_gemini(resume_text, jd_text, num_questions=3)
    
    if questions:
        print(f"\n✅ Generated {len(questions)} questions!")
        for i, q in enumerate(questions, 1):
            print(f"\n{i}. {q['title']}")
            print(f"   Category: {q['category']}")
            print(f"   Test Cases: {len(q['testCases'])}")
            # Note: No difficulty field displayed
    else:
        print("\n⚠️ Failed to generate questions with AI, using fallback")


if __name__ == "__main__":
    print("\n🚀 Starting Dynamic Question Generation Test\n")
    
    # Test with sample text (always works)
    test_question_generation()
    
    # Uncomment below to test with actual files
    # test_with_files("path/to/resume.pdf", "path/to/job_description.pdf")
    
    print("\n" + "="*70)
    print("🎉 ALL TESTS COMPLETED!")
    print("="*70)