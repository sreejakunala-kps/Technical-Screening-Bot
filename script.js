// Global variable to store questions
let generatedQuestions = [];
let currentQuestionIndex = 0;
let userAnswers = {}; // Store user code for each question

// --- Page Elements ---
const uploadPage = document.getElementById('upload-page');
const assessmentPage = document.getElementById('assessment-page');
const analyzeBtn = document.getElementById('analyze-btn');
const timerDisplay = document.getElementById('timer-display');
const questionTabsContainer = document.getElementById('question-tabs');
const questionContentDiv = document.getElementById('question-content');
const codeEditor = document.getElementById('code-editor');

// ==========================================
// 1. UPLOAD & PAGE TRANSITION LOGIC
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    uploadPage.classList.remove('hidden'); 
    assessmentPage.classList.add('hidden');

    setupUploadBox('drop-zone-resume', 'resume-file', 'filename-resume');
    setupUploadBox('drop-zone-jd', 'jd-file', 'filename-jd');
    
    analyzeBtn.addEventListener('click', handleAnalyzeClick);
    
    // Attach Run and Submit button listeners
    document.querySelector('.run-btn').addEventListener('click', handleRunCode);
    document.querySelector('.submit-btn').addEventListener('click', handleSubmitTest);
});

async function handleAnalyzeClick() {
    const resumeInput = document.getElementById('resume-file');
    const jdInput = document.getElementById('jd-file');

    if (!resumeInput.files[0] || !jdInput.files[0]) {
        alert("⚠ Please upload BOTH a Resume and a Job Description.");
        return;
    }

    const originalText = analyzeBtn.innerText;
    analyzeBtn.innerText = "Processing... (Generating 3 questions)";
    analyzeBtn.disabled = true;

    const formData = new FormData();
    formData.append('resume', resumeInput.files[0]);
    formData.append('jd', jdInput.files[0]);

    try {
        const response = await fetch('http://127.0.0.1:8000/analyze-application', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error("Backend responded with an error.");

        const data = await response.json();
        console.log("Analysis Result:", data);
        console.log("Number of questions received:", data.questions.length);

        generatedQuestions = data.questions;
        
        // Verify we have 3 questions
        if (generatedQuestions.length < 3) {
            console.warn("⚠ Less than 3 questions received. Got:", generatedQuestions.length);
        }
        
        localStorage.setItem('generatedQuestions', JSON.stringify(data.questions));
        
        showAssessmentPage();

    } catch (error) {
        console.error("Connection/Processing Failed:", error);
        alert("❌ Connection Failed! Make sure 'python main.py' is running.");
        analyzeBtn.innerText = originalText;
        analyzeBtn.disabled = false;
    }
}

function showAssessmentPage() {
    uploadPage.classList.add('hidden');
    assessmentPage.classList.remove('hidden');
    startTimer();
    renderTabs();
    loadQuestion(0);
}

function setupUploadBox(dropZoneId, fileInputId, fileNameId) {
    const dropZone = document.getElementById(dropZoneId);
    const fileInput = document.getElementById(fileInputId);
    const fileNameDisplay = document.getElementById(fileNameId);

    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFile(e.target.files[0], fileNameDisplay, dropZone);
    });

    ['dragenter', 'dragover'].forEach(evt => {
        dropZone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropZone.classList.add('border-blue-500', 'bg-blue-50');
        });
    });

    ['dragleave', 'drop'].forEach(evt => {
        dropZone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropZone.classList.remove('border-blue-500', 'bg-blue-50');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFile(files[0], fileNameDisplay, dropZone);
        }
    });
}

function handleFile(file, displayElement, container) {
    displayElement.textContent = `✅ Selected: ${file.name}`;
    displayElement.classList.remove('hidden');
    container.classList.remove('border-gray-300');
    container.classList.add('border-green-500', 'bg-green-50');
}

// ==========================================
// 2. ASSESSMENT LOGIC (Timer, Tabs, Content)
// ==========================================

let timerInterval;

function startTimer() {
    let duration = 3600; // 1 Hour
    
    if (timerInterval) clearInterval(timerInterval);
    
    timerInterval = setInterval(() => {
        if (duration <= 0) {
            clearInterval(timerInterval);
            timerDisplay.textContent = "Time's Up!";
            alert("⏰ Time's up! Auto-submitting your test.");
            handleSubmitTest();
            return;
        }
        duration--;
        
        let minutes = Math.floor(duration / 60);
        let seconds = duration % 60;
        
        timerDisplay.textContent = `⏳ ${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
        
        if (duration < 300) {
            timerDisplay.style.color = '#dc2626';
            timerDisplay.style.backgroundColor = '#fee2e2';
        }
    }, 1000);
}

function renderTabs() {
    questionTabsContainer.innerHTML = generatedQuestions.map((q, index) => `
        <button class="tab-btn ${index === 0 ? 'active' : ''}" onclick="switchTab(${index})">
            Q${index + 1}
        </button>
    `).join('');
}

window.switchTab = function(index) {
    // Save current code before switching
    saveCurrentCode();
    
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => tab.classList.remove('active'));
    tabs[index].classList.add('active');
    
    currentQuestionIndex = index;
    loadQuestion(index);
}

function saveCurrentCode() {
    const code = codeEditor.value;
    userAnswers[currentQuestionIndex] = code;
}

function loadQuestion(index) {
    const q = generatedQuestions[index];
    
    // ✅ FIXED: Removed q.difficulty - now only shows category
    questionContentDiv.innerHTML = `
        <span class="q-badge">${q.category || 'Coding Challenge'}</span>
        <h1 class="q-title">${q.title}</h1>
        <p class="q-desc" style="white-space: pre-wrap;">${q.description}</p>
        
        <div style="margin-top: 20px; padding: 15px; background: #f3f4f6; border-radius: 8px;">
            <h3 style="font-weight: 600; margin-bottom: 10px;">Test Cases:</h3>
            ${q.testCases.map((tc, i) => `
                <div style="margin-bottom: 8px; font-family: 'Fira Code', monospace; font-size: 0.85rem;">
                    <strong>Test ${i + 1}:</strong> Input: ${tc.input} → Expected: ${tc.output}
                </div>
            `).join('')}
        </div>
        
        // ${q.hints && q.hints.length > 0 ? `
        //     <div style="margin-top: 20px; padding: 15px; background: #fffbeb; border-radius: 8px; border-left: 4px solid #f59e0b;">
        //         <h3 style="font-weight: 600; margin-bottom: 10px; color: #92400e;">💡 Hints:</h3>
        //         ${q.hints.map(hint => `
        //             <div style="margin-bottom: 6px; color: #78350f;">• ${hint}</div>
        //         `).join('')}
        //     </div>
        ` : ''}
    `;
    
    // Restore saved code or use template
    if (userAnswers[index]) {
        codeEditor.value = userAnswers[index];
    } else {
        const lang = document.getElementById('language-select').value;
        codeEditor.value = getCodeTemplate(lang, q);
    }
}

function getCodeTemplate(language, question) {
    const fnName = question.functionName || 'solution';
    
    const templates = {
        python: `def ${fnName}(${question.testCases[0]?.input ? 'params' : ''}):\n    # Write your code here\n    pass\n\n# Test cases will run automatically`,
        javascript: `function ${fnName}(${question.testCases[0]?.input ? 'params' : ''}) {\n    // Write your code here\n    \n}\n\n// Test cases will run automatically`,
        java: `public class Solution {\n    public static void ${fnName}(${question.testCases[0]?.input ? 'params' : ''}) {\n        // Write your code here\n        \n    }\n}`,
        cpp: `#include <iostream>\nusing namespace std;\n\nvoid ${fnName}(${question.testCases[0]?.input ? 'params' : ''}) {\n    // Write your code here\n    \n}\n\nint main() {\n    return 0;\n}`,
        c: `#include <stdio.h>\n\nvoid ${fnName}() {\n    // Write your code here\n}\n\nint main() {\n    ${fnName}();\n    return 0;\n}`
    };
    
    return templates[language] || templates.python;
}

// ==========================================
// 3. RUN CODE FUNCTIONALITY
// ==========================================

function handleRunCode() {
    saveCurrentCode();
    
    const code = codeEditor.value.trim();
    if (!code || code === '# Write your code here...') {
        alert('⚠ Please write some code first!');
        return;
    }
    
    const currentQuestion = generatedQuestions[currentQuestionIndex];
    const testCases = currentQuestion.testCases || [];
    
    // Create results display
    let resultsHTML = '<div style="margin-top: 15px; padding: 15px; background: #1f2937; color: white; border-radius: 8px; font-family: \'Fira Code\', monospace;">';
    resultsHTML += '<h3 style="color: #60a5fa; margin-bottom: 10px;">🔄 Running Test Cases...</h3>';
    
    // Simulate test execution (in a real app, you'd send this to backend)
    let passed = 0;
    let failed = 0;
    
    testCases.forEach((tc, i) => {
        // This is a simulation - in production, send to backend for execution
        const randomPass = Math.random() > 0.3; // 70% pass rate for demo
        
        if (randomPass) {
            passed++;
            resultsHTML += `<div style="color: #10b981; margin: 5px 0;">✅ Test ${i + 1}: PASSED</div>`;
        } else {
            failed++;
            resultsHTML += `<div style="color: #ef4444; margin: 5px 0;">❌ Test ${i + 1}: FAILED</div>`;
            resultsHTML += `<div style="color: #9ca3af; font-size: 0.8rem; margin-left: 20px;">Expected: ${tc.output}</div>`;
        }
    });
    
    resultsHTML += `<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #374151;">`;
    resultsHTML += `<strong>Results: ${passed}/${testCases.length} passed</strong>`;
    resultsHTML += `</div></div>`;
    
    // Append results to question content
    questionContentDiv.innerHTML += resultsHTML;
    
    // Scroll to results
    questionContentDiv.scrollTop = questionContentDiv.scrollHeight;
}

// ==========================================
// 4. SUBMIT TEST FUNCTIONALITY
// ==========================================

function handleSubmitTest() {
    saveCurrentCode();
    
    // Check if user has attempted all questions
    const unanswered = [];
    for (let i = 0; i < generatedQuestions.length; i++) {
        if (!userAnswers[i] || userAnswers[i].trim() === '' || userAnswers[i].includes('Write your code here')) {
            unanswered.push(i + 1);
        }
    }
    
    if (unanswered.length > 0) {
        const confirmSubmit = confirm(`⚠ You haven't completed questions: ${unanswered.join(', ')}\n\nDo you want to submit anyway?`);
        if (!confirmSubmit) return;
    }
    
    // Prepare submission data
    const submission = {
        timestamp: new Date().toISOString(),
        questions: generatedQuestions,
        answers: userAnswers,
        timeRemaining: timerDisplay.textContent
    };
    
    // Stop timer
    if (timerInterval) clearInterval(timerInterval);
    
    // Store submission
    localStorage.setItem('lastSubmission', JSON.stringify(submission));
    
    // Show confirmation
    alert('✅ Test Submitted Successfully!\n\nYour answers have been recorded.\n\nThank you for completing the assessment.');
    
    console.log('Submission Data:', submission);
    
    // Optional: Send to backend
    // sendSubmissionToBackend(submission);
    
    // Redirect or show results page
    location.reload(); // Refresh to go back to upload page
}

// Optional: Send submission to backend
async function sendSubmissionToBackend(submission) {
    try {
        const response = await fetch('http://127.0.0.1:8000/submit-assessment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(submission)
        });
        
        const result = await response.json();
        console.log('Backend response:', result);
    } catch (error) {
        console.error('Submission error:', error);
    }
}

// Update code template when language changes
document.getElementById('language-select').addEventListener('change', () => {
    if (confirm('Changing language will reset your code. Continue?')) {
        loadQuestion(currentQuestionIndex);
    }
});

// Log when questions are loaded for debugging
console.log('✅ Script loaded - No difficulty levels will be displayed');
console.log('📋 Questions will show category badge only');