// BUG HUNTERS - Platform Core JavaScript Engine

document.addEventListener('DOMContentLoaded', () => {
    initTabMonitoring();
    initExamTimer();
    initCodeEditor();
    initAutoToasts();
});

// --- Toast Notification System ---
window.showToast = function(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `cyber-toast toast-${type}`;
    
    let iconClass = 'fa-info-circle';
    if (type === 'success') iconClass = 'fa-check-circle';
    if (type === 'warning') iconClass = 'fa-exclamation-triangle';
    if (type === 'error') iconClass = 'fa-times-circle';

    toast.innerHTML = `
        <i class="fas ${iconClass}" style="font-size: 1.2rem; color: var(--cyber-cyan);"></i>
        <div style="flex-grow: 1; font-size: 0.9rem;">${message}</div>
    `;

    container.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 50);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 4500);
};

function initAutoToasts() {
    // Show any Django messages rendered in DOM
    const djangoMessages = document.querySelectorAll('.django-flash-message');
    djangoMessages.forEach(el => {
        const msg = el.dataset.message;
        const tag = el.dataset.tag || 'info';
        if (msg) showToast(msg, tag);
    });
}

// --- Anti-Cheating & Tab Switch Monitoring ---
let isHandlingTabSwitch = false;

function initTabMonitoring() {
    const examContainer = document.querySelector('[data-exam-round]');
    if (!examContainer) return; // Only monitor on competition examination screens

    const roundNumber = parseInt(examContainer.dataset.examRound, 10);
    const csrfToken = getCsrfToken();

    function triggerViolation(eventType) {
        if (isHandlingTabSwitch) return;
        isHandlingTabSwitch = true;

        fetch('/competition/api/log-violation/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({
                round_number: roundNumber,
                event_type: eventType,
                details: `Participant switched tab or lost focus (${eventType})`
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                updateViolationUI(data.violation_count, data.max_warnings);
                showTabSwitchModal(data.violation_count);
            }
        })
        .catch(err => console.error("Violation logging failed:", err))
        .finally(() => {
            setTimeout(() => { isHandlingTabSwitch = false; }, 2000);
        });
    }

    // 1. Page Visibility API
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
            triggerViolation('tab_switch');
        }
    });

    // 2. Window Blur Event
    window.addEventListener('blur', () => {
        triggerViolation('window_blur');
    });
}

function updateViolationUI(count, maxWarnings) {
    const badge = document.getElementById('violation-counter-badge');
    if (badge) {
        badge.innerHTML = `<i class="fas fa-shield-alt"></i> Violations: ${count} / ${maxWarnings}`;
        if (count >= maxWarnings) {
            badge.classList.add('flagged');
        }
    }
}

function showTabSwitchModal(count) {
    let modal = document.getElementById('tab-warning-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'tab-warning-modal';
        modal.className = 'cyber-modal';
        modal.innerHTML = `
            <div class="cyber-modal-card">
                <div class="modal-icon warning" id="warning-modal-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <h3 id="warning-modal-title" style="margin-bottom: 0.75rem; color: #fff;">Tab Switching Detected!</h3>
                <p id="warning-modal-text" style="color: var(--text-muted); line-height: 1.5; margin-bottom: 1.5rem;">
                    WARNING! Tab switching detected. Please remain on the competition page. Repeated violations may lead to disqualification.
                </p>
                <div style="font-size: 0.85rem; color: var(--cyber-cyan); margin-bottom: 1.5rem;" id="warning-modal-count">
                    Recorded Violations: ${count}
                </div>
                <button class="btn-cyber" onclick="closeTabWarningModal()" style="width: 100%; justify-content: center;">
                    <i class="fas fa-check"></i> I Understand &amp; Acknowledge
                </button>
            </div>
        `;
        document.body.appendChild(modal);
    }

    const titleEl = document.getElementById('warning-modal-title');
    const textEl = document.getElementById('warning-modal-text');
    const iconEl = document.getElementById('warning-modal-icon');
    const countEl = document.getElementById('warning-modal-count');

    if (countEl) countEl.innerText = `Recorded Violations: ${count}`;

    if (count === 1) {
        titleEl.innerText = "WARNING: Tab Switching Detected!";
        textEl.innerText = "WARNING! Tab switching detected. Please remain on the competition page. Repeated violations may lead to disqualification.";
        iconEl.className = "modal-icon warning";
    } else if (count === 2) {
        titleEl.innerText = "URGENT WARNING: Second Violation!";
        textEl.innerText = "You have switched tabs a second time! A third violation will flag your account for Administrator Review and potential penalty.";
        iconEl.className = "modal-icon danger";
    } else {
        titleEl.innerText = "ACCOUNT FLAGGED FOR REVIEW!";
        textEl.innerText = "Maximum tab-switching warnings exceeded. Your test session has been formally flagged and reported to competition proctors.";
        iconEl.className = "modal-icon danger";
    }

    modal.classList.add('active');
}

window.closeTabWarningModal = function() {
    const modal = document.getElementById('tab-warning-modal');
    if (modal) modal.classList.remove('active');
};

// --- Examination Countdown Timer Engine ---
function initExamTimer() {
    const timerContainer = document.getElementById('exam-countdown');
    if (!timerContainer) return;

    let remainingSeconds = parseInt(timerContainer.dataset.remaining, 10);
    const displayEl = document.getElementById('timer-text');
    const timerBox = document.querySelector('.timer-box');
    const form = document.getElementById('exam-form');

    function updateDisplay() {
        const mins = Math.floor(remainingSeconds / 60);
        const secs = remainingSeconds % 60;
        displayEl.innerText = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

        if (remainingSeconds <= 15) {
            timerBox.classList.add('timer-warning');
        } else {
            timerBox.classList.remove('timer-warning');
        }
    }

    updateDisplay();

    const timerInterval = setInterval(() => {
        remainingSeconds--;
        if (remainingSeconds <= 0) {
            clearInterval(timerInterval);
            displayEl.innerText = "00:00";
            showToast("Time's Up! Moving to the next question...", "warning");
            
            // Auto submit
            if (form) {
                // Add auto_submit flag
                let hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'auto_submitted';
                hiddenInput.value = 'true';
                form.appendChild(hiddenInput);
                form.submit();
            }
        } else {
            updateDisplay();
        }
    }, 1000);
}

// --- Interactive Code Editor Helper (Tab Indentation) ---
function initCodeEditor() {
    const editor = document.querySelector('.code-editor-area');
    if (!editor) return;

    editor.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            e.preventDefault();
            const start = this.selectionStart;
            const end = this.selectionEnd;
            this.value = this.value.substring(0, start) + "    " + this.value.substring(end);
            this.selectionStart = this.selectionEnd = start + 4;
        }
    });
}

// --- Live Code Runner AJAX ---
window.runCodeTest = function() {
    const editor = document.querySelector('.code-editor-area');
    const langSelect = document.getElementById('code-lang-indicator');
    const customInputEl = document.getElementById('custom-input-box');
    const consoleOutput = document.getElementById('console-output');
    const runBtn = document.getElementById('run-code-btn');

    if (!editor || !consoleOutput) return;

    const code = editor.value;
    const language = langSelect ? langSelect.dataset.lang : 'python';
    const customInput = customInputEl ? customInputEl.value : '';

    if (!code.trim()) {
        showToast("Please enter code before running.", "warning");
        return;
    }

    if (runBtn) {
        runBtn.disabled = true;
        runBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
    }

    consoleOutput.innerText = "Compiling and executing in isolated sandbox...\n";

    fetch('/competition/api/run-code/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            code: code,
            language: language,
            custom_input: customInput
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            if (data.return_code === 0) {
                consoleOutput.innerText = data.output || "[Program finished with no output]";
                consoleOutput.style.color = "#34d399";
            } else {
                consoleOutput.innerText = data.error || data.output || "Execution failed with non-zero exit code.";
                consoleOutput.style.color = "#f87171";
            }
        } else {
            consoleOutput.innerText = `Error: ${data.message}`;
            consoleOutput.style.color = "#f87171";
        }
    })
    .catch(err => {
        consoleOutput.innerText = `Network or Server Error: ${err}`;
        consoleOutput.style.color = "#f87171";
    })
    .finally(() => {
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.innerHTML = '<i class="fas fa-play"></i> Run Code';
        }
    });
};

function getCsrfToken() {
    const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
    if (cookie) return cookie.split('=')[1];
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : '';
}

