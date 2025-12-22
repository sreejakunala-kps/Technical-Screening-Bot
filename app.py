import os
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# --- Mock AI Functions (Replace with actual OpenAI/LLM calls) ---
def parse_resume(file_path):
    # In a real app, you'd use an NLP library (e.g., Spacy, NLTK)
    # or an LLM to extract keywords/skills.
    # For this example, we'll just mock the output.
    print(f"Parsing resume at: {file_path}")
    return "Python, Machine Learning, Data Structures"

def generate_coding_problem(skills):
    # This is where your AI agent shines. It takes skills and generates
    # a relevant, time-bound coding problem.
    # For this example, we mock a problem.
    if "Python" in skills:
        question = "Write a Python function `reverse_string(s)` that takes a string `s` and returns the reversed string."
        test_cases = [("hello", "olleh"), ("world", "dlrow")]
        time_limit = 180 # seconds
        return question, test_cases, time_limit
    return "No relevant skills found. Please upload a programming-focused resume.", [], 0

def evaluate_code(user_code, test_cases):
    # !!! SECURITY WARNING: Running arbitrary code is dangerous.
    # A real platform uses a sandboxed execution environment (e.g., Docker, Piston API).
    # For a simple local proof-of-concept, we'll skip safe execution.
    # Real evaluation involves:
    # 1. Executing user_code with each input in test_cases.
    # 2. Comparing the output to the expected output.
    
    # Mock evaluation:
    if "def reverse_string(s):" in user_code and "s[::-1]" in user_code:
        return "PASS", 100
    return "FAIL", 0
# -------------------------------------------------------------------

load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key') # Needed for session
app.config['UPLOAD_FOLDER'] = 'uploads' # Folder to temporarily store resumes
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'resume' not in request.files:
            return redirect(request.url)
        file = request.files['resume']
        if file.filename == '':
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # 1. AI Agent: Parse Resume
            skills = parse_resume(file_path)
            
            # 2. AI Agent: Generate Problem
            question, test_cases, time_limit = generate_coding_problem(skills)

            # Store test details in the session
            session['question'] = question
            session['test_cases'] = test_cases
            session['time_limit'] = time_limit
            
            # Clean up the uploaded file (optional, but good practice)
            os.remove(file_path)

            return redirect(url_for('start_test'))

    return render_template('index.html')


@app.route('/test', methods=['GET', 'POST'])
def start_test():
    question = session.get('question')
    time_limit = session.get('time_limit', 0)
    
    if not question:
        return redirect(url_for('index'))

    if request.method == 'POST':
        # The test has ended, or the user submitted their code
        user_code = request.form['code_input']
        test_cases = session.get('test_cases', [])

        # 3. AI Agent: Evaluate Code
        status, score = evaluate_code(user_code, test_cases)
        
        # Display results and clean up session
        session.pop('question', None)
        session.pop('test_cases', None)
        session.pop('time_limit', None)

        return render_template('results.html', score=score, status=status, user_code=user_code)

    return render_template('test.html', question=question, time_limit=time_limit)


if __name__ == '__main__':
    # Add your OpenAI API Key to a file named .env
    # SECRET_KEY='your_super_secret_key'
    # OPENAI_API_KEY='sk-...'
    app.run(debug=True)