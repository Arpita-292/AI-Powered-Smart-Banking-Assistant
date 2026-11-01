// Initialization on Load
// Auto-sanitize language: Strictly Kannada or English. Clean up legacy 'Hindi'
(function sanitizeStoredLanguage() {
    try {
        const stored = localStorage.getItem('siri_bank_lang');
        if (!stored || stored === 'Hindi' || (stored !== 'Kannada' && stored !== 'English')) {
            localStorage.setItem('siri_bank_lang', 'Kannada');
        }
    } catch(e) {}
})();

// Inject shared components immediately (skip on profile page)
if (window.location.pathname !== '/profile') {
    injectProfileModal();
}

document.addEventListener('DOMContentLoaded', () => {
    loadUserSummary();
    injectVoiceAssistantBar();

    // Pre-warm SpeechSynthesis voice cache so first response is 0ms
    if ('speechSynthesis' in window) {
        window.speechSynthesis.getVoices();
        if (window.speechSynthesis.onvoiceschanged !== undefined) {
            window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
        }
    }

    // Auto-scroll chat to bottom
    const chatBox = document.getElementById('chat-messages');
    if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
});

// Logout function
async function logout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
    } catch (e) {
        console.error(e);
    } finally {
        sessionStorage.removeItem('siri_chat_history');
        sessionStorage.removeItem('siri_chat_history_turns');
        sessionStorage.removeItem('siri_reg_flow');
        sessionStorage.removeItem('siri_pending_submit_form');
        sessionStorage.removeItem('pending_sidebar_tool');
        window.location.href = '/';
    }
}

// Fetch dashboard data
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
}

async function loadUserSummary() {
    try {
        const response = await fetch('/api/user/summary');
        if (response.ok) {
            const data = await response.json();
            currentUserData = data;

            // Update Balance Card
            if (data.accounts && data.accounts.length > 0) {
                const acc = data.accounts[0];
                const bEl = document.getElementById('main-balance');
                if (bEl) {
                    const formattedBalance = `₹${parseFloat(acc.balance).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
                    bEl.setAttribute('data-balance', formattedBalance);
                    // Check if it should be hidden
                    if (sessionStorage.getItem('balanceHidden') === 'true') {
                        bEl.innerText = '₹ ••••••';
                        const eyeIcon = document.getElementById('balance-eye-icon');
                        if (eyeIcon) eyeIcon.className = 'fa-solid fa-eye-slash';
                    } else {
                        bEl.innerText = formattedBalance;
                    }
                }
                const currentLang = localStorage.getItem('siri_bank_lang') || 'Kannada';
                const isKn = (currentLang === 'Kannada');

                const aEl = document.getElementById('main-account-number');
                if (aEl) aEl.innerText = `${isKn ? 'ಖಾತೆ' : 'Acc'}: ••••${acc.account_number.slice(-4)}`;
                
                // Update UPI ID
                const uEl = document.getElementById('main-upi-id');
                if (uEl) uEl.innerText = `${isKn ? 'ಯುಪಿಐ ಐಡಿ' : 'UPI ID'}: ${data.user.upi_id || (isKn ? 'ಹೊಂದಿಸಿಲ್ಲ' : 'Not set')}`;
            }

            // Update topbar profile image if available
            if (data.user && data.user.profile_photo) {
                document.querySelectorAll('.topbar-profile-btn').forEach(btn => {
                    btn.innerHTML = `<img src="${data.user.profile_photo}" alt="Profile" style="width:36px;height:36px;border-radius:50%;object-fit:cover;border:2px solid #6366f1;box-shadow:0 2px 6px rgba(99,102,241,0.3);display:block;">`;
                });
            }

            // Update Recent Activity List (Redesigned)
            const recentList = document.getElementById('recent-activity-list');
            if (recentList) {
                const currentLang = localStorage.getItem('siri_bank_lang') || 'Kannada';
                const isKn = (currentLang === 'Kannada');
                recentList.innerHTML = '';
                if (data.transactions && data.transactions.length > 0) {
                    data.transactions.forEach(tx => {
                        const dateObj = new Date(tx.created_at);
                        const dateStr = dateObj.toLocaleDateString(isKn ? 'kn-IN' : 'en-IN', { day: 'numeric', month: 'short' });
                        
                        // Fix: Correctly identify if it's a credit or debit for THIS user
                        let isCredit = tx.transaction_type === 'DEPOSIT';
                        if (tx.transaction_type === 'TRANSFER') {
                            isCredit = (tx.receiver_id === data.user.id);
                        }
                        
                        let icon = '<i class="fa-solid fa-arrow-right-from-bracket"></i>';
                        let iconBg = '#fee2e2';
                        let iconColor = '#ef4444';
                        
                        if(isCredit) {
                            icon = '<i class="fa-solid fa-arrow-left-long"></i>';
                            iconBg = '#d1fae5';
                            iconColor = '#10b981';
                        } else if(tx.transaction_type === 'TRANSFER' || tx.transaction_type === 'WITHDRAWAL') {
                            icon = tx.transaction_type === 'TRANSFER' ? '<i class="fa-solid fa-paper-plane"></i>' : '<i class="fa-solid fa-money-bill-transfer"></i>';
                            iconBg = tx.transaction_type === 'TRANSFER' ? '#e0e7ff' : '#fff7ed';
                            iconColor = tx.transaction_type === 'TRANSFER' ? '#6366f1' : '#f97316';
                        }

                        const onclickAction = (!isCredit && tx.transaction_type === 'TRANSFER' && tx.receiver_account) 
                            ? `onclick="prefillSidebarBankTransfer('${tx.receiver_account}')" style="cursor:pointer;"`
                            : '';

                        let txLabel = '';
                        if (isCredit) {
                            txLabel = tx.sender_name ? (isKn ? 'ಇವರಿಂದ ' + tx.sender_name : 'From ' + tx.sender_name) : (tx.description || (isKn ? 'ಹಣ ಸ್ವೀಕೃತಿ' : 'Credit'));
                        } else {
                            txLabel = tx.receiver_name ? (isKn ? 'ಇವರಿಗೆ ' + tx.receiver_name : 'To ' + tx.receiver_name) : (tx.description || (isKn ? 'ಹಣ ವರ್ಗಾವಣೆ' : 'Transfer'));
                        }

                        let typeLabel = tx.transaction_type;
                        if (isKn) {
                            if (typeLabel === 'DEPOSIT') typeLabel = 'ಠೇವಣಿ';
                            else if (typeLabel === 'WITHDRAWAL') typeLabel = 'ಹಿಂಪಡೆಯುವಿಕೆ';
                            else if (typeLabel === 'TRANSFER') typeLabel = 'ವರ್ಗಾವಣೆ';
                        }

                        recentList.innerHTML += `
                            <div class="activity-item" ${onclickAction}>
                                <div class="activity-info">
                                    <div class="activity-icon" style="background: ${iconBg}; color: ${iconColor};">
                                        ${icon}
                                    </div>
                                    <div class="activity-details">
                                        <div style="font-weight: 600; color: var(--text-dark); display:flex; align-items:center; gap:5px;">
                                            ${txLabel}
                                            ${(!isCredit && tx.transaction_type === 'TRANSFER') ? `<i class="fa-solid fa-rotate-left" style="font-size:0.7rem; color:var(--primary-color);" title="${isKn ? 'ಮತ್ತೆ ಪಾವತಿಸಿ' : 'Pay Again'}"></i>` : ''}
                                        </div>
                                        <div style="font-size: 0.75rem;">${dateStr} &bull; ${isKn ? 'ಉಲ್ಲೇಖ: TXN-' : 'TXN-'}${tx.id} &bull; ${typeLabel}</div>
                                    </div>
                                </div>
                                <div class="activity-amount ${isCredit ? 'credit' : 'debit'}">
                                    ${isCredit ? '+' : '-'} ₹${parseFloat(tx.amount).toLocaleString('en-IN')}
                                </div>
                            </div>
                        `;
                    });
                } else {
                    recentList.innerHTML = `<div style="text-align:center; padding: 20px; color: #94a3b8;">${isKn ? 'ಯಾವುದೇ ಇತ್ತೀಚಿನ ವಹಿವಾಟುಗಳಿಲ್ಲ.' : 'No recent transactions.'}</div>`;
                }
            }
        }
        loadUpcomingActivity();
        loadSuggestedPayees();
    } catch (e) {
        console.error("Dashboard fetch error:", e);
    }
}

async function executeQuickTransfer() {
    const acc = document.getElementById('transfer-acc').value;
    const amt = document.getElementById('transfer-amt').value;
    const isRecurring = document.getElementById('is-recurring').checked;
    const day = document.getElementById('recur-day').value;

    try {
        let endpoint = '/api/transfer';
        let body = { receiver_account: acc, amount: amt };
        
        if (isRecurring) {
            endpoint = '/api/standing_instruction';
            body.day_of_month = day;
        }

        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        showToast(data.message);
        if (data.success) {
            document.getElementById('quick-transfer-form').reset();
            loadUserSummary();
        }
    } catch (e) {
        showToast("Transfer failed");
    }
}

async function applyLoan() {
    const btn = document.getElementById('loan-submit-btn');
    const oldText = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
    
    const amt = document.getElementById('loan-amt').value;
    const purpose = document.getElementById('loan-purpose').value;

    try {
        const res = await fetch('/api/user/loan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: amt, purpose: purpose })
        });
        const data = await res.json();
        alert(data.message);
        btn.innerHTML = oldText;
        if (data.success) document.getElementById('loan-form').reset();
    } catch (e) {
        alert("Loan application failed");
        btn.innerHTML = oldText;
    }
}

async function loadSuggestedPayees() {
    const list = document.getElementById('suggested-users-list');
    const sideList = document.getElementById('sidebar-recent-payees');
    const sideListAlt = document.getElementById('sidebar-recent-payees-alt');
    
    if (!list && !sideList && !sideListAlt) return;
    
    try {
        const res = await fetch('/api/user/payees');
        const data = await res.json();
        allPayees = data;
        
        if (list) list.innerHTML = '';
        if (sideList) sideList.innerHTML = '';
        if (sideListAlt) sideListAlt.innerHTML = '';
        
        if (data && data.length > 0) {
            data.forEach(user => {
                const initial = user.full_name.charAt(0);
                const html = `
                    <div class="user-circle-item" onclick="prefillSidebarPay('${user.phone_number}')" style="min-width: 65px;">
                        <div class="user-avatar" style="width: 45px; height: 45px; font-size: 1rem;">${initial}</div>
                        <div class="user-circle-name" style="font-size: 0.7rem;">${user.full_name.split(' ')[0]}</div>
                    </div>
                `;
                if (list) list.innerHTML += html;
                if (sideList) sideList.innerHTML += html;
                if (sideListAlt) sideListAlt.innerHTML += html;
            });
        } else {
            const emptyMsg = '<div style="color: #94a3b8; font-size: 0.8rem;">No recent payees</div>';
            if (list) list.innerHTML = emptyMsg;
            if (sideList) sideList.innerHTML = emptyMsg;
            if (sideListAlt) sideListAlt.innerHTML = emptyMsg;
        }
    } catch (e) {
        console.error("Error loading payees:", e);
    }
}

function prefillSidebarPay(phone) {
    showSidebarAction('pay-phone');
    const input = document.getElementById('side-pay-phone');
    if (input) {
        input.value = phone;
        lookupPayeeName(phone);
        document.getElementById('side-pay-amt').focus();
    }
}

let lookupDebounceTimer = null;
async function lookupPayeeName(phone) {
    clearTimeout(lookupDebounceTimer);
    const card = document.getElementById('side-pay-recipient-card');
    const errBox = document.getElementById('side-pay-recipient-error');
    const spinner = document.getElementById('phone-lookup-spinner');
    
    if (!phone) {
        if (card) card.style.display = 'none';
        if (errBox) errBox.style.display = 'none';
        return;
    }

    const clean = phone.toString().replace(/\D/g, '');
    if (clean.length < 10) {
        if (card) card.style.display = 'none';
        if (errBox) errBox.style.display = 'none';
        return;
    }

    if (spinner) spinner.style.display = 'block';

    lookupDebounceTimer = setTimeout(async () => {
        try {
            const resp = await fetch(`/api/user/lookup-phone?phone=${encodeURIComponent(clean)}`);
            const data = await resp.json();
            if (spinner) spinner.style.display = 'none';

            if (data.found) {
                if (errBox) errBox.style.display = 'none';
                if (card) {
                    card.style.display = 'block';
                    const nameEl = document.getElementById('recipient-verified-name');
                    if (nameEl) nameEl.innerText = data.name;
                    const accEl = document.getElementById('recipient-verified-acc');
                    if (accEl) accEl.innerText = `SIRI BANK • ${data.account_number}`;
                    const avatarEl = document.getElementById('recipient-avatar-initial');
                    if (avatarEl) avatarEl.innerText = (data.name || 'U')[0].toUpperCase();
                }
            } else {
                if (card) card.style.display = 'none';
                if (errBox) {
                    errBox.style.display = 'block';
                    const errText = document.getElementById('recipient-error-text');
                    if (errText) errText.innerText = data.message || "No registered SIRI BANK user found with this number.";
                }
            }
        } catch (e) {
            if (spinner) spinner.style.display = 'none';
            console.error("Lookup error:", e);
        }
    }, 200);
}

function prefillSidebarBankTransfer(acc) {
    showSidebarAction('bank-transfer');
    const input = document.getElementById('side-bank-acc');
    if (input) {
        input.value = acc;
        document.getElementById('side-bank-amt').focus();
    }
}

let allPayees = []; // Cache for searching

async function searchPayees() {
    const query = document.getElementById('payee-search-input').value.toLowerCase();
    const list = document.getElementById('suggested-users-list');
    if (!list) return;

    if (allPayees.length === 0) {
        // Load them if not already loaded
        const res = await fetch('/api/user/payees');
        allPayees = await res.json();
    }

    const filtered = allPayees.filter(p => 
        p.full_name.toLowerCase().includes(query) || 
        p.phone_number.includes(query)
    );

    list.innerHTML = '';
    if (filtered.length > 0) {
        filtered.forEach(user => {
            const initial = user.full_name.charAt(0);
            list.innerHTML += `
                <div class="user-circle-item" onclick="prefillSidebarPay('${user.phone_number}')">
                    <div class="user-avatar">${initial}</div>
                    <div class="user-circle-name">${user.full_name.split(' ')[0]}</div>
                </div>
            `;
        });
    } else {
        list.innerHTML = '<div style="color: #94a3b8; font-size: 0.8rem; padding: 10px;">No results found</div>';
    }
}

async function loadUpcomingActivity() {
    const list = document.getElementById('upcoming-activity-list');
    if (!list) return;
    try {
        const res = await fetch('/api/user/upcoming');
        const data = await res.json();
        list.innerHTML = '';
        if (data && data.length > 0) {
            data.forEach(item => {
                list.innerHTML += `
                    <div class="activity-item">
                        <div class="activity-info">
                            <div class="activity-icon" style="background: #fef3c7; color: #d97706;">
                                <i class="fa-solid fa-clock"></i>
                            </div>
                            <div class="activity-details">
                                <div style="display:flex; align-items:center; gap:8px;">
                                    Recurring Transfer to ${item.receiver_account}
                                    <span class="upcoming-badge">Scheduled</span>
                                </div>
                                <div>Due on Day ${item.day_of_month} of month</div>
                            </div>
                        </div>
                        <div class="activity-amount" style="color: #64748b;">
                            ₹${parseFloat(item.amount).toLocaleString('en-IN')}
                        </div>
                    </div>
                `;
            });
        } else {
            list.innerHTML = '<div style="text-align:center; padding: 20px; color: #94a3b8;">No upcoming activities scheduled.</div>';
        }
    } catch (e) {
        console.error("Error loading upcoming:", e);
    }
}

function toggleBalanceVisibility() {
    const bEl = document.getElementById('main-balance');
    const eye = document.getElementById('balance-eye-icon');
    const isHidden = bEl.innerText.includes('•');
    
    if (isHidden) {
        bEl.innerText = bEl.getAttribute('data-balance');
        eye.className = 'fa-solid fa-eye';
        sessionStorage.setItem('balanceHidden', 'false');
    } else {
        bEl.innerText = '₹ ••••••';
        eye.className = 'fa-solid fa-eye-slash';
        sessionStorage.setItem('balanceHidden', 'true');
    }
}

function switchActivityTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    if (tab === 'recent') {
        document.getElementById('recent-activity-list').style.display = 'flex';
        document.getElementById('upcoming-activity-list').style.display = 'none';
    } else {
        document.getElementById('recent-activity-list').style.display = 'none';
        document.getElementById('upcoming-activity-list').style.display = 'flex';
    }
}

let currentUserData = null;

function showToast(msg) {
    const toast = document.getElementById('toast-msg') || document.getElementById('toast');
    if (!toast) {
        console.log("Toast: " + msg);
        return;
    }
    toast.innerText = msg;
    toast.classList.add('show');
    toast.style.display = 'block';
    setTimeout(() => { 
        toast.classList.remove('show');
        toast.style.display = 'none';
    }, 3000);
}

let profileModalTimeout = null;

async function openProfile() {
    console.log("openProfile() explicitly called. Width:", window.innerWidth);
    let modal = document.getElementById('siri-profile-modal-overlay');
    
    if (!modal) {
        console.log("Modal missing, injecting...");
        injectProfileModal();
        modal = document.getElementById('siri-profile-modal-overlay');
    }
    
    if (!modal) {
        alert("Fatal: Profile system failed to initialize. Please refresh.");
        return;
    }
    
    // Clear any pending close timeout
    if (profileModalTimeout) {
        clearTimeout(profileModalTimeout);
        profileModalTimeout = null;
    }
    
    // Use DIRECT INLINE STYLES to bypass all CSS conflicts
    modal.style.setProperty('display', 'flex', 'important');
    modal.style.setProperty('opacity', '1', 'important');
    modal.style.setProperty('z-index', '2147483647', 'important');
    modal.style.setProperty('visibility', 'visible', 'important');
    modal.style.setProperty('pointer-events', 'auto', 'important');
    
    // Add the class for the inner card transition
    modal.classList.add('show');
    
    console.log("Modal visibility set to flex/1/visible");

    const updateUI = () => {
        if (!currentUserData || !currentUserData.user) return;
        const user = currentUserData.user;
        const account = (currentUserData.accounts && currentUserData.accounts.length > 0) ? currentUserData.accounts[0] : { account_number: 'N/A', balance: 0, status: 'N/A' };
        
        const avatar = modal.querySelector('#prof-avatar');
        const name = modal.querySelector('#prof-name');
        const id = modal.querySelector('#prof-id');
        const upi = modal.querySelector('#prof-upi');
        const acc = modal.querySelector('#prof-acc');
        const balance = modal.querySelector('#prof-balance');
        const status = modal.querySelector('#prof-status');

        if (avatar) {
            if (user.profile_photo) {
                avatar.innerHTML = `<img src="${user.profile_photo}" alt="Profile" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">`;
                avatar.style.padding = '0';
                avatar.style.overflow = 'hidden';
            } else {
                avatar.innerText = (user.full_name || "?")[0].toUpperCase();
            }
        }
        if (name) name.innerText = user.full_name || "User";
        if (id) id.innerText = user.customer_id || "N/A";
        if (upi) upi.innerText = (user.upi_id ? user.upi_id + "@siribank" : "Not Set");
        if (acc) acc.innerText = account.account_number;
        if (balance) balance.innerText = "₹" + parseFloat(account.balance || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 });
        if (status) {
            status.innerText = account.status;
            status.style.color = (account.status === 'ACTIVE' || account.status === 'APPROVED') ? '#10b981' : '#ef4444';
        }
    };

    // If we have data, show it immediately
    if (currentUserData) {
        updateUI();
    } else {
        // Show loading in modal if no data yet
        const balance = modal.querySelector('#prof-balance');
        if (balance) balance.innerText = "Loading...";
    }

    // Refresh data in background
    try {
        await loadUserSummary();
        updateUI();
    } catch (e) {
        console.error("Failed to refresh profile data:", e);
        if (!currentUserData) {
            const balance = modal.querySelector('#prof-balance');
            if (balance) balance.innerText = "Error loading";
        }
    }
}

function closeProfile() {
    const modal = document.getElementById('siri-profile-modal-overlay');
    if (modal) {
        modal.classList.remove('show');
        if (profileModalTimeout) clearTimeout(profileModalTimeout);
        profileModalTimeout = setTimeout(() => {
            if (!modal.classList.contains('show')) {
                modal.style.setProperty('display', 'none', 'important');
                modal.style.setProperty('opacity', '0', 'important');
            }
            profileModalTimeout = null;
        }, 300);
    }
}

window.openProfile = openProfile;
window.closeProfile = closeProfile;

function injectProfileModal() {
    console.log("Checking profile modal injection...");
    if (document.getElementById('siri-profile-modal-overlay')) return;
    
    const modalHtml = `
    <div id="siri-profile-modal-overlay" class="siri-profile-modal-overlay" onclick="if(event.target === this) closeProfile()">
        <div class="profile-card-modal">
            <div class="profile-header">
                <button class="close-modal" onclick="closeProfile()"><i class="fa-solid fa-xmark"></i></button>
                <div class="profile-avatar" id="prof-avatar">?</div>
                <h2 id="prof-name" style="margin: 0; font-weight: 800;">User</h2>
                <p style="opacity: 0.8; font-size: 0.9rem; margin-top: 5px;" id="prof-upi">@siribank</p>
            </div>
            <div class="profile-body">
                <div class="profile-detail-group">
                    <div class="detail-row">
                        <span class="detail-label">Customer ID</span>
                        <span class="detail-value" id="prof-id">Loading...</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Account Number</span>
                        <span class="detail-value" id="prof-acc">Loading...</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">IFSC Code</span>
                        <span class="detail-value">SIRI0004829</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Branch</span>
                        <span class="detail-value">MAIN BRANCH (AI)</span>
                    </div>
                </div>

                <div class="profile-detail-group" style="background: #f1f5f9; padding: 15px; border-radius: 12px;">
                    <div class="detail-row" style="border: none; padding: 0;">
                        <span class="detail-label">Current Ledger Balance</span>
                        <span class="detail-value" style="color: var(--primary-color); font-size: 1.1rem;" id="prof-balance">₹--</span>
                    </div>
                    <div class="detail-row" style="border: none; padding: 5px 0 0 0;">
                        <span class="detail-label">Account Status</span>
                        <span class="detail-value" id="prof-status" style="color: #10b981; text-transform: uppercase; font-size: 0.75rem; background: #d1fae5; padding: 2px 8px; border-radius: 50px;">ACTIVE</span>
                    </div>
                </div>
            </div>
            <div class="profile-footer">
                <button class="btn-primary" onclick="location.href='/aadhaar-kyc'" style="width: 100%; justify-content: center;">
                    <i class="fa-solid fa-id-card" style="margin-right: 8px;"></i> View KYC Details
                </button>
            </div>
        </div>
    </div>`;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

async function executeQuickTransfer() {
    const acc = document.getElementById('transfer-acc').value;
    const amt = document.getElementById('transfer-amt').value;
    const isRecurring = document.getElementById('is-recurring') ? document.getElementById('is-recurring').checked : false;
    const recurDay = document.getElementById('recur-day') ? document.getElementById('recur-day').value : 1;

    if (!acc || !amt) return;

    // UI Loading state
    const btn = document.querySelector('.transfer-form button');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
    btn.disabled = true;

    try {
        let endpoint = isRecurring ? '/api/standing_instruction' : '/api/transfer';
        let payload = { receiver_account: acc, amount: amt };
        if (isRecurring) payload.day_of_month = recurDay;

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (data.success) {
            showToast(isRecurring ? "Standing Instruction Saved!" : "Transfer Successful to " + acc);
            document.getElementById('quick-transfer-form').reset();
            if (document.getElementById('recur-day-group')) document.getElementById('recur-day-group').style.display = 'none';
            loadUserSummary(); // reload balances and history
        } else {
            alert("Failed: " + data.message);
        }
    } catch (e) {
        alert("Network error processing request");
    } finally {
        btn.innerHTML = isRecurring ? 'Initialize Instruction' : 'Send Money';
        btn.disabled = false;
    }
}

/** CHATBOT LOGIC **/
const chatMessages = document.getElementById('chat-messages');
function saveChatState() {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        const clone = chatMessages.cloneNode(true);
        clone.querySelectorAll('#ai-thinking-indicator, #live-user-speech-bubble').forEach(el => el.remove());
        sessionStorage.setItem('siri_chat_history', clone.innerHTML);
    }
}

function updateAiStatus(statusType) {
    const headerStatus = document.getElementById('chat-header-status');
    const badgeText = document.getElementById('ai-badge-text');
    const badgeDot = document.querySelector('.ai-badge-dot');
    const currentLang = localStorage.getItem('siri_bank_lang') || 'Kannada';
    const isKn = (currentLang === 'Kannada');

    let textHeader = '';
    let textBadge = '';
    let dotColor = '#10b981';

    if (statusType === 'listening') {
        textHeader = isKn ? "🔴 ಕೇಳಿಸಿಕೊಳ್ಳುತ್ತಿದ್ದೇನೆ... (Listening)" : "🔴 Listening... Speak now";
        textBadge = isKn ? "🔴 ಕೇಳಿಸಿಕೊಳ್ಳುತ್ತಿದ್ದೇನೆ..." : "🔴 Listening... (30s)";
        dotColor = '#ef4444';
    } else if (statusType === 'thinking') {
        textHeader = isKn ? "⚡ ಯೋಚಿಸುತ್ತಿದೆ... (Thinking)" : "⚡ Thinking...";
        textBadge = isKn ? "⚡ ಯೋಚಿಸುತ್ತಿದೆ..." : "⚡ Thinking...";
        dotColor = '#f59e0b';
    } else if (statusType === 'speaking') {
        textHeader = isKn ? "🔊 ಮಾತನಾಡುತ್ತಿದೆ... (Speaking)" : "🔊 Speaking...";
        textBadge = isKn ? "🔊 ಮಾತನಾಡುತ್ತಿದೆ..." : "🔊 Speaking...";
        dotColor = '#3b82f6';
    } else { // standby
        textHeader = isKn ? "💤 ಸಿದ್ಧವಾಗಿದೆ (Say 'Hey Siri' or 'ನಮಸ್ಕಾರ')" : "💤 Ready (Say 'Hey Siri' or 'Namaskara')";
        textBadge = isKn ? "SIRI AI (ಹೇಳಿ: 'ಹೇ ಸಿರಿ' / 'ನಮಸ್ಕಾರ')" : "SIRI AI (Say 'Hey Siri' / 'Namaskara')";
        dotColor = '#10b981';
    }

    if (headerStatus) headerStatus.innerText = textHeader;
    if (badgeText) badgeText.innerText = textBadge;
    if (badgeDot) badgeDot.style.background = dotColor;

    // Update orb container state classes for synchronized glowing animation
    const orbContainer = document.getElementById('chat-orb-container');
    if (orbContainer) {
        orbContainer.classList.remove('state-listening', 'state-thinking', 'state-speaking', 'state-standby');
        orbContainer.classList.add(`state-${statusType || 'standby'}`);
    }
}

function appendMessage(text, sender) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}`;
    
    // Add text content
    const textSpan = document.createElement('span');
    textSpan.innerText = text;
    msgDiv.appendChild(textSpan);
    
    // Add replay button for bot
    if (sender === 'bot') {
        addReplayBtn(msgDiv, text);
    }
    
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight; // Auto-scroll
    saveChatState();
}

function showThinkingIndicator() {
    removeThinkingIndicator();
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;

    const currentLang = localStorage.getItem('siri_bank_lang') || 'Kannada';
    const thinkingText = (currentLang === 'Kannada') ? "ಸಿರಿ ಯೋಚಿಸುತ್ತಿದೆ..." : "SIRI AI is thinking...";

    const div = document.createElement('div');
    div.id = 'ai-thinking-indicator';
    div.className = 'message bot thinking-bubble';
    div.style.background = '#f1f5f9';
    div.style.padding = '10px 14px';
    div.style.borderRadius = '14px';
    div.style.marginBottom = '10px';
    div.style.boxShadow = '0 2px 8px rgba(0,0,0,0.04)';
    div.style.fontSize = '0.86rem';
    div.style.maxWidth = '85%';
    div.innerHTML = `
        <div class="thinking-content" style="display:flex; align-items:center; gap:8px; font-style:italic; color:#4f46e5;">
            <i class="fa-solid fa-sparkles fa-spin" style="color:#6366f1;"></i>
            <span>${thinkingText}</span>
            <span class="thinking-dots"><span class="dot-1">.</span><span class="dot-2">.</span><span class="dot-3">.</span></span>
        </div>
    `;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    updateAiStatus('thinking');
}

function removeThinkingIndicator() {
    const el = document.getElementById('ai-thinking-indicator');
    if (el) el.remove();
}

function updateLiveSpeechPreview(text) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;

    let preview = document.getElementById('live-user-speech-bubble');
    if (!text || text.trim().length === 0) {
        if (preview) preview.remove();
        return;
    }

    if (!preview) {
        preview = document.createElement('div');
        preview.id = 'live-user-speech-bubble';
        preview.className = 'message user live-speech';
        preview.style.background = '#e0f2fe';
        preview.style.color = '#0369a1';
        preview.style.padding = '10px 14px';
        preview.style.borderRadius = '14px';
        preview.style.marginBottom = '10px';
        preview.style.fontSize = '0.86rem';
        preview.style.alignSelf = 'flex-end';
        preview.style.maxWidth = '85%';
        chatMessages.appendChild(preview);
    }
    preview.innerHTML = `<span>🎙️ ${text} <span class="thinking-dots"><span>.</span></span></span>`;
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function clearLiveSpeechPreview() {
    const preview = document.getElementById('live-user-speech-bubble');
    if (preview) preview.remove();
}

/** PROGRESSIVE WORD-BY-WORD SPEECH STREAMING (Synchronized with speech onset) **/
function streamBotMessage(fullText, onComplete) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) {
        appendMessage(fullText, 'bot');
        if (onComplete) onComplete();
        return;
    }

    const msgDiv = document.createElement('div');
    msgDiv.className = 'message bot';
    msgDiv.style.background = 'white';
    msgDiv.style.padding = '10px 14px';
    msgDiv.style.borderRadius = '14px';
    msgDiv.style.marginBottom = '10px';
    msgDiv.style.boxShadow = '0 2px 6px rgba(0,0,0,0.05)';
    msgDiv.style.fontSize = '0.88rem';
    msgDiv.style.maxWidth = '88%';
    msgDiv.style.lineHeight = '1.45';

    const textSpan = document.createElement('span');
    textSpan.innerHTML = '<span style="display:inline-flex; gap:3px; align-items:center; opacity:0.6;"><span style="width:5px; height:5px; background:#0284c7; border-radius:50%; display:inline-block; animation:pulse 1s infinite;"></span><span style="width:5px; height:5px; background:#0284c7; border-radius:50%; display:inline-block; animation:pulse 1s infinite 0.2s;"></span><span style="width:5px; height:5px; background:#0284c7; border-radius:50%; display:inline-block; animation:pulse 1s infinite 0.4s;"></span></span>';
    msgDiv.appendChild(textSpan);
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    const words = fullText.trim().split(/\s+/);
    let started = false;
    let currentIndex = 0;
    // Human conversational word pace
    const intervalMs = Math.max(110, Math.min(190, Math.floor(3600 / Math.max(words.length, 1))));

    const startStreaming = () => {
        if (started) return;
        started = true;
        textSpan.innerHTML = '';
        if (words.length <= 1) {
            textSpan.innerText = fullText;
            addReplayBtn(msgDiv, fullText);
            saveChatState();
            if (onComplete) onComplete();
            return;
        }

        if (window._activeStreamTimer) {
            clearInterval(window._activeStreamTimer);
            window._activeStreamTimer = null;
        }

        window._activeStreamTimer = setInterval(() => {
            currentIndex++;
            textSpan.innerText = words.slice(0, currentIndex).join(' ');
            chatMessages.scrollTop = chatMessages.scrollHeight;

            if (currentIndex >= words.length) {
                clearInterval(window._activeStreamTimer);
                window._activeStreamTimer = null;
                addReplayBtn(msgDiv, fullText);
                saveChatState();
                if (onComplete) onComplete();
            }
        }, intervalMs);
    };

    window._startActiveStream = startStreaming;

    window._finishActiveStream = () => {
        if (window._activeStreamTimer) {
            clearInterval(window._activeStreamTimer);
            window._activeStreamTimer = null;
        }
        textSpan.innerText = fullText;
        addReplayBtn(msgDiv, fullText);
        saveChatState();
        if (onComplete) onComplete();
    };

    // Auto-start fallback after 250ms
    setTimeout(() => {
        if (!started) startStreaming();
    }, 250);
}

function addReplayBtn(parentDiv, text) {
    if (parentDiv.querySelector('.replay-voice-btn')) return;
    const replayBtn = document.createElement('button');
    replayBtn.innerHTML = '<i class="fa-solid fa-volume-high"></i>';
    replayBtn.className = 'replay-voice-btn';
    replayBtn.title = 'Replay voice';
    replayBtn.style.background = 'none';
    replayBtn.style.border = 'none';
    replayBtn.style.color = '#64748b';
    replayBtn.style.cursor = 'pointer';
    replayBtn.style.marginLeft = '8px';
    replayBtn.style.fontSize = '0.85rem';
    replayBtn.onclick = () => speakText(text);
    parentDiv.appendChild(replayBtn);
}

/**
 * ACOUSTIC ECHO CANCELLATION & SELF-ECHO SUPPRESSION SYSTEM
 * Keeps track of recent utterances spoken by the assistant.
 * Prevents microphone from hearing the bot's own voice and re-triggering conversation loops.
 */
window._recentBotUtterances = [];
window._latestUtteranceId = 0;
window._isBotActivelySpeaking = false;
window._botSpeechEndTime = 0;

function isSelfEcho(transcript) {
    if (!transcript) return false;
    const raw = transcript.toLowerCase().trim();
    // Normalize: strip punctuation and excessive whitespace
    const clean = raw.replace(/[.,!?:;'"(){}\[\]\\\/_\-—]/g, ' ').replace(/\s+/g, ' ').trim();
    if (!clean || clean.length < 2) return false;

    // Explicit allow-list for command/confirmation words that must NEVER be suppressed as echo
    const commandWords = [
        'yes', 'no', 'submit', 'cancel', 'proceed', 'confirm', 'ok', 'okay', 'done', 'stop', 'wait',
        'login', 'register', 'balance', 'transfer', 'pay', 'kyc', 'otp',
        'ಹೌದು', 'ಬೇಡ', 'ಸಲ್ಲಿಸಿ', 'ಸಲ್ಲಿಸು', 'ಸರಿ', 'ರದ್ದು', 'ಖಂಡಿತ', 'ಮುಂದುವರಿಸಿ', 'ಲಾಗಿನ್', 'ನೋಂದಣಿ', 'ಒಟಿಪಿ'
    ];
    const userWords = clean.split(' ').filter(w => w.length > 0);
    // If user's utterance consists of 1-3 words that are standard commands or confirmation words,
    // it is NEVER an acoustic echo!
    if (userWords.length <= 3 && userWords.some(w => commandWords.includes(w))) {
        return false;
    }

    const timeSinceSpeech = Date.now() - (window._botSpeechEndTime || 0);

    const utterances = window._recentBotUtterances || [];
    for (let utt of utterances) {
        if (!utt) continue;
        const cleanUtt = utt.toLowerCase().replace(/[.,!?:;'"(){}\[\]\\\/_\-—]/g, ' ').replace(/\s+/g, ' ').trim();
        
        // 1. Exact match (whole utterance matches)
        if (clean === cleanUtt) {
            return true;
        }

        // 2. Transcript is a meaningful multi-word phrase inside bot utterance
        // Must be at least 3 words and at least 15 characters to prevent matching single words!
        if (userWords.length >= 3 && clean.length >= 15 && cleanUtt.includes(clean)) {
            return true;
        }

        // 3. Bot utterance is a substring of transcript
        if (cleanUtt.length >= 15 && clean.includes(cleanUtt)) {
            return true;
        }

        // 4. Word-level similarity: If 70% or more of words in clean match words in cleanUtt (min 3 words)
        const words = clean.split(' ').filter(w => w.length > 1);
        if (words.length >= 3) {
            const uttWords = new Set(cleanUtt.split(' ').filter(w => w.length > 1));
            const matchCount = words.filter(w => uttWords.has(w)).length;
            if (matchCount / words.length >= 0.70) {
                return true;
            }
        }
    }

    // Common bot ending phrases that frequently echo from laptop speakers
    const commonBotEndings = [
        "how can i help you today", "how can i help you", "how can i assist you today", "how can i assist you",
        "i am here to assist you", "with your banking needs", "assist you with your banking needs",
        "certainly i will assist you", "can i help you today", "help you today",
        "ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ", "ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ", "ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ",
        "ಬ್ಯಾಂಕಿಂಗ್ ಸೇವೆಗಳಿಗೆ ಸ್ವಾಗತ", "ಧನ್ಯವಾದಗಳು"
    ];
    for (let phrase of commonBotEndings) {
        const cleanPhrase = phrase.replace(/[.,!?:;'"(){}\[\]\\\/_\-—]/g, ' ').trim();
        if (clean === cleanPhrase || (clean.length >= 15 && (clean.includes(cleanPhrase) || cleanPhrase.includes(clean)))) {
            if (timeSinceSpeech < 5000) {
                return true;
            }
        }
    }

    return false;
}

/** NATURAL HUMAN VOICE AUDIO SYNTHESIS ENGINE (Instant Low-Latency Human Speech) **/
function speakText(text, explicitLang) {
    if (!text) return;

    const cleanText = text.replace(/<[^>]*>?/gm, '').trim().substring(0, 1500);
    if (!cleanText) return;

    const utteranceId = ++window._latestUtteranceId;

    if (!window._recentBotUtterances) window._recentBotUtterances = [];
    window._recentBotUtterances.push(cleanText.toLowerCase());
    if (window._recentBotUtterances.length > 10) window._recentBotUtterances.shift();

    window._isBotActivelySpeaking = true;
    window._botSpeechEndTime = Date.now() + 60000;

    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
    }
    if (window.currentVoiceAudio) {
        try {
            window.currentVoiceAudio.pause();
            window.currentVoiceAudio.currentTime = 0;
            window.currentVoiceAudio.src = '';
        } catch(e){}
        window.currentVoiceAudio = null;
    }

    const hasKannada = /[\u0C80-\u0CFF]/.test(cleanText);
    const configuredLang = explicitLang || localStorage.getItem('siri_bank_lang') || 'English';
    const speechLang = hasKannada ? 'Kannada' : (configuredLang === 'Kannada' ? 'Kannada' : 'English');

    let ttsText = cleanText;
    if (hasKannada || speechLang === 'Kannada') {
        ttsText = ttsText.replace(/(?<=[,\s(])0(?=[,\s)]|$)/g, 'ಸೊನ್ನೆ').replace(/\b0\b/g, 'ಸೊನ್ನೆ');
    } else {
        ttsText = ttsText.replace(/(?<=[,\s(])0(?=[,\s)]|$)/g, 'zero').replace(/\b0\b/g, 'zero');
    }

    if (typeof SiriSpeechEngine !== 'undefined') {
        SiriSpeechEngine.onSpeechStart();
    }

    // Direct High-Speed Backend Voice Stream (/api/tts - Original Google Neural Voice)
    const ttsUrl = `/api/tts?text=${encodeURIComponent(ttsText)}&lang=${encodeURIComponent(speechLang)}`;
    let fallbackTriggered = false;
    const audio = new Audio(ttsUrl);
    window.currentVoiceAudio = audio;

    audio.onplay = () => {
        if (utteranceId !== window._latestUtteranceId) {
            try { audio.pause(); } catch(e){}
            return;
        }
        updateAiStatus('speaking');
        // Instantly start progressive word streaming on the chat bubble when voice begins!
        if (typeof window._startActiveStream === 'function') {
            window._startActiveStream();
        }
    };

    audio.onended = () => {
        if (utteranceId !== window._latestUtteranceId) return;
        if (typeof window._finishActiveStream === 'function') {
            window._finishActiveStream();
        }
        window.currentVoiceAudio = null;
        window._botSpeechEndTime = Date.now();

        if (typeof window._onBotSpeechEndOnce === 'function') {
            const cb = window._onBotSpeechEndOnce;
            window._onBotSpeechEndOnce = null;
            cb();
        }

        setTimeout(() => {
            if (utteranceId === window._latestUtteranceId) {
                window._isBotActivelySpeaking = false;
                if (typeof SiriSpeechEngine !== 'undefined') {
                    SiriSpeechEngine.onSpeechEnd();
                }
            }
        }, 350);
    };

    const triggerFallback = (reason) => {
        if (utteranceId !== window._latestUtteranceId) return;
        if (reason && (reason.name === 'AbortError' || (typeof reason === 'string' && reason.includes('abort')))) return;
        if (!fallbackTriggered && window.currentVoiceAudio === audio) {
            fallbackTriggered = true;
            window.currentVoiceAudio = null;
            speakWithBrowserSpeechSynthesis(ttsText, speechLang, utteranceId);
        }
    };

    audio.onerror = () => triggerFallback("audio.onerror");

    const playPromise = audio.play();
    if (playPromise !== undefined) {
        playPromise.then(() => {
            if (typeof window._startActiveStream === 'function') {
                window._startActiveStream();
            }
        }).catch(err => {
            if (err.name !== 'AbortError') triggerFallback(err);
        });
    }
}

function speakWithBrowserSpeechSynthesis(text, currentLang, utteranceId, presetVoice) {
    if (utteranceId && utteranceId !== window._latestUtteranceId) return;
    if (!('speechSynthesis' in window)) {
        window._isBotActivelySpeaking = false;
        if (typeof SiriSpeechEngine !== 'undefined') SiriSpeechEngine.onSpeechEnd();
        return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    window._activeUtterance = utterance;

    const langMap = { 'English': 'en-US', 'Kannada': 'kn-IN' };
    const targetLang = langMap[currentLang] || 'kn-IN';
    utterance.lang = targetLang;

    if (presetVoice) {
        utterance.voice = presetVoice;
    } else {
        const voices = window.speechSynthesis.getVoices();
        let selectedVoice = null;
        if (currentLang === 'English') {
            selectedVoice = voices.find(v => (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Neural') || v.name.includes('Jenny') || v.name.includes('Aria') || v.name.includes('Guy')) && v.lang.startsWith('en'))
                || voices.find(v => v.lang.startsWith('en'));
        } else {
            selectedVoice = voices.find(v => v.lang.includes('kn') || v.name.includes('Kannada') || v.name.includes('ಕನ್ನಡ'));
        }
        if (selectedVoice) utterance.voice = selectedVoice;
    }

    // Natural human conversational rate and pitch
    utterance.rate = currentLang === 'English' ? 1.02 : 0.95;
    utterance.pitch = 1.0;

    utterance.onstart = () => {
        if (utteranceId && utteranceId !== window._latestUtteranceId) return;
        updateAiStatus('speaking');
        if (typeof window._startActiveStream === 'function') {
            window._startActiveStream();
        }
    };

    utterance.onend = () => {
        if (utteranceId && utteranceId !== window._latestUtteranceId) return;
        if (typeof window._finishActiveStream === 'function') {
            window._finishActiveStream();
        }
        window._activeUtterance = null;
        window._botSpeechEndTime = Date.now();
        if (typeof window._onBotSpeechEndOnce === 'function') {
            const cb = window._onBotSpeechEndOnce;
            window._onBotSpeechEndOnce = null;
            cb();
        }
        setTimeout(() => {
            if (!utteranceId || utteranceId === window._latestUtteranceId) {
                window._isBotActivelySpeaking = false;
                if (typeof SiriSpeechEngine !== 'undefined') {
                    SiriSpeechEngine.onSpeechEnd();
                }
            }
        }, 350);
    };

    utterance.onerror = () => {
        if (utteranceId && utteranceId !== window._latestUtteranceId) return;
        if (typeof window._finishActiveStream === 'function') {
            window._finishActiveStream();
        }
        window._activeUtterance = null;
        window._botSpeechEndTime = Date.now();
        if (typeof window._onBotSpeechEndOnce === 'function') {
            const cb = window._onBotSpeechEndOnce;
            window._onBotSpeechEndOnce = null;
            cb();
        }
        setTimeout(() => {
            if (!utteranceId || utteranceId === window._latestUtteranceId) {
                window._isBotActivelySpeaking = false;
                if (typeof SiriSpeechEngine !== 'undefined') {
                    SiriSpeechEngine.onSpeechEnd();
                }
            }
        }, 400);
    };

    const resumeTimer = setInterval(() => {
        if (window.speechSynthesis.speaking) {
            window.speechSynthesis.pause();
            window.speechSynthesis.resume();
        } else {
            clearInterval(resumeTimer);
        }
    }, 10000);

    window.speechSynthesis.speak(utterance);
}

async function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    if (!chatInput) return;
    const text = chatInput.value.trim();
    if (!text) return;

    clearLiveSpeechPreview();
    // Show user message
    appendMessage(text, 'user');
    chatInput.value = '';

    // Show animated thinking bubble
    showThinkingIndicator();

    // Mute mic while awaiting bot response
    if (typeof SiriSpeechEngine !== 'undefined') {
        SiriSpeechEngine.onSpeechStart();
    }

    // Retrieve conversation history for memory
    let history = [];
    try {
        const savedHistory = sessionStorage.getItem('siri_chat_history_turns');
        if (savedHistory) history = JSON.parse(savedHistory);
    } catch(e){}

    try {
        const currentLang = localStorage.getItem('siri_bank_lang') || 'Kannada';
        const currentPage = window.location.pathname;
        let currentTab = '';
        if (currentPage === '/' || currentPage === '/login' || currentPage === '/register' || currentPage === '/signup') {
            const regForm = document.getElementById('register-form');
            const isRegVisible = regForm && regForm.style.display !== 'none';
            currentTab = isRegVisible ? 'register' : 'login';
        } else if (currentPage === '/aadhaar-kyc') {
            currentTab = 'kyc';
        } else if (currentPage === '/pay') {
            currentTab = 'pay';
        } else if (currentPage === '/atm-services') {
            currentTab = 'atm';
        } else if (currentPage === '/request-history') {
            currentTab = 'history';
        } else {
            currentTab = 'dashboard';
        }

        let siriRf = {};
        try { siriRf = JSON.parse(sessionStorage.getItem('siri_reg_flow') || '{}'); } catch(e){}
        const hasPhoto = !!(window.regPhotoBase64 || siriRf.photo || document.getElementById('reg_has_photo')?.value === 'true' || document.getElementById('photo_preview_wrap')?.style.display === 'flex');
        const hasIdProof = !!(window.regIdProofBase64 || siriRf.id_proof || document.getElementById('reg_has_id_proof')?.value === 'true' || document.getElementById('id_preview_wrap')?.style.display === 'flex');

        const formState = {
            name: document.getElementById('reg_name')?.value?.trim() || '',
            email: document.getElementById('reg_email')?.value?.trim() || '',
            phone: document.getElementById('reg_phone')?.value?.trim() || '',
            aadhaar: document.getElementById('reg_aadhaar')?.value?.trim() || '',
            password: document.getElementById('reg_password')?.value?.trim() || '',
            photo: hasPhoto ? 'true' : '',
            id_proof: hasIdProof ? 'true' : '',
            identifier: document.getElementById('identifier')?.value?.trim() || '',
            kyc_name: document.getElementById('kyc-full-name')?.value?.trim() || '',
            kyc_dob: document.getElementById('kyc-dob')?.value?.trim() || '',
            kyc_aadhaar: document.getElementById('kyc-aadhaar-num')?.value?.trim() || '',
            kyc_otp: document.getElementById('kyc-otp-input')?.value?.trim() || ''
        };

        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                language: currentLang,
                history: history,
                page: currentPage,
                tab: currentTab,
                form_state: formState
            })
        });
        const data = await response.json();

        // Remove thinking indicator
        removeThinkingIndicator();

        // Automatic language synchronization based on use
        if (data.switch_language && (data.switch_language === 'Kannada' || data.switch_language === 'English')) {
            syncVoiceLanguage(data.switch_language);
        }

        // Save conversation memory turns & registration flow state
        if (data.history) {
            sessionStorage.setItem('siri_chat_history_turns', JSON.stringify(data.history));
        }
        if (data.reg_flow) {
            sessionStorage.setItem('siri_reg_flow', JSON.stringify(data.reg_flow));
        }

        if (data.reply) {
            // Speak audio and stream words progressively while speaking!
            updateAiStatus('speaking');
            speakText(data.reply);
            streamBotMessage(data.reply);
        } else {
            appendMessage("System error. Please try again.", 'bot');
            if (typeof SiriSpeechEngine !== 'undefined') SiriSpeechEngine.onSpeechEnd();
        }

        // Execute voice form filling, navigation, or screen reading actions
        handleVoiceActions(data);

        if (data.intent === 'ATM_CARD_REQUEST' || data.intent === 'AADHAAR_LINK_REQUEST') {
            if (typeof loadUserSummary === 'function') loadUserSummary();
        }

    } catch (e) {
        removeThinkingIndicator();
        console.error("Chat fetch error:", e);
        appendMessage("Offline. Cannot connect to SIRI BANK.", 'bot');
        if (typeof SiriSpeechEngine !== 'undefined') SiriSpeechEngine.onSpeechEnd();
    }
}

/** 
 * UNIFIED MASTER SPEECH & WAKE-WORD ENGINE
 * 
 * Manages hands-free wake word listening, active voice commands, audio earcon chimes,
 * and conversational turn-taking with zero conflicts, audio bleed, or browser crashes.
 * Supported Languages: Kannada (kn-IN) and English (en-US). Zero Hindi.
 **/
const SiriSpeechEngine = (function () {
    const STATE_IDLE = 'IDLE';
    const STATE_WAKE_WORD = 'WAKE_WORD';
    const STATE_COMMAND = 'COMMAND';
    const STATE_SPEAKING = 'SPEAKING';

    let state = STATE_IDLE;
    let recognizer = null;
    let isStarting = false;
    let isRunning = false;
    let commandTimeoutTimer = null;
    let speechEndDebounceTimer = null;
    let audioContext = null;

    const wakeWords = [
        'hey siri', 'siri', 'hey gemini', 'gemini', 'siri bank', 'hello bank', 'bank',
        'ನಮಸ್ಕಾರ', 'ನಮಸ್ತೆ', 'ಸಿರಿ', 'ಹೇಸಿರಿ', 'ಹೇಸರಿ', 'ಹೆಸರಿ', 'ಹೇ ಸಿರಿ', 'ಹಾಯ್ ಸಿರಿ', 'ಹೇಯ್ ಸಿರಿ',
        'ಹಲೋ ಸಿರಿ', 'ಹಲೋ ಬ್ಯಾಂಕ್', 'ಸಿರಿ ಬ್ಯಾಂಕ್', 'ಬ್ಯಾಂಕ್', 'namaskara', 'namaste'
    ];

    // Regex matching any wake word prefix with or without spaces, Kannada or English
    const wakeWordPrefixRegex = /^(?:hey\s+|hi\s+|hello\s+|ಹೇ\s*|ಹಾಯ್\s*|ಹಲೋ\s*|ಹೇಯ್\s*)?(?:siri|gemini|siri\s*bank|bank|ಸಿರಿ|ಸರಿ|ಜೆಮಿನಿ|ಜಮಿನಿ|ಸಿರಿ\s*ಬ್ಯಾಂಕ್|ಬ್ಯಾಂಕ್|ನಮಸ್ಕಾರ|ನಮಸ್ತೆ|namaskara|namaste|ಹೇಸಿರಿ|ಹೇಸರಿ|ಹೆಸರಿ|ಹಾಯ್ಸಿರಿ)[\s,.:!?-]*/i;

    function extractWakeWordAndCommand(transcript) {
        if (!transcript) return { isWakeWord: false, isOnlyWake: true, command: "" };
        const text = transcript.trim();
        const lower = text.toLowerCase();

        const match = text.match(wakeWordPrefixRegex);
        let isWakeWord = false;
        let command = "";

        if (match && match[0].length > 0) {
            isWakeWord = true;
            command = text.slice(match[0].length).trim();
        } else {
            const foundLoose = wakeWords.some(w => lower.includes(w.toLowerCase()));
            if (foundLoose) {
                isWakeWord = true;
                command = text.replace(wakeWordPrefixRegex, '').trim();
            }
        }

        // Clean leading filler words right after wake-up (e.g., "ಹೇಳು", "ಹೇಳಿ", "ದಯವಿಟ್ಟು", "please")
        command = command.replace(/^(?:ಹೇಳು|ಹೇಳಿ|ದಯವಿಟ್ಟು|ಪ್ಲೀಸ್|please|tell\s+me|can\s+you)[\s,.:!?-]*/i, '').trim();

        // Check if remaining text is empty or just another greeting/wake token
        const isOnlyWake = (command.length < 2 || /^(?:siri|gemini|ಸಿರಿ|ಸರಿ|ಬ್ಯಾಂಕ್|ನಮಸ್ಕಾರ|ನಮಸ್ತೆ|hey|hi|hello)$/i.test(command));

        return {
            isWakeWord: isWakeWord,
            isOnlyWake: isOnlyWake,
            command: isOnlyWake ? "" : command
        };
    }

    function getAudioContext() {
        if (!audioContext) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (AudioCtx) audioContext = new AudioCtx();
        }
        if (audioContext && audioContext.state === 'suspended') {
            audioContext.resume().catch(() => {});
        }
        return audioContext;
    }

    function playChime(type = 'wake') {
        try {
            const ctx = getAudioContext();
            if (!ctx) return;
            const now = ctx.currentTime;
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';

            if (type === 'wake') {
                // Cheerful 200ms dual chime (587.33Hz D5 -> 880Hz A5)
                osc.frequency.setValueAtTime(587.33, now);
                osc.frequency.exponentialRampToValueAtTime(880, now + 0.12);
                gain.gain.setValueAtTime(0.22, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.28);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(now);
                osc.stop(now + 0.3);
            } else if (type === 'cancel') {
                // Soft falling cancel tone (659.25Hz -> 440Hz)
                osc.frequency.setValueAtTime(659.25, now);
                osc.frequency.exponentialRampToValueAtTime(440, now + 0.15);
                gain.gain.setValueAtTime(0.16, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(now);
                osc.stop(now + 0.26);
            }
        } catch (e) {
            console.debug("Chime audio notice:", e);
        }
    }

    const INACTIVITY_TIMEOUT_MS = 30000; // 30 seconds conversational listening!

    function resetInactivityTimer() {
        if (commandTimeoutTimer) clearTimeout(commandTimeoutTimer);
        if (state !== STATE_COMMAND) return;

        commandTimeoutTimer = setTimeout(() => {
            if (state === STATE_COMMAND) {
                console.log("[SiriSpeechEngine] 30s inactivity reached. Returning to passive wake-word standby.");
                playChime('cancel');
                state = STATE_WAKE_WORD;
                updateMicUI();
                updateAiStatus('standby');
                const chatInput = document.getElementById('chat-input');
                if (chatInput) {
                    const currentLang = localStorage.getItem('siri_bank_lang') || 'Kannada';
                    chatInput.placeholder = (currentLang === 'Kannada') ? "ಮಾತನಾಡಿ ಅಥವಾ ಟೈಪ್ ಮಾಡಿ..." : "Type a message or speak...";
                }
            }
        }, INACTIVITY_TIMEOUT_MS);
    }

    function init() {
        if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
            console.warn("Web Speech Recognition not supported in this browser.");
            return;
        }
        if (recognizer) return;

        try {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognizer = new SpeechRecognition();
            recognizer.continuous = true;
            recognizer.interimResults = true; // Enables real-time live streaming text!

            updateRecognizerLanguage();

            recognizer.onstart = function () {
                isStarting = false;
                isRunning = true;
                console.log("[SiriSpeechEngine] Started successfully, state:", state);
                updateMicUI();
            };

            recognizer.onresult = function (event) {
                if (window._isBotActivelySpeaking || (Date.now() - (window._botSpeechEndTime || 0) < 300)) {
                    return; // Drop echo while bot is speaking or during 300ms acoustic grace period
                }

                resetInactivityTimer(); // Active speech resets 30-sec idle standby timer!

                let interimTranscript = '';
                let finalTranscript = '';

                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    const trans = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += trans;
                    } else {
                        interimTranscript += trans;
                    }
                }

                const chatInput = document.getElementById('chat-input');
                const chatContainer = document.getElementById('chat-container');
                const isChatOpen = chatContainer && chatContainer.classList.contains('open');

                const liveText = (finalTranscript + ' ' + interimTranscript).trim();

                // Live Text Stream: Display interim words in real-time as user speaks!
                if (liveText.length > 0 && !isSelfEcho(liveText)) {
                    if (chatInput) {
                        chatInput.value = liveText;
                    }
                    if (isChatOpen || state === STATE_COMMAND) {
                        updateLiveSpeechPreview(liveText);
                    }
                }

                // 1. If currently in ACTIVE COMMAND listening mode or chat is open:
                if (state === STATE_COMMAND || isChatOpen) {
                    // Confirmed sentence received from speech engine -> auto-answer immediately!
                    if (finalTranscript.trim().length > 0) {
                        const cleanFinal = finalTranscript.trim();
                        if (isSelfEcho(cleanFinal)) {
                            console.warn("[SiriSpeechEngine] Self-echo suppressed:", cleanFinal);
                            if (chatInput && isSelfEcho(chatInput.value)) chatInput.value = '';
                            clearLiveSpeechPreview();
                            return;
                        }
                        console.log(`[SiriSpeechEngine] Confirmed question: "${cleanFinal}". Auto-answering immediately!`);
                        if (speechEndDebounceTimer) clearTimeout(speechEndDebounceTimer);
                        handleCommandTranscript(cleanFinal);
                        return;
                    }

                    // Smart End-of-Speech Auto-Answer (Natural pause detection):
                    // When user speaks and pauses for 2000ms (giving ample time for numbers/PINs),
                    // automatically answer without waiting for manual send.
                    if (interimTranscript.trim().length >= 2) {
                        const candidate = liveText.trim();
                        // Never auto-submit on partial/incomplete digit fragments like "12" or "1 2"
                        const isShortDigits = /^\d{1,5}$/.test(candidate.replace(/\s+/g, ''));
                        if (!isSelfEcho(candidate) && !isShortDigits) {
                            if (speechEndDebounceTimer) clearTimeout(speechEndDebounceTimer);
                            const isQuickConfirm = /^(yes|submit|confirm|proceed|ok|okay|no|cancel|click|capture|take|retake|use|ಹೌದು|ಸಲ್ಲಿಸಿ|ಸಲ್ಲಿಸು|ಸರಿ|ಬೇಡ|ಕ್ಲಿಕ್|ಮತ್ತೆ|ದೃಢೀಕರಿಸಿ|ಬಳಸಿ)$/i.test(candidate);
                            const delay = isQuickConfirm ? 350 : 2000;
                            speechEndDebounceTimer = setTimeout(() => {
                                if (state === STATE_COMMAND || isChatOpen) {
                                    console.log(`[SiriSpeechEngine] Natural speech pause detected (${delay}ms). Auto-answering: "${candidate}"`);
                                    handleCommandTranscript(candidate);
                                }
                            }, delay);
                        }
                    }
                    return;
                }

                // 2. In WAKE_WORD mode (passive standby):
                if (finalTranscript.trim().length > 0) {
                    clearLiveSpeechPreview();
                    const cleanFinal = finalTranscript.trim();
                    if (isSelfEcho(cleanFinal)) return;

                    const extraction = extractWakeWordAndCommand(cleanFinal);
                    if (extraction.isWakeWord) {
                        console.log("[SiriSpeechEngine] Wake word recognized:", cleanFinal);
                        playChime('wake');
                        openChat();

                        if (!extraction.isOnlyWake && extraction.command.length > 1) {
                            if (isSelfEcho(extraction.command)) return;
                            console.log("[SiriSpeechEngine] One-shot command detected. Answering immediately:", extraction.command);
                            handleCommandTranscript(extraction.command);
                        } else {
                            console.log("[SiriSpeechEngine] Wake-up only. Entering active command listening mode.");
                            enterCommandListeningMode();
                        }
                    }
                }
            };

            recognizer.onerror = function (event) {
                isStarting = false;
                if (event.error === 'no-speech') {
                    return; // Normal idle silence
                }
                if (event.error === 'aborted') {
                    isRunning = false;
                    return;
                }
                console.warn("[SiriSpeechEngine] Notice:", event.error);
                if (event.error === 'not-allowed') {
                    isRunning = false;
                    state = STATE_IDLE;
                    updateMicUI();
                    updateAiStatus('standby');
                }
            };

            recognizer.onend = function () {
                isRunning = false;
                isStarting = false;
                console.log("[SiriSpeechEngine] Ended. Current state:", state);

                if (state === STATE_WAKE_WORD || state === STATE_COMMAND) {
                    setTimeout(() => {
                        safeStart();
                    }, 400);
                } else {
                    updateMicUI();
                }
            };

            state = STATE_WAKE_WORD;
            safeStart();
        } catch (e) {
            console.debug("Wake word init waiting for interaction:", e);
        }
    }

    function updateRecognizerLanguage() {
        if (!recognizer) return;
        const currentLang = localStorage.getItem('siri_bank_lang') || 'English';
        recognizer.lang = (currentLang === 'Kannada') ? 'kn-IN' : 'en-US';
    }

    function safeStart() {
        if (!recognizer || isRunning || isStarting) return;
        if (window._isBotActivelySpeaking || state === STATE_IDLE) return;
        if (Date.now() - (window._botSpeechEndTime || 0) < 300) {
            setTimeout(safeStart, 150);
            return;
        }

        updateRecognizerLanguage();
        try {
            isStarting = true;
            recognizer.start();
        } catch (e) {
            isStarting = false;
            console.debug("[SiriSpeechEngine] safeStart notice:", e.message);
        }
    }

    function safeStop() {
        if (!recognizer) return;
        try {
            recognizer.abort(); // Immediately discard any pending audio from mic buffer!
        } catch (e) {
            try { recognizer.stop(); } catch (err) {}
        }
        isRunning = false;
        isStarting = false;
    }

    function enterCommandListeningMode() {
        state = STATE_COMMAND;
        updateMicUI();
        updateAiStatus('listening');

        const currentLang = localStorage.getItem('siri_bank_lang') || 'English';
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            chatInput.placeholder = (currentLang === 'Kannada') ? "🔴 ಕೇಳಿಸಿಕೊಳ್ಳುತ್ತಿದ್ದೇನೆ... ಮಾತನಾಡಿ" : "🔴 Listening... Speak now";
            chatInput.focus();
        }

        resetInactivityTimer();
    }

    function handleCommandTranscript(transcript) {
        if (!transcript || transcript.length < 1) return;
        if (speechEndDebounceTimer) clearTimeout(speechEndDebounceTimer);
        if (isSelfEcho(transcript)) {
            console.warn("[SiriSpeechEngine] handleCommandTranscript dropped self-echo:", transcript);
            return;
        }
        clearLiveSpeechPreview();
        if (commandTimeoutTimer) clearTimeout(commandTimeoutTimer);

        console.log("[SiriSpeechEngine] User question recognized. Automatically answering immediately:", transcript);
        
        // Intercept Voice Commands when Camera Modal is open
        const camModal = document.getElementById('cameraModal');
        if (camModal && camModal.style.display === 'flex') {
            const textLower = (transcript || '').toLowerCase();
            if (/^(click|capture|take|cheese|shoot|snap|photo|picture|ಕ್ಲಿಕ್|ಕ್ಲಿಕ್ ಮಾಡಿ|ಫೋಟೋ|ತೆಗೆ|ತೆಗೆಯಿರಿ|ರೆಡಿ|ready)$/i.test(textLower) || textLower.includes('click') || textLower.includes('capture') || textLower.includes('ಕ್ಲಿಕ್') || textLower.includes('cheese')) {
                const liveControls = document.getElementById('camLiveControls');
                if (liveControls && liveControls.style.display !== 'none' && typeof captureLivePhoto === 'function') {
                    captureLivePhoto();
                    return;
                }
            }
            if (/^(confirm|use|yes|done|ok|save|ಸರಿ|ಬಳಸಿ|ಮುಗಿಸಿ)$/i.test(textLower) || textLower.includes('use') || textLower.includes('confirm') || textLower.includes('ಸರಿ') || textLower.includes('ಬಳಸಿ')) {
                const prevControls = document.getElementById('camPreviewControls');
                if (prevControls && prevControls.style.display !== 'none' && typeof confirmLivePhoto === 'function') {
                    confirmLivePhoto();
                    return;
                }
            }
            if (/^(retake|again|ಮತ್ತೆ|ಮತ್ತೆ ತೆಗೆ|ಮತ್ತೆ ತೆಗೆಯಿರಿ)$/i.test(textLower) || textLower.includes('retake')) {
                if (typeof retakeLivePhoto === 'function') {
                    retakeLivePhoto();
                    return;
                }
            }
        }

        const chatInput = document.getElementById('chat-input');
        if (chatInput) chatInput.value = transcript;

        state = STATE_SPEAKING;
        window._isBotActivelySpeaking = true;
        safeStop();
        updateMicUI();
        sendMessage();
    }

    function onSpeechStart() {
        state = STATE_SPEAKING;
        window._isBotActivelySpeaking = true;
        if (speechEndDebounceTimer) clearTimeout(speechEndDebounceTimer);
        if (commandTimeoutTimer) clearTimeout(commandTimeoutTimer);
        safeStop();
        updateMicUI();
    }

    function onSpeechEnd() {
        console.log("[SiriSpeechEngine] Bot speech ended. Actively listening for your question now!");
        window._isBotActivelySpeaking = false;
        if (speechEndDebounceTimer) clearTimeout(speechEndDebounceTimer);
        enterCommandListeningMode();
        safeStart();
    }

    function cancelCommand() {
        if (speechEndDebounceTimer) clearTimeout(speechEndDebounceTimer);
        if (commandTimeoutTimer) clearTimeout(commandTimeoutTimer);
        clearLiveSpeechPreview();
        playChime('cancel');
        state = STATE_WAKE_WORD;
        updateMicUI();
        updateAiStatus('standby');
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            const currentLang = localStorage.getItem('siri_bank_lang') || 'English';
            chatInput.placeholder = (currentLang === 'Kannada') ? "ಮಾತನಾಡಿ ಅಥವಾ ಟೈಪ್ ಮಾಡಿ..." : "Type a message or speak...";
        }
    }

    function toggleManualMic() {
        getAudioContext();
        if (state === STATE_COMMAND) {
            cancelCommand();
        } else {
            playChime('wake');
            openChat();
            enterCommandListeningMode();
            safeStart();
        }
    }

    function updateMicUI() {
        const micBtn = document.getElementById('mic-btn');
        const badge = document.getElementById('ai-callout-badge');

        if (state === STATE_COMMAND) {
            if (micBtn) {
                micBtn.classList.remove('idle-pulse');
                micBtn.classList.add('mic-listening-active');
                micBtn.style.background = '#fee2e2';
                micBtn.style.color = '#ef4444';
            }
            if (badge) {
                badge.style.borderColor = '#ef4444';
                badge.style.boxShadow = '0 0 18px rgba(239, 68, 68, 0.6)';
            }
        } else {
            if (micBtn) {
                micBtn.classList.remove('mic-listening-active');
                micBtn.classList.add('idle-pulse');
                micBtn.style.background = '#eef2ff';
                micBtn.style.color = '#4f46e5';
            }
            if (badge) {
                badge.style.borderColor = '';
                badge.style.boxShadow = '';
            }
        }
    }

    function setLanguage(lang) {
        if (!recognizer) return;
        const currentLang = lang || localStorage.getItem('siri_bank_lang') || 'English';
        const newLangCode = (currentLang === 'Kannada') ? 'kn-IN' : 'en-US';
        if (recognizer.lang !== newLangCode) {
            recognizer.lang = newLangCode;
            if (isRunning) {
                safeStop();
                setTimeout(() => {
                    if (state === STATE_WAKE_WORD || state === STATE_COMMAND) {
                        safeStart();
                    }
                }, 250);
            }
        }
    }

    return {
        init: init,
        toggle: toggleManualMic,
        startCommand: enterCommandListeningMode,
        cancelCommand: cancelCommand,
        resetTimer: resetInactivityTimer,
        onSpeechStart: onSpeechStart,
        onSpeechEnd: onSpeechEnd,
        setLanguage: setLanguage,
        getState: () => state,
        getStatus: () => {
            if (state === STATE_COMMAND) return 'listening';
            if (state === STATE_SPEAKING) return 'speaking';
            return 'standby';
        }
    };
})();

function toggleVoice() {
    if (typeof SiriSpeechEngine !== 'undefined') {
        SiriSpeechEngine.toggle();
    }
}

function restoreChatState() {
    const savedHistory = sessionStorage.getItem('siri_chat_history');
    const chatMessages = document.getElementById('chat-messages');
    if (savedHistory && chatMessages) {
        chatMessages.innerHTML = savedHistory;
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    const wasOpen = sessionStorage.getItem('siri_chat_open');
    if (wasOpen === 'true') {
        const chatContainer = document.getElementById('chat-container');
        const toggleBtnIcon = document.querySelector('#chat-toggle-btn i');
        if (chatContainer) {
            chatContainer.classList.add('open');
            chatContainer.style.display = 'flex';
            if (toggleBtnIcon) {
                toggleBtnIcon.classList.remove('fa-robot', 'fa-comment-dots');
                toggleBtnIcon.classList.add('fa-times');
            }
        }
    }
}

function openChat() {
    const chatContainer = document.getElementById('chat-container');
    if (!chatContainer) return;
    chatContainer.classList.add('open');
    chatContainer.style.display = 'flex';
    sessionStorage.setItem('siri_chat_open', 'true');
    const toggleBtnIcon = document.querySelector('#chat-toggle-btn i');
    if (toggleBtnIcon) {
        toggleBtnIcon.classList.remove('fa-robot', 'fa-comment-dots');
        toggleBtnIcon.classList.add('fa-times');
    }
    const input = document.getElementById('chat-input');
    if (input) input.focus();
}

function closeChat() {
    const chatContainer = document.getElementById('chat-container');
    if (!chatContainer) return;
    chatContainer.classList.remove('open');
    chatContainer.style.display = 'none';
    sessionStorage.setItem('siri_chat_open', 'false');
    const toggleBtnIcon = document.querySelector('#chat-toggle-btn i');
    if (toggleBtnIcon) {
        toggleBtnIcon.classList.remove('fa-times');
        toggleBtnIcon.classList.add('fa-robot');
    }
}

function toggleChat() {
    const chatContainer = document.getElementById('chat-container');
    if (!chatContainer) return;
    if (chatContainer.classList.contains('open') && chatContainer.style.display !== 'none') {
        closeChat();
    } else {
        openChat();
    }
}

async function clearFullChat(skipConfirm = false) {
    const isKn = (localStorage.getItem('siri_bank_lang') || 'English') === 'Kannada';
    if (!skipConfirm) {
        const confirmMsg = isKn 
            ? "ಸಂಪೂರ್ಣ ಚಾಟ್ ಇತಿಹಾಸವನ್ನು ಅಳಿಸಲು ನೀವು ಖಚಿತವಾಗಿ ಬಯಸುವಿರಾ?" 
            : "Are you sure you want to delete the full chat history?";
        if (!confirm(confirmMsg)) return;
    }

    // 1. Terminate any active bot voice playback immediately
    if (window.currentVoiceAudio) {
        try {
            window.currentVoiceAudio.pause();
            window.currentVoiceAudio = null;
        } catch(e) {}
    }
    if (window.speechSynthesis) {
        try { window.speechSynthesis.cancel(); } catch(e) {}
    }
    window._isBotActivelySpeaking = false;
    if (typeof updateAiStatus === 'function') updateAiStatus('idle');

    // 2. Clear client-side sessionStorage
    sessionStorage.removeItem('siri_chat_history');
    sessionStorage.removeItem('siri_chat_history_turns');
    sessionStorage.removeItem('siri_reg_flow');
    sessionStorage.removeItem('siri_pending_submit_form');
    sessionStorage.removeItem('pending_voice_fill');
    sessionStorage.removeItem('pending_voice_reply');
    sessionStorage.removeItem('pending_sidebar_tool');

    // 3. Clear server-side session
    try {
        await fetch('/api/chat/clear', { method: 'POST' });
    } catch(e) {
        console.error("Failed to clear server chat history:", e);
    }

    // 4. Reset Chat DOM to initial welcoming greeting
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        chatMessages.innerHTML = `
            <div class="message bot initial-bot-greeting" style="background: white; padding: 12px 14px; border-radius: 14px; box-shadow: 0 2px 6px rgba(0,0,0,0.04); font-size: 0.88rem; line-height: 1.45; border-left: 3px solid #4f46e5;">
                ${isKn 
                    ? "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ SIRI BANK AI ಸಹಾಯಕ. ನೀವು ಕನ್ನಡ ಅಥವಾ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಮಾತನಾಡಬಹುದು!" 
                    : "Hello! I am your SIRI BANK AI Assistant. You can speak with me in English or Kannada!"}
            </div>
        `;
        chatMessages.scrollTop = 0;
    }

    // 5. Explicitly overwrite stored chat state with the reset greeting
    if (typeof saveChatState === 'function') {
        saveChatState();
    } else {
        sessionStorage.removeItem('siri_chat_history');
    }

    // 6. Clear input
    const chatInput = document.getElementById('chat-input');
    if (chatInput) chatInput.value = '';

    showToast(isKn ? "ಸಂಪೂರ್ಣ ಚಾಟ್ ಅಳಿಸಲಾಗಿದೆ" : "Full chat deleted successfully");
}
window.clearFullChat = clearFullChat;

function startVoice() {
    if (typeof SiriSpeechEngine !== 'undefined') {
        SiriSpeechEngine.startCommand();
    }
}

function stopVoice() {
    if (typeof SiriSpeechEngine !== 'undefined') {
        SiriSpeechEngine.cancelCommand();
    }
}

/** DATE FORMATTER FOR HTML5 DATE INPUTS **/
function formatDobForInput(val) {
    if (!val) return '';
    const str = String(val).trim();

    // 1. Already strict YYYY-MM-DD
    const isoMatch = str.match(/\b(19\d\d|20[0-2]\d)-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b/);
    if (isoMatch) return isoMatch[0];

    // Clean ordinals: 15th -> 15, 1st -> 1, 15ನೇ -> 15
    const cleaned = str.replace(/(\d+)(?:st|nd|rd|th|ನೇ)/gi, '$1');

    // 2. DD-MM-YYYY or DD/MM/YYYY
    const dmyMatch = cleaned.match(/\b(0?[1-9]|[12]\d|3[01])[\/\-\.\s](0?[1-9]|1[0-2])[\/\-\.\s](19\d\d|20[0-2]\d)\b/);
    if (dmyMatch) {
        const d = String(dmyMatch[1]).padStart(2, '0');
        const m = String(dmyMatch[2]).padStart(2, '0');
        const y = dmyMatch[3];
        return `${y}-${m}-${d}`;
    }

    // 3. YYYY/MM/DD
    const ymdMatch = cleaned.match(/\b(19\d\d|20[0-2]\d)[\/\-\.\s](0?[1-9]|1[0-2])[\/\-\.\s](0?[1-9]|[12]\d|3[01])\b/);
    if (ymdMatch) {
        const y = ymdMatch[1];
        const m = String(ymdMatch[2]).padStart(2, '0');
        const d = String(ymdMatch[3]).padStart(2, '0');
        return `${y}-${m}-${d}`;
    }

    // 4. English and Kannada month names
    const monthMap = {
        'january': '01', 'jan': '01', 'february': '02', 'feb': '02', 'march': '03', 'mar': '03',
        'april': '04', 'apr': '04', 'may': '05', 'june': '06', 'jun': '06', 'july': '07', 'jul': '07',
        'august': '08', 'aug': '08', 'september': '09', 'sep': '09', 'sept': '09', 'october': '10', 'oct': '10',
        'november': '11', 'nov': '11', 'december': '12', 'dec': '12',
        'ಜನವರಿ': '01', 'ಜನವಾರಿ': '01', 'ಫೆಬ್ರವರಿ': '02', 'ಫೆಬ್ರುವರಿ': '02', 'ಮಾರ್ಚ್': '03', 'ಏಪ್ರಿಲ್': '04',
        'ಮೇ': '05', 'ಜೂನ್': '06', 'ಜುಲೈ': '07', 'ಆಗಸ್ಟ್': '08', 'ಅಗಸ್ಟ್': '08', 'ಸೆಪ್ಟೆಂಬರ್': '09',
        'ಸೆಪ್ಟಂಬರ್': '09', 'ಅಕ್ಟೋಬರ್': '10', 'ಅಕ್ಟೋಬರ': '10', 'ನವೆಂಬರ್': '11', 'ನವೆಂಬರ': '11', 'ಡಿಸೆಂಬರ್': '12', 'ಡಿಸೆಂಬರ': '12'
    };

    const monthKeys = Object.keys(monthMap).join('|');
    const dmyWordRegex = new RegExp('\\b(0?[1-9]|[12]\\d|3[01])\\s*(?:of)?\\s*(' + monthKeys + ')\\s*,?\\s*(19\\d\\d|20[0-2]\\d)\\b', 'i');
    const dmyWordMatch = cleaned.match(dmyWordRegex);
    if (dmyWordMatch) {
        const d = String(dmyWordMatch[1]).padStart(2, '0');
        const m = monthMap[dmyWordMatch[2].toLowerCase()];
        const y = dmyWordMatch[3];
        if (m) return `${y}-${m}-${d}`;
    }

    const mdyWordRegex = new RegExp('\\b(' + monthKeys + ')\\s*(0?[1-9]|[12]\\d|3[01])\\s*,?\\s*(19\\d\\d|20[0-2]\\d)\\b', 'i');
    const mdyWordMatch = cleaned.match(mdyWordRegex);
    if (mdyWordMatch) {
        const m = monthMap[mdyWordMatch[1].toLowerCase()];
        const d = String(mdyWordMatch[2]).padStart(2, '0');
        const y = mdyWordMatch[3];
        if (m) return `${y}-${m}-${d}`;
    }

    // Try standard Date parsing as fallback
    const parsed = new Date(val);
    if (!isNaN(parsed.getTime())) {
        const y = parsed.getFullYear();
        const m = String(parsed.getMonth() + 1).padStart(2, '0');
        const d = String(parsed.getDate()).padStart(2, '0');
        if (y >= 1900 && y <= 2030) return `${y}-${m}-${d}`;
    }

    return '';
}

/** VOICE ASSISTANT ACTIONS & ACCESSIBILITY LOGIC **/
function handleVoiceActions(data) {
    if (!data) return;

    // 0. AUTH TAB SWITCHING (e.g. "click on register", "click on login", filling registration details)
    if (data.action === 'SWITCH_AUTH_MODE' || data.mode || data.action === 'FILL_REGISTER' || data.target_form === 'register' || (data.fields && data.fields.name && !document.getElementById('kyc-full-name'))) {
        const mode = data.mode || (data.target_form === 'register' || data.action === 'FILL_REGISTER' || (data.fields && data.fields.name) || (data.intent && data.intent.includes('REGISTER')) ? 'register' : 'login');
        
        // Ensure authModal is displayed if present on the page!
        const authModal = document.getElementById('authModal');
        if (authModal) {
            authModal.style.display = 'flex';
        }

        if (typeof openAuthModal === 'function') {
            openAuthModal(mode);
        } else if (typeof switchAuthMode === 'function') {
            switchAuthMode(mode);
        }

        if (mode === 'register') {
            const btn = document.getElementById('tab-btn-register');
            if (btn) btn.click();
            sessionStorage.setItem('siri_pending_submit_form', 'register');
            if (data.action === 'SWITCH_AUTH_MODE') showToast("Switched to Registration form.");
        } else {
            const btn = document.getElementById('tab-btn-login');
            if (btn) btn.click();
            sessionStorage.setItem('siri_pending_submit_form', 'login');
            if (data.action === 'SWITCH_AUTH_MODE') showToast("Switched to Login form.");
        }
    }

    // 0.2 LIVE CAMERA TRIGGER (Selfie / ID scan)
    if (data.action === 'OPEN_CAMERA' || data.intent === 'OPEN_CAMERA') {
        const camTarget = data.camera_target || data.target || 'photo';
        if (typeof openLiveCamera === 'function') {
            openLiveCamera(camTarget);
        }
    }

    // Upfront target form pending submission tracking
    if (data.target_form) {
        sessionStorage.setItem('siri_pending_submit_form', data.target_form);
    } else if (data.action === 'FILL_REGISTER') {
        sessionStorage.setItem('siri_pending_submit_form', 'register');
    }

    // 0.5 KYC ACTIONS: RESET, GENERATE OTP, VERIFY OTP, AUTO SIMULATE
    if (data.action === 'RESET_KYC' || data.intent === 'KYC_RETRY' || data.intent === 'KYC_REJECTED_EXPLAIN') {
        const step1 = document.getElementById('kyc-step-1');
        if (window.location.pathname !== '/aadhaar-kyc' || !step1) {
            if (data.fields && Object.keys(data.fields).length > 0) {
                sessionStorage.setItem('pending_voice_fill', JSON.stringify(data.fields));
            }
            showToast("Navigating to Aadhaar KYC...");
            if (typeof navigateSpa === 'function') {
                navigateSpa('/aadhaar-kyc?retry=true', true);
            } else {
                window.location.href = '/aadhaar-kyc?retry=true';
            }
            return;
        } else {
            resetKycWizard();
            if (data.fields && data.fields.name) {
                const nameEl = document.getElementById('kyc-full-name');
                if (nameEl) {
                    nameEl.value = data.fields.name;
                    highlightVoiceField(nameEl);
                }
            }
            return;
        }
    }

    if (data.action === 'GENERATE_KYC_OTP' || data.intent === 'KYC_GENERATE_OTP') {
        if (window.location.pathname !== '/aadhaar-kyc') {
            if (typeof navigateSpa === 'function') navigateSpa('/aadhaar-kyc', true);
            else window.location.href = '/aadhaar-kyc';
            return;
        }
        showToast("Generating simulated Aadhaar OTP...");
        fetch('/api/user/kyc/generate-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(res => res.json())
        .then(otpData => {
            if (otpData.success && otpData.otp) {
                if (typeof nextKYCStep === 'function') nextKYCStep(1);
                const otpInput = document.getElementById('kyc-otp-input');
                if (otpInput) {
                    otpInput.value = otpData.otp;
                    highlightVoiceField(otpInput);
                }
                showToast(`Mock OTP Generated: ${otpData.otp}`);
            } else {
                showToast(otpData.message || "Failed to generate OTP");
            }
        })
        .catch(err => {
            console.error("OTP generate error:", err);
            showToast("Error generating OTP");
        });
        return;
    }

    if (data.action === 'VERIFY_KYC_OTP' || data.intent === 'KYC_VERIFY_OTP') {
        if (window.location.pathname !== '/aadhaar-kyc') {
            if (typeof navigateSpa === 'function') navigateSpa('/aadhaar-kyc', true);
            else window.location.href = '/aadhaar-kyc';
            return;
        }
        const otpInput = document.getElementById('kyc-otp-input');
        const otpToVerify = (otpInput?.value?.trim()) || (data.fields?.otp) || '123456';
        showToast(`Verifying OTP ${otpToVerify}...`);
        fetch('/api/user/kyc/verify-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ otp: otpToVerify })
        })
        .then(res => res.json())
        .then(vData => {
            if (vData.success) {
                showToast("OTP Verified! Starting Face Liveness Scan...");
                if (typeof nextKYCStep === 'function') {
                    nextKYCStep(2); // Advances to step 3 and triggers startWebcamScan
                }
            } else {
                showToast(vData.message || "Invalid OTP");
            }
        })
        .catch(err => {
            console.error("OTP verification error:", err);
            showToast("Error verifying OTP");
        });
        return;
    }

    if (data.action === 'SIMULATE_KYC_AUTO' || data.intent === 'KYC_SIMULATE_ALL') {
        if (window.location.pathname !== '/aadhaar-kyc') {
            sessionStorage.setItem('pending_simulate_kyc_auto', JSON.stringify(data.fields || {}));
            showToast("Navigating to Aadhaar KYC for simulation...");
            if (typeof navigateSpa === 'function') {
                navigateSpa('/aadhaar-kyc', true);
            } else {
                window.location.href = '/aadhaar-kyc';
            }
            return;
        } else {
            executeFullSimulatedKyc(data.fields || {});
            return;
        }
    }

    // CLEAR CHAT ACTION
    if (data.action === 'CLEAR_CHAT' || data.intent === 'CLEAR_CHAT') {
        setTimeout(() => {
            clearFullChat(true);
        }, 800);
        return;
    }

    // 1. AUTO FORM FILLING ON CURRENT PAGE
    if (data.fields && Object.keys(data.fields).length > 0) {
        applyVoiceFields(data.fields);
    }

    // 2. LOGOUT ACTION (Waits until bot finishes speaking completely!)
    if (data.action === 'LOGOUT' || data.intent === 'LOGOUT') {
        showToast("Logging out of SIRI BANK...");
        let logoutExecuted = false;
        const doLogout = () => {
            if (logoutExecuted) return;
            logoutExecuted = true;
            setTimeout(() => {
                if (typeof logout === 'function') logout();
            }, 600); // 600ms natural pause after speech finishes
        };

        // If bot is speaking, wait for speech completion callback
        if (window._isBotActivelySpeaking || window.currentVoiceAudio) {
            window._onBotSpeechEndOnce = doLogout;
            // Safety timeout based on sentence length in case speech events are skipped
            const replyLen = (data.reply || "").length;
            const safeTimeout = Math.max(6500, replyLen * 95);
            setTimeout(doLogout, safeTimeout);
        } else {
            setTimeout(doLogout, 2500);
        }
        return;
    }

    // 3. SUB-ACTION TOOLS (e.g. 'click on bank transfer', 'pay phone', 'upi')
    const toolName = data.tool || (data.intent === 'SUB_ACTION_BANK_TRANSFER' ? 'bank-transfer' : data.intent === 'SUB_ACTION_PHONE_PAY' ? 'pay-phone' : data.intent === 'SUB_ACTION_UPI_PAY' ? 'upi-pay' : null);
    if (toolName) {
        if (typeof showSidebarAction === 'function') {
            showSidebarAction(toolName);
        }
        sessionStorage.setItem('pending_sidebar_tool', toolName);
    }

    // 3.5 CARD ACTIONS: DEBIT & CREDIT CARD REQUESTS & TAB SWITCHING
    if (data.action === 'CREATE_REQUEST_ATM' || data.intent === 'ATM_CARD_REQUEST') {
        showToast("Submitting Debit Card request...");
        fetch('/api/user/kyc/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                request_type: 'ATM_CARD',
                details: 'Requested Visa Debit Card via AI Voice Assistant'
            })
        })
        .then(r => r.json())
        .then(res => {
            if (res.success) {
                showToast("Visa Debit Card application submitted successfully!");
                if (typeof loadUserSummary === 'function') loadUserSummary();
            }
        });
        if (typeof updateSegment === 'function') updateSegment(0);
    }

    if (data.action === 'CREATE_REQUEST_CREDIT' || data.intent === 'CREDIT_CARD_REQUEST') {
        showToast("Submitting Credit Card request...");
        fetch('/api/user/kyc/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                request_type: 'CREDIT_CARD',
                details: 'Requested SIRI Platinum Credit Card via AI Voice Assistant'
            })
        })
        .then(r => r.json())
        .then(res => {
            if (res.success) {
                showToast("Credit Card application submitted for review!");
                if (typeof loadUserSummary === 'function') loadUserSummary();
            }
        });
        if (typeof updateSegment === 'function') updateSegment(1);
    }

    if (data.action === 'SWITCH_CARD_TAB' || data.intent === 'SHOW_DEBIT_CARD' || data.intent === 'SHOW_CREDIT_CARD') {
        if (typeof updateSegment === 'function') {
            if (data.card_type === 'credit' || data.intent === 'SHOW_CREDIT_CARD') {
                updateSegment(1);
            } else {
                updateSegment(0);
            }
        }
    }

    // 4. READ SCREEN ACTION
    if (data.action === 'READ_SCREEN') {
        readCurrentScreenAloud();
        return;
    }

    // 5. VOICE NAVIGATION & CROSS-SECTION FORM FILL PERSISTENCE
    if (data.redirect) {
        if (data.redirect.includes('retry=true') && window.location.pathname === '/aadhaar-kyc') {
            showToast("Resetting KYC wizard for retry...");
            window.location.href = data.redirect;
            return;
        }
        // Direct switch if target is register/login and user is already on auth page
        const curPath = window.location.pathname;
        if ((data.redirect === '/register' || data.redirect === '/signup') && (curPath === '/' || curPath === '/login' || curPath === '/register')) {
            const authModal = document.getElementById('authModal');
            if (authModal) authModal.style.display = 'flex';
            if (typeof openAuthModal === 'function') {
                openAuthModal('register');
            } else if (typeof switchAuthMode === 'function') {
                switchAuthMode('register');
            }
            const btn = document.getElementById('tab-btn-register');
            if (btn) btn.click();
            sessionStorage.setItem('siri_pending_submit_form', 'register');
            showToast("Switched to Registration form.");
            return;
        }
        if (data.redirect === '/login' && (curPath === '/' || curPath === '/login' || curPath === '/register')) {
            const authModal = document.getElementById('authModal');
            if (authModal) authModal.style.display = 'flex';
            if (typeof openAuthModal === 'function') {
                openAuthModal('login');
            } else if (typeof switchAuthMode === 'function') {
                switchAuthMode('login');
            }
            const btn = document.getElementById('tab-btn-login');
            if (btn) btn.click();
            sessionStorage.setItem('siri_pending_submit_form', 'login');
            showToast("Switched to Login form.");
            return;
        }

        if (curPath !== data.redirect) {
            if (data.fields && Object.keys(data.fields).length > 0) {
                sessionStorage.setItem('pending_voice_fill', JSON.stringify(data.fields));
            }
            if (data.reply) {
                sessionStorage.setItem('pending_voice_reply', data.reply);
            }
            if ((data.action === 'SUBMIT_FORM' || data.action === 'SUBMIT_REGISTER') && data.target_form) {
                sessionStorage.setItem('siri_pending_submit_form', data.target_form);
            }
            showToast(`Navigating to ${data.redirect}...`);
            setTimeout(() => {
                if (typeof navigateSpa === 'function') {
                    navigateSpa(data.redirect, true);
                } else {
                    window.location.href = data.redirect;
                }
            }, 1000);
            return;
        }
    }

    // 6. AUTOMATIC FORM SUBMISSION TRIGGER UPON USER CONFIRMATION
    if (data.action === 'SUBMIT_FORM' || data.action === 'SUBMIT_REGISTER' || data.intent === 'CONFIRM_SUBMIT') {
        executeFormSubmission(data.target_form);
    } else if (data.action === 'CANCEL_SUBMIT' || data.intent === 'CANCEL_SUBMIT') {
        sessionStorage.removeItem('siri_pending_submit_form');
        showToast("Submission cancelled.");
    }
}

function executeFormSubmission(targetForm) {
    const pendingForm = targetForm || sessionStorage.getItem('siri_pending_submit_form');
    const path = window.location.pathname;

    // A. KYC SIMULATION EXPLICIT SUBMISSION
    if (pendingForm === 'kyc_simulate') {
        executeFullSimulatedKyc();
        sessionStorage.removeItem('siri_pending_submit_form');
        return true;
    }

    // B1. LOGIN FORM SUBMISSION
    if (pendingForm === 'login' || ((path === '/login' || path === '/') && pendingForm !== 'register')) {
        const regForm = document.getElementById('register-form');
        const loginForm = document.getElementById('login-form');
        const isRegVisible = regForm && regForm.style.display !== 'none';
        if (!isRegVisible && loginForm) {
            showToast("Logging in to your account...");
            const loginBtn = document.getElementById('login-btn');
            if (loginBtn) {
                loginBtn.click();
            } else {
                loginForm.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
            }
            sessionStorage.removeItem('siri_pending_submit_form');
            return true;
        }
    }

    // B2. REGISTRATION SUBMISSION (Login / Registration Page)
    if (pendingForm === 'register' || ((path === '/login' || path === '/' || path === '/register' || path === '/signup') && pendingForm === 'register')) {
        const regForm = document.getElementById('register-form');
        if (regForm) {
            showToast("Submitting your registration for approval...");
            const regBtn = document.getElementById('register-btn');
            if (regBtn) {
                regBtn.click();
            } else {
                regForm.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
            }
            sessionStorage.removeItem('siri_pending_submit_form');
            return true;
        }
    }

    // C. PHONE TRANSFER SUBMISSION
    if (pendingForm === 'pay-phone') {
        const btn = document.getElementById('side-confirm-pay');
        if (btn) {
            showToast("Executing phone transfer...");
            btn.click();
            sessionStorage.removeItem('siri_pending_submit_form');
            return true;
        } else if (typeof executeSidebarPhoneTransfer === 'function') {
            showToast("Executing phone transfer...");
            executeSidebarPhoneTransfer();
            sessionStorage.removeItem('siri_pending_submit_form');
            return true;
        }
    }

    // D. BANK ACCOUNT TRANSFER SUBMISSION
    if (pendingForm === 'pay-acc') {
        const btn = document.getElementById('side-confirm-bank');
        if (btn) {
            showToast("Executing bank transfer...");
            btn.click();
            sessionStorage.removeItem('siri_pending_submit_form');
            return true;
        } else if (typeof executeSidebarBankTransfer === 'function') {
            showToast("Executing bank transfer...");
            executeSidebarBankTransfer();
            sessionStorage.removeItem('siri_pending_submit_form');
            return true;
        }
    }

    // E. ATM CARD REQUEST SUBMISSION
    if (pendingForm === 'atm-card') {
        showToast("Submitting ATM card request...");
        fetch('/api/user/requests/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                request_type: 'ATM_CARD',
                details: 'Requested Visa Debit Card via AI Confirmation'
            })
        })
        .then(r => r.json())
        .then(res => {
            if (res.success) {
                showToast("ATM Card request submitted successfully!");
            }
        });
        sessionStorage.removeItem('siri_pending_submit_form');
        return true;
    }

    return false;
}

function formatDigitsForSpeech(digits) {
    if (!digits) return '';
    return String(digits).split('').join(', ');
}

function resetKycWizard() {
    // Hide any rejection or pending status cards
    document.querySelectorAll('.main-content .glass-card').forEach(c => {
        if (!c.classList.contains('kyc-card')) c.style.display = 'none';
    });

    // Show progress bar
    const progress = document.querySelector('.kyc-progress');
    if (progress) progress.style.display = 'flex';
    const progressLineActive = document.getElementById('progress-line-active');
    if (progressLineActive) progressLineActive.style.width = '0%';

    for (let i = 1; i <= 4; i++) {
        const dot = document.getElementById(`step-dot-${i}`);
        if (dot) {
            if (i === 1) {
                dot.classList.add('active');
                dot.style.color = 'var(--primary-color)';
                dot.style.borderColor = 'var(--primary-color)';
            } else {
                dot.classList.remove('active');
                dot.style.color = '#94a3b8';
                dot.style.borderColor = '#cbd5e1';
            }
        }
    }

    // Step cards
    const step1 = document.getElementById('kyc-step-1');
    if (step1) step1.style.display = 'block';
    const step2 = document.getElementById('kyc-step-2');
    if (step2) step2.style.display = 'none';
    const step3 = document.getElementById('kyc-step-3');
    if (step3) step3.style.display = 'none';
    const step4 = document.getElementById('kyc-step-4');
    if (step4) step4.style.display = 'none';

    // Clear inputs
    const dobEl = document.getElementById('kyc-dob');
    if (dobEl) dobEl.value = '';
    const aadhaarEl = document.getElementById('kyc-aadhaar-num');
    if (aadhaarEl) aadhaarEl.value = '';
    const otpEl = document.getElementById('kyc-otp-input');
    if (otpEl) otpEl.value = '';
    const consent = document.querySelector('#kyc-step-1 input[type="checkbox"]');
    if (consent) consent.checked = false;

    showToast("KYC Wizard reset for retry.");
}
window.resetKycWizard = resetKycWizard;

function executeFullSimulatedKyc(fields) {
    fields = fields || {};
    if (window.location.pathname !== '/aadhaar-kyc') {
        sessionStorage.setItem('pending_simulate_kyc_auto', JSON.stringify(fields));
        showToast("Navigating to Aadhaar KYC...");
        setTimeout(() => {
            if (typeof navigateSpa === 'function') {
                navigateSpa('/aadhaar-kyc', true);
            } else {
                window.location.href = '/aadhaar-kyc';
            }
        }, 800);
        return;
    }

    // 1. Fill Step 1 Fields if available
    if (fields && Object.keys(fields).length > 0) {
        applyVoiceFields(fields);
    }

    const nameInput = document.getElementById('kyc-full-name');
    const dobInput = document.getElementById('kyc-dob');
    const aadhaarInput = document.getElementById('kyc-aadhaar-num');
    const consentCheckbox = document.querySelector('#kyc-step-1 input[type="checkbox"]');

    if (consentCheckbox) consentCheckbox.checked = true;

    // Provide robust defaults if fields were missing
    if (nameInput && !nameInput.value.trim()) {
        const profileNameEl = document.querySelector('.user-greeting h3') || document.querySelector('.user-name');
        nameInput.value = (profileNameEl ? profileNameEl.innerText.replace(/hello|welcome|hi|ಗೌರವ/gi, '').trim() : '') || 'Account Holder';
        highlightVoiceField(nameInput);
    }
    if (dobInput && !dobInput.value.trim()) {
        dobInput.value = '1995-05-15';
        highlightVoiceField(dobInput);
    }
    if (aadhaarInput && !aadhaarInput.value.trim()) {
        aadhaarInput.value = '1234 5678 9001';
        highlightVoiceField(aadhaarInput);
    }

    showToast("Step 1 Complete: Simulating Aadhaar OTP generation...");

    // Call backend to generate simulated OTP
    fetch('/api/user/kyc/generate-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(r => r.json())
    .then(data => {
        if (data.success && data.otp) {
            showToast("Step 2: Aadhaar OTP sent to linked mobile");
            
            // Advance to Step 2
            if (typeof nextKYCStep === 'function') {
                nextKYCStep(1);
            }

            const otpInput = document.getElementById('kyc-otp-input');
            if (otpInput) {
                otpInput.value = data.otp;
                highlightVoiceField(otpInput);
            }

            // Automatically verify the OTP after 1.4s visual pause
            setTimeout(() => {
                showToast("Verifying Aadhaar OTP...");
                fetch('/api/user/kyc/verify-otp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ otp: data.otp })
                })
                .then(res => res.json())
                .then(vdata => {
                    if (vdata.success) {
                        showToast("Step 3: OTP Verified! Starting Face Liveness Check...");
                        if (typeof nextKYCStep === 'function') {
                            nextKYCStep(2); // Advances to Step 3, which triggers startFaceScan()
                        }
                    } else {
                        showToast(vdata.message || "Invalid OTP entered");
                    }
                })
                .catch(err => {
                    console.error("Error verifying OTP:", err);
                    showToast("Error verifying simulated OTP");
                });
            }, 1400);
        } else {
            showToast(data.message || "Failed to generate simulated OTP");
        }
    })
    .catch(err => {
        console.error("Error generating KYC OTP:", err);
        showToast("Network error generating OTP");
    });
}

function simulateAndVerifyKYCOtp() {
    executeFullSimulatedKyc();
}


function applyVoiceFields(fields) {
    if (!fields) return 0;
    let filledCount = 0;

    // Ensure auth modal is visible if filling login or registration fields
    if (fields.identifier || fields.name || fields.phone || fields.aadhaar || fields.password) {
        const authModal = document.getElementById('authModal');
        if (authModal && authModal.style.display === 'none') {
            authModal.style.display = 'flex';
        }
    }

    // Login Form: Identifier (Phone / Aadhaar / Customer ID)
    if (fields.identifier) {
        const el = document.getElementById('identifier');
        if (el) {
            el.value = fields.identifier;
            highlightVoiceField(el);
            filledCount++;
            if (typeof switchAuthMode === 'function') switchAuthMode('login');
        }
    }

    // Password for Login or Registration
    if (fields.password !== undefined) {
        const regForm = document.getElementById('register-form');
        const isRegVisible = regForm && regForm.style.display !== 'none';
        const el = isRegVisible ? document.getElementById('reg_password') : (document.getElementById('password') || document.getElementById('reg_password'));
        if (el) { el.value = fields.password; if (fields.password) highlightVoiceField(el); filledCount++; }
    }

    // Self-Registration Form / Login Form Phone & Aadhaar & Email
    if (fields.name !== undefined && !document.getElementById('kyc-full-name')) {
        const el = document.getElementById('reg_name');
        if (el) { el.value = fields.name; if (fields.name) highlightVoiceField(el); filledCount++; }
    }
    if (fields.email !== undefined) {
        const el = document.getElementById('reg_email');
        if (el) { el.value = fields.email; if (fields.email) highlightVoiceField(el); filledCount++; }
    }
    if (fields.phone !== undefined && !fields.identifier) {
        const regForm = document.getElementById('register-form');
        const isRegVisible = regForm && regForm.style.display !== 'none';
        const pendingForm = sessionStorage.getItem('siri_pending_submit_form');
        if (isRegVisible || pendingForm === 'register') {
            const el = document.getElementById('reg_phone');
            if (el) { el.value = fields.phone; if (fields.phone) highlightVoiceField(el); filledCount++; }
        } else {
            const el = document.getElementById('identifier');
            if (el) { el.value = fields.phone; if (fields.phone) highlightVoiceField(el); filledCount++; }
        }
    }
    if (fields.aadhaar !== undefined && !fields.identifier && !document.getElementById('kyc-aadhaar-num')) {
        const regForm = document.getElementById('register-form');
        const isRegVisible = regForm && regForm.style.display !== 'none';
        const pendingForm = sessionStorage.getItem('siri_pending_submit_form');
        if (isRegVisible || pendingForm === 'register') {
            const el = document.getElementById('reg_aadhaar');
            if (el) { el.value = fields.aadhaar; if (fields.aadhaar) highlightVoiceField(el); filledCount++; }
        } else {
            const el = document.getElementById('identifier');
            if (el) { el.value = fields.aadhaar; if (fields.aadhaar) highlightVoiceField(el); filledCount++; }
        }
    }

    // Only switch to registration if explicitly targeting registration
    if ((fields.name || fields.phone || fields.aadhaar) && !fields.identifier) {
        const pendingForm = sessionStorage.getItem('siri_pending_submit_form');
        const path = window.location.pathname;
        if (pendingForm === 'register' || path === '/register' || path === '/signup') {
            if (typeof switchAuthMode === 'function') switchAuthMode('register');
        }
    }

    // Payment Phone Number & Amount
    if (fields.phone) {
        const el = document.getElementById('side-pay-phone') || document.getElementById('pay-phone-number') || document.getElementById('transfer-phone-num');
        if (el) { 
            el.value = fields.phone; 
            highlightVoiceField(el); 
            filledCount++; 
            if (typeof lookupPayeeName === 'function') lookupPayeeName(fields.phone);
        }
        if (fields.amount) {
            const amtEl = document.getElementById('side-pay-amt') || document.getElementById('pay-amount') || document.getElementById('transfer-amount');
            if (amtEl) { amtEl.value = fields.amount; highlightVoiceField(amtEl); filledCount++; }
        }
        if (typeof showSidebarAction === 'function') showSidebarAction('pay-phone');
    }

    // Bank Account Number & Amount
    if (fields.account) {
        const el = document.getElementById('side-bank-acc') || document.getElementById('pay-account') || document.getElementById('transfer-account-num');
        if (el) { el.value = fields.account; highlightVoiceField(el); filledCount++; }
        if (fields.amount) {
            const amtEl = document.getElementById('side-bank-amt') || document.getElementById('pay-amount') || document.getElementById('transfer-amount');
            if (amtEl) { amtEl.value = fields.amount; highlightVoiceField(amtEl); filledCount++; }
        }
        if (typeof showSidebarAction === 'function') showSidebarAction('bank-transfer');
    }

    // KYC Form Fields
    if (fields.name || fields.aadhaar || fields.dob) {
        if (fields.name) {
            const el = document.getElementById('kyc-full-name');
            if (el) { el.value = fields.name; highlightVoiceField(el); filledCount++; }
        }
        if (fields.dob) {
            const el = document.getElementById('kyc-dob');
            if (el) {
                const formatted = formatDobForInput(fields.dob);
                if (formatted) {
                    el.value = formatted;
                    highlightVoiceField(el);
                    filledCount++;
                }
            }
        }
        if (fields.aadhaar) {
            const el = document.getElementById('kyc-aadhaar-num');
            if (el) { el.value = fields.aadhaar; highlightVoiceField(el); filledCount++; }
        }
        // Auto-check required consent checkbox in step 1
        const consentCheckbox = document.querySelector('#kyc-step-1 input[type="checkbox"]');
        if (consentCheckbox) {
            consentCheckbox.checked = true;
        }
    }

    if (filledCount > 0) {
        showToast(`🎙️ Voice Assistant filled ${filledCount} field(s)!`);
    }
    return filledCount;
}

function checkPendingVoiceActions() {
    restoreChatState();

    const pendingFill = sessionStorage.getItem('pending_voice_fill');
    const pendingReply = sessionStorage.getItem('pending_voice_reply');

    if (pendingFill) {
        try {
            const fields = JSON.parse(pendingFill);
            setTimeout(() => {
                applyVoiceFields(fields);
                sessionStorage.removeItem('pending_voice_fill');
            }, 600);
        } catch (e) {
            console.error("Error parsing pending voice fill", e);
        }
    }

    if (pendingReply) {
        setTimeout(() => {
            speakText(pendingReply);
            sessionStorage.removeItem('pending_voice_reply');
        }, 800);
    }

    const pendingTool = sessionStorage.getItem('pending_sidebar_tool');
    if (pendingTool) {
        setTimeout(() => {
            if (typeof showSidebarAction === 'function') {
                showSidebarAction(pendingTool);
            }
            sessionStorage.removeItem('pending_sidebar_tool');
        }, 650);
    }

    const pendingSimAuto = sessionStorage.getItem('pending_simulate_kyc_auto');
    if (pendingSimAuto) {
        sessionStorage.removeItem('pending_simulate_kyc_auto');
        try {
            const fields = JSON.parse(pendingSimAuto);
            setTimeout(() => {
                executeFullSimulatedKyc(fields);
            }, 700);
        } catch (e) {
            setTimeout(() => {
                executeFullSimulatedKyc({});
            }, 700);
        }
    }



    // Check if retry requested on /aadhaar-kyc
    if (window.location.pathname === '/aadhaar-kyc' && window.location.search.includes('retry=true')) {
        const s1 = document.getElementById('kyc-step-1');
        const s2 = document.getElementById('kyc-step-2');
        const s3 = document.getElementById('kyc-step-3');
        const s4 = document.getElementById('kyc-step-4');
        if (s1) s1.style.display = 'block';
        if (s2) s2.style.display = 'none';
        if (s3) s3.style.display = 'none';
        if (s4) s4.style.display = 'none';
        const progLine = document.getElementById('progress-line-active');
        if (progLine) progLine.style.width = '0%';
        showToast("KYC Wizard ready for retry. Fill details or click Simulate.");
    }
}

function highlightVoiceField(element) {
    if (!element) return;
    element.focus();
    element.classList.add('voice-filled-highlight');
    setTimeout(() => element.classList.remove('voice-filled-highlight'), 3500);
}

function readCurrentScreenAloud() {
    let narrationText = "";
    const path = window.location.pathname;
    const currentLang = localStorage.getItem('siri_bank_lang') || 'Kannada';

    if (path === '/' || path === '/login') {
        narrationText = (currentLang === 'Kannada')
            ? "ಸಿರಿ ಬ್ಯಾಂಕ್ ಲಾಗಿನ್ ಪುಟಕ್ಕೆ ಸುಸ್ವಾಗತ. ನಿಮ್ಮ ಆಧಾರ್ ಸಂಖ್ಯೆ ಅಥವಾ ಗ್ರಾಹಕ ಐಡಿ ಮತ್ತು ಪಾಸ್ವರ್ಡ್ ನಮೂದಿಸಿ. ಅಥವಾ ಧ್ವನಿ ಮೂಲಕ ಲಾಗಿನ್ ಆಗಲು ಆಧಾರ್ ಸಂಖ್ಯೆ ಹೇಳಿ."
            : "Welcome to SIRI Bank Login page. Enter your Aadhaar Number or Customer ID and Password to sign in. You can also use voice login by saying: login with Aadhaar 123456789001.";
    } else if (path === '/home' || path === '/dashboard' || path === '/') {
        const balEl = document.getElementById('main-balance');
        const balance = balEl ? balEl.innerText : "ಲಭ್ಯವಿಲ್ಲ";
        narrationText = (currentLang === 'Kannada')
            ? `ಸಿರಿ ಬ್ಯಾಂಕ್ ಮುಖಪುಟಕ್ಕೆ ಸುಸ್ವಾಗತ. ನಿಮ್ಮ ಖಾತೆಯ ಬ್ಯಾಲೆನ್ಸ್ ${balance} ಆಗಿದೆ. ಲಭ್ಯವಿರುವ ಆಯ್ಕೆಗಳು: ಹಣ ವರ್ಗಾವಣೆ, ಎಟಿಎಂ ಸೇವೆಗಳು ಮತ್ತು ಆಧಾರ್ ಕೆವೈಸಿ.`
            : `You are on the Home Dashboard of SIRI Bank. Your account balance is ${balance}. Available quick options: Send Money, ATM Services, and Aadhaar KYC.`;
    } else if (path === '/pay') {
        narrationText = (currentLang === 'Kannada')
            ? "ಇದು ಪಾವತಿ ಮತ್ತು ಹಣ ವರ್ಗಾವಣೆ ಪುಟ. ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ಅಥವಾ ಖಾತೆ ಸಂಖ್ಯೆ ಮೂಲಕ ಹಣ ಕಳುಹಿಸಬಹುದು."
            : "You are on the Pay and Transfers page. Here you can transfer funds by mobile number or account number.";
    } else if (path === '/aadhaar-kyc') {
        narrationText = (currentLang === 'Kannada')
            ? "ಇದು ಆಧಾರ್ ಇ-ಕೆವೈಸಿ ಪುಟ. ಹಂತ 1 ವಿವರಗಳು, ಹಂತ 2 ಮೊಬೈಲ್ ಒಟಿಪಿ ಮತ್ತು ಹಂತ 3 ಫೇಸ್ ಲೈವ್‌ನೆಸ್ ಸ್ಕ್ಯಾನ್ ಪೂರ್ಣಗೊಳಿಸಿ."
            : "You are on the Aadhaar e-KYC page. Complete Step 1 details, Step 2 Mobile OTP, and Step 3 Face Liveness Scan.";
    } else if (path === '/atm-services') {
        narrationText = (currentLang === 'Kannada')
            ? "ಇದು ಎಟಿಎಂ ಸೇವೆಗಳ ಪುಟ. ಇಲ್ಲಿ ನಿಮ್ಮ ಡೆಬಿಟ್ ಅಥವಾ ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್ ನಿರ್ವಹಿಸಬಹುದು ಮತ್ತು ಹೊಸ ಕಾರ್ಡ್ ವಿನಂತಿಸಬಹುದು."
            : "You are on the ATM Services page. Here you can manage your Debit and Credit cards, request new cards, and set daily transaction limits.";
    } else if (path === '/request-history') {
        narrationText = (currentLang === 'Kannada')
            ? "ಇದು ವಿನಂತಿ ಮತ್ತು ವಹಿವಾಟು ಇತಿಹಾಸ ಪುಟ. ನಿಮ್ಮ ಹಿಂದಿನ ವಹಿವಾಟುಗಳನ್ನು ಪರಿಶೀಲಿಸಬಹುದು ಮತ್ತು ಸ್ಟೇಟ್‌ಮೆಂಟ್ ಡೌನ್‌ಲೋಡ್ ಮಾಡಬಹುದು."
            : "You are on the Request and Transaction History page. Here you can review past requests and download account statements.";
    } else {
        const title = document.title || "SIRI Bank Page";
        narrationText = (currentLang === 'Kannada')
            ? `ನೀವು ${title} ನೋಡುತ್ತಿದ್ದೀರಿ. ಧ್ವನಿ ಸಹಾಯಕ ಬಳಸಿ ನಿಮ್ಮ ಬ್ಯಾಂಕಿಂಗ್ ಕೆಲಸಗಳನ್ನು ಸುಲಭವಾಗಿ ಮಾಡಿ.`
            : `You are viewing ${title}. Use the voice assistant to speak commands or navigate across SIRI Bank.`;
    }

    openChat();
    updateAiStatus('speaking');
    speakText(narrationText);
    streamBotMessage(narrationText);
}

function triggerVoiceAssistant(promptMsg) {
    openChat();
    if (typeof SiriSpeechEngine !== 'undefined') {
        SiriSpeechEngine.startCommand();
    }
    if (promptMsg) {
        speakText(promptMsg);
    }
}

function syncVoiceLanguage(val, skipLandingSync) {
    if (!val || (val !== 'Kannada' && val !== 'English')) val = 'Kannada';
    localStorage.setItem('siri_bank_lang', val);
    
    // Sync with server session in background
    try {
        fetch('/api/user/set_language', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ language: val })
        }).catch(() => {});
    } catch(e) {}

    // If on landing page and changeLanguage is defined, synchronize landing page instantly
    if (!skipLandingSync && typeof window.changeLanguage === 'function') {
        try { window.changeLanguage(val, true); } catch(e) {}
    }

    // Sync all dropdowns and toggle buttons
    const headerLang = document.getElementById('chat-header-lang');
    if (headerLang && headerLang.value !== val) headerLang.value = val;

    const barLang = document.getElementById('voice-bar-lang');
    if (barLang && barLang.value !== val) barLang.value = val;
    
    const topLang = document.getElementById('language-selector');
    if (topLang && topLang.value !== val) topLang.value = val;

    const regLang = document.getElementById('reg_lang');
    if (regLang && regLang.value !== val) regLang.value = val;

    // Login page top toggle pills
    const btnKn = document.getElementById('btn-lang-kn');
    const btnEn = document.getElementById('btn-lang-en');
    if (btnKn && btnEn) {
        if (val === 'Kannada') {
            btnKn.style.background = '#4f46e5';
            btnKn.style.color = '#ffffff';
            btnEn.style.background = 'transparent';
            btnEn.style.color = '#64748b';
        } else {
            btnEn.style.background = '#4f46e5';
            btnEn.style.color = '#ffffff';
            btnKn.style.background = 'transparent';
            btnKn.style.color = '#64748b';
        }
    }

    const chatInput = document.getElementById('chat-input');
    if (chatInput && (typeof SiriSpeechEngine === 'undefined' || SiriSpeechEngine.getState() !== 'COMMAND')) {
        chatInput.placeholder = (val === 'Kannada') ? "ಮಾತನಾಡಿ ಅಥವಾ ಟೈಪ್ ಮಾಡಿ..." : "Type a message or use voice...";
    }

    // Apply comprehensive dynamic translations across the entire page
    applyPageTranslations(val);

    // If on history page, re-invoke loadHistory()
    if (typeof window.loadHistory === 'function') {
        try { window.loadHistory(); } catch(e) {}
    }

    // If on home dashboard, re-invoke loadUserSummary()
    if (document.getElementById('main-balance') && typeof loadUserSummary === 'function') {
        try { loadUserSummary(); } catch(e) {}
    }

    updateAiStatus(typeof SiriSpeechEngine !== 'undefined' ? SiriSpeechEngine.getStatus() : 'standby');

    if (typeof SiriSpeechEngine !== 'undefined') {
        SiriSpeechEngine.setLanguage(val);
    }
}

function applyPageTranslations(lang) {
    const isKn = (lang === 'Kannada');

    // ── 1. GLOBAL SIDEBAR NAVIGATION ──
    const navItems = [
        { href: '/home', kn: 'ಮುಖಪುಟ', en: 'Home' },
        { href: '/pay', kn: 'ಹಣ ವರ್ಗಾವಣೆ', en: 'Pay' },
        { href: '/atm-services', kn: 'ಎಟಿಎಂ ಸೇವೆಗಳು', en: 'ATM Services' },
        { href: '/aadhaar-kyc', kn: 'ಆಧಾರ್ ಕೆವೈಸಿ', en: 'Aadhaar/KYC' },
        { href: '/request-history', kn: 'ವಿನಂತಿ ಇತಿಹಾಸ', en: 'Request History' }
    ];
    navItems.forEach(item => {
        const el = document.querySelector(`.sidebar-nav a[href="${item.href}"] .menu-text`);
        if (el) el.innerText = isKn ? item.kn : item.en;
    });
    const logoutBtn = document.querySelector('.sidebar-nav .logout-btn .menu-text, .sidebar .logout-btn .menu-text');
    if (logoutBtn) logoutBtn.innerText = isKn ? 'ಲಾಗ್ ಔಟ್' : 'Logout';

    // ── 2. GLOBAL TOPBAR PAGE TITLE ──
    const topGreeting = document.querySelector('.topbar .user-greeting h3');
    if (topGreeting) {
        const p = window.location.pathname;
        let pageTitle = isKn ? "ಮುಖಪುಟ" : "Home";
        if (p.includes('/pay')) pageTitle = isKn ? "ಹಣ ವರ್ಗಾವಣೆ" : "Pay";
        else if (p.includes('/atm')) pageTitle = isKn ? "ಎಟಿಎಂ ಸೇವೆಗಳು" : "ATM Services";
        else if (p.includes('/kyc')) pageTitle = isKn ? "ಆಧಾರ್ ಕೆವೈಸಿ" : "Aadhaar/KYC";
        else if (p.includes('/history')) pageTitle = isKn ? "ವಿನಂತಿ ಇತಿಹಾಸ" : "Request History";
        else if (p.includes('/profile')) pageTitle = isKn ? "ಪ್ರೊಫೈಲ್" : "Profile";
        topGreeting.innerHTML = `SIRI BANK <span style="color:var(--primary-color); margin-left: 10px;">${pageTitle}</span>`;
    }

    // ── 3. LOGIN & REGISTRATION PAGE (login.html) ──
    const subtitle = document.getElementById('login-subtitle');
    if (subtitle) {
        subtitle.innerText = isKn ? "AI ಆಧಾರಿತ ಸ್ಮಾರ್ಟ್ ಮತ್ತು ಸಮಗ್ರ ಬ್ಯಾಂಕಿಂಗ್" : "AI Powered Smart & Inclusive Banking";
    }

    const wakeText = document.getElementById('wake-word-text');
    if (wakeText) {
        wakeText.innerHTML = isKn 
            ? 'ವೇಕ್ ವರ್ಡ್: <strong>"ಹೇ ಸಿರಿ"</strong> ಅಥವಾ <strong>"ನಮಸ್ಕಾರ"</strong> ಎಂದು ಹೇಳಿ'
            : 'Wake Word: Say <strong>"Hey Siri"</strong> or <strong>"Namaskara"</strong>';
    }

    const voiceTitle = document.getElementById('voice-card-title');
    if (voiceTitle) {
        voiceTitle.innerText = isKn ? "ಧ್ವನಿ ನೋಂದಣಿ ಮತ್ತು ಸಹಾಯ" : "Voice Registration / Hands-Free Assist";
    }

    const voiceDesc = document.getElementById('voice-card-desc');
    if (voiceDesc) {
        voiceDesc.innerText = isKn 
            ? "ಓದಲು ಅಥವಾ ಟೈಪ್ ಮಾಡಲು ಕಷ್ಟವೇ? ಕ್ಲಿಕ್ ಮಾಡಿ ಮಾತನಾಡಿ, AI ನಿಮಗಾಗಿ ನೋಂದಾಯಿಸುತ್ತದೆ!" 
            : "Difficulty reading or typing? Click & speak, AI will register for you!";
    }

    const tabLogin = document.getElementById('tab-btn-login');
    if (tabLogin) {
        tabLogin.innerHTML = `<i class="fa-solid fa-right-to-bracket" style="margin-right: 6px;"></i> ${isKn ? "ಲಾಗಿನ್" : "Sign In"}`;
    }

    const tabReg = document.getElementById('tab-btn-register');
    if (tabReg) {
        tabReg.innerHTML = `<i class="fa-solid fa-user-plus" style="margin-right: 6px;"></i> ${isKn ? "ಹೊಸ ನೋಂದಣಿ" : "Register New"}`;
    }

    const lblIdent = document.getElementById('label-identifier');
    if (lblIdent) {
        lblIdent.innerText = isKn ? "ಆಧಾರ್ / ಗ್ರಾಹಕ ಐಡಿ / ಮೊಬೈಲ್ ಸಂಖ್ಯೆ" : "Aadhaar / Customer ID / Phone";
    }
    const inpIdent = document.getElementById('identifier');
    if (inpIdent) {
        inpIdent.placeholder = isKn ? "12 ಅಂಕಿಯ ಆಧಾರ್ ಅಥವಾ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ನಮೂದಿಸಿ" : "Enter 12-digit Aadhaar or Mobile";
    }

    const lblPass = document.getElementById('label-password');
    if (lblPass) {
        lblPass.innerText = isKn ? "ಪಾಸ್‌ವರ್ಡ್" : "Password";
    }
    const inpPass = document.getElementById('password');
    if (inpPass) {
        inpPass.placeholder = isKn ? "ನಿಮ್ಮ ಪಾಸ್‌ವರ್ಡ್ ನಮೂದಿಸಿ" : "Enter your password";
    }

    const btnLogin = document.getElementById('login-btn');
    if (btnLogin && !btnLogin.disabled) {
        btnLogin.innerHTML = `<i class="fa-solid fa-right-to-bracket" style="margin-right: 8px;"></i> ${isKn ? "ಖಾತೆಗೆ ಲಾಗಿನ್ ಮಾಡಿ" : "Login to Account"}`;
    }

    const btnFp = document.getElementById('btn-fingerprint');
    if (btnFp) {
        btnFp.innerHTML = `<i class="fa-solid fa-fingerprint" style="margin-right: 8px;"></i> ${isKn ? "ಬೆರಳಚ್ಚು ದೃಢೀಕರಣ (Fingerprint)" : "Simulate Fingerprint Auth"}`;
    }

    const linkStatus = document.getElementById('link-check-status');
    if (linkStatus) {
        linkStatus.innerHTML = `<i class="fa-solid fa-magnifying-glass"></i> ${isKn ? "ಅರ್ಜಿ / ನೋಂದಣಿ ಸ್ಥಿತಿ ಪರಿಶೀಲಿಸಿ" : "Check Application / Registration Status"}`;
    }

    const regNote = document.getElementById('register-note');
    if (regNote) {
        regNote.innerHTML = isKn
            ? `<i class="fa-solid fa-circle-info" style="color: #3b82f6; margin-right: 6px;"></i> <strong>ಸೂಚನೆ:</strong> ಹೊಸ ಖಾತೆಗಳನ್ನು ಸಕ್ರಿಯಗೊಳಿಸುವ ಮೊದಲು ಪರಿಶೀಲನೆಗಾಗಿ ಬ್ಯಾಂಕ್ ನಿರ್ವಾಹಕರಿಗೆ ಸಲ್ಲಿಸಲಾಗುತ್ತದೆ.`
            : `<i class="fa-solid fa-circle-info" style="color: #3b82f6; margin-right: 6px;"></i> <strong>Note:</strong> New accounts are submitted to the Bank Administrator for verification and approval before activation.`;
    }

    const lblName = document.getElementById('label-reg-name');
    if (lblName) lblName.innerText = isKn ? "ಪೂರ್ಣ ಹೆಸರು" : "Full Name";
    const inpName = document.getElementById('reg_name');
    if (inpName) inpName.placeholder = isKn ? "ಉದಾ: ರಮೇಶ್ ಕುಮಾರ್" : "e.g. Ramesh Kumar";

    const lblPhone = document.getElementById('label-reg-phone');
    if (lblPhone) lblPhone.innerText = isKn ? "ಮೊಬೈಲ್ ಸಂಖ್ಯೆ" : "Mobile Number";
    const inpPhone = document.getElementById('reg_phone');
    if (inpPhone) inpPhone.placeholder = isKn ? "10 ಅಂಕಿಯ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ" : "10-digit phone number";

    const lblAadhaar = document.getElementById('label-reg-aadhaar');
    if (lblAadhaar) lblAadhaar.innerText = isKn ? "ಆಧಾರ್ ಸಂಖ್ಯೆ" : "Aadhaar Number";
    const inpAadhaar = document.getElementById('reg_aadhaar');
    if (inpAadhaar) inpAadhaar.placeholder = isKn ? "12 ಅಂಕಿಯ ಆಧಾರ್ ಸಂಖ್ಯೆ" : "12-digit Aadhaar number";

    const lblRegPass = document.getElementById('label-reg-password');
    if (lblRegPass) lblRegPass.innerText = isKn ? "ಪಾಸ್‌ವರ್ಡ್ ರಚಿಸಿ" : "Create Password / PIN";
    const inpRegPass = document.getElementById('reg_password');
    if (inpRegPass) inpRegPass.placeholder = isKn ? "ಕನಿಷ್ಠ 4 ಅಕ್ಷರಗಳು" : "Minimum 4 characters";

    const lblRegLang = document.getElementById('label-reg-lang');
    if (lblRegLang) lblRegLang.innerText = isKn ? "ಆದ್ಯತೆಯ ಭಾಷೆ" : "Preferred Language";

    const btnReg = document.getElementById('register-btn');
    if (btnReg && !btnReg.disabled) {
        btnReg.innerHTML = `<i class="fa-solid fa-user-check" style="margin-right: 8px;"></i> ${isKn ? "ಅನುಮೋದನೆಗಾಗಿ ನೋಂದಣಿ ಸಲ್ಲಿಸಿ" : "Submit Registration for Approval"}`;
    }

    // Status Modal (login.html)
    const statusModalH3 = document.querySelector('#statusModal h3');
    if (statusModalH3) statusModalH3.innerHTML = `<i class="fa-solid fa-clipboard-check" style="color: #4f46e5;"></i> ${isKn ? "ಅರ್ಜಿ ಸ್ಥಿತಿ ಪರಿಶೀಲನೆ" : "Application Status"}`;
    const statusModalP = document.querySelector('#statusModal p');
    if (statusModalP) statusModalP.innerText = isKn ? "ನಿಮ್ಮ ನೋಂದಣಿ ಅನುಮೋದನೆ ಸ್ಥಿತಿಯನ್ನು ತಿಳಿಯಲು ನಿಮ್ಮ ನೋಂದಾಯಿತ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ಅಥವಾ ಆಧಾರ್ ಸಂಖ್ಯೆಯನ್ನು ನಮೂದಿಸಿ." : "Enter your Registered Mobile Number or Aadhaar to check your registration approval state.";
    const statusModalInput = document.getElementById('status-checker-input');
    if (statusModalInput) statusModalInput.placeholder = isKn ? "ಮೊಬೈಲ್ ಅಥವಾ ಆಧಾರ್ ಸಂಖ್ಯೆ ನಮೂದಿಸಿ" : "Enter Phone or Aadhaar";
    const statusModalCheckBtn = document.querySelector('#statusModal button.btn-primary');
    if (statusModalCheckBtn) statusModalCheckBtn.innerText = isKn ? "ಸ್ಥಿತಿ ಪರಿಶೀಲಿಸಿ" : "Check Status";
    const statusModalCloseBtn = document.querySelector('#statusModal button[onclick*="closeStatusModal"]');
    if (statusModalCloseBtn) statusModalCloseBtn.innerText = isKn ? "ಮುಚ್ಚಿ" : "Close";

    // ── 4. HOME DASHBOARD (index.html) ──
    const bBrand = document.querySelector('.premium-balance-card .bank-brand');
    if (bBrand) bBrand.innerText = isKn ? 'ಸಿರಿ ಸೇವಿಂಗ್ಸ್' : 'SIRI SAVINGS';
    const bLabel = document.querySelector('.premium-balance-card .balance-label');
    if (bLabel) bLabel.innerText = isKn ? 'ಒಟ್ಟು ಬ್ಯಾಲೆನ್ಸ್' : 'Total Balance';

    // Credit Card Offer card
    const credCardH3 = document.querySelector('.slider-item .premium-balance-card h3');
    if (credCardH3 && (credCardH3.innerText.includes('Credit Card Offer') || credCardH3.innerText.includes('ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್'))) {
        credCardH3.innerText = isKn ? 'ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್ ಆಫರ್' : 'Credit Card Offer';
    }
    const credCardP = document.querySelector('.slider-item .premium-balance-card p');
    if (credCardP && (credCardP.innerText.includes('eligible') || credCardP.innerText.includes('ಅರ್ಹ'))) {
        credCardP.innerText = isKn 
            ? 'ಇನ್ನೂ ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್‌ಗೆ ಅರ್ಹರಾಗಿಲ್ಲ. ಸೌಲಭ್ಯ ಪಡೆಯಲು ನಮ್ಮೊಂದಿಗೆ ನಿರಂತರ ವಹಿವಾಟು ನಡೆಸಿ!' 
            : 'Not eligible for credit card yet. Keep banking with us to unlock!';
    }

    // Section Titles on Home & Other Pages
    document.querySelectorAll('.glass-card .section-title, .modules-section .section-title').forEach(t => {
        const txt = t.innerText.trim().toLowerCase();
        if (txt.includes('quick action') || txt.includes('ತ್ವರಿತ ಸೇವೆ')) {
            t.innerText = isKn ? 'ತ್ವರಿತ ಸೇವೆಗಳು' : 'Quick Actions';
        } else if (txt.includes('money transfer') || txt.includes('ಹಣ ವರ್ಗಾವಣೆ')) {
            t.innerText = isKn ? 'ಹಣ ವರ್ಗಾವಣೆ' : 'Money Transfer';
        } else if (txt.includes('recent payee') || txt.includes('ಇತ್ತೀಚಿನ ಸ್ವೀಕೃತ')) {
            t.innerText = isKn ? 'ಇತ್ತೀಚಿನ ಸ್ವೀಕೃತದಾರರು' : 'Recent Payees';
        } else if (txt.includes('upi management') || txt.includes('ಯುಪಿಐ ನಿರ್ವಹಣೆ')) {
            t.innerText = isKn ? 'ಯುಪಿಐ ನಿರ್ವಹಣೆ' : 'UPI Management';
        } else if (txt.includes('debit card quick') || txt.includes('ಡೆಬಿಟ್ ಕಾರ್ಡ್ ತ್ವರಿತ')) {
            t.innerText = isKn ? 'ಡೆಬಿಟ್ ಕಾರ್ಡ್ ತ್ವರಿತ ಕ್ರಿಯೆಗಳು' : 'Debit Card Quick Actions';
        } else if (txt.includes('credit card quick') || txt.includes('ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್ ತ್ವರಿತ')) {
            t.innerText = isKn ? 'ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್ ತ್ವರಿತ ಕ್ರಿಯೆಗಳು' : 'Credit Card Quick Actions';
        } else if (txt.includes('offers & rewards') || txt.includes('ಆಫರ್‌ಗಳು ಮತ್ತು ಬಹುಮಾನ')) {
            t.innerText = isKn ? 'ಆಫರ್‌ಗಳು ಮತ್ತು ಬಹುಮಾನಗಳು' : 'Offers & Rewards';
        } else if (txt.includes('security insights') || txt.includes('ಕಾರ್ಡ್ ಭದ್ರತಾ ಸಲಹೆ')) {
            t.innerText = isKn ? 'ಕಾರ್ಡ್ ಭದ್ರತಾ ಸಲಹೆಗಳು' : 'Security Insights';
        }
    });

    // Home Quick Action items
    const homeQaMap = [
        { fn: 'pay-phone', kn: 'ಮೊಬೈಲ್ ಪಾವತಿ', en: 'Pay Phone' },
        { fn: 'bank-transfer', kn: 'ಖಾತೆ ವರ್ಗಾವಣೆ', en: 'Transfer' },
        { fn: 'upi-pay', kn: 'ಯುಪಿಐ ಪಾವತಿ', en: 'UPI Pay' },
        { fn: 'card-settings', kn: 'ಸೆಟ್ಟಿಂಗ್ಸ್', en: 'Settings' },
        { fn: 'edit-limit', kn: 'ಮಿತಿಗಳು', en: 'Limits' },
        { fn: 'card-offers', kn: 'ಆಫರ್‌ಗಳು', en: 'Offers' },
        { fn: 'instant-loan', kn: 'ಸಾಲ', en: 'Loan' },
        { fn: 'add-money', kn: 'ಹಣ ಸೇರಿಸಿ', en: 'Add Money' }
    ];
    homeQaMap.forEach(item => {
        const el = document.querySelector(`.action-item[onclick*="${item.fn}"] .action-label`);
        if (el) el.innerText = isKn ? item.kn : item.en;
    });

    // Activity Tabs
    const tabRecent = document.querySelector('button[onclick*="switchActivityTab(\'recent\')"]');
    if (tabRecent) tabRecent.innerText = isKn ? 'ಇತ್ತೀಚಿನ ವಹಿವಾಟುಗಳು' : 'Recent Activity';
    const tabUpcoming = document.querySelector('button[onclick*="switchActivityTab(\'upcoming\')"]');
    if (tabUpcoming) tabUpcoming.innerText = isKn ? 'ಮುಂದಿನ ವಹಿವಾಟುಗಳು' : 'Upcoming Activity';

    const upEmpty = document.querySelector('#upcoming-activity-list div');
    if (upEmpty) upEmpty.innerText = isKn ? 'ಯಾವುದೇ ನಿಗದಿತ ಚಟುವಟಿಕೆಗಳಿಲ್ಲ.' : 'No upcoming activities scheduled.';

    // Virtual card details
    document.querySelectorAll('.virtual-card .card-details > div').forEach(d => {
        const firstDiv = d.querySelector('div:first-child');
        if (firstDiv) {
            const t = firstDiv.innerText.trim();
            if (t === 'Card Holder' || t === 'ಕಾರ್ಡ್‌ದಾರರು') firstDiv.innerText = isKn ? 'ಕಾರ್ಡ್‌ದಾರರು' : 'Card Holder';
            if (t === 'Valid Thru' || t === 'ಮಾನ್ಯತೆಯ ಅವಧಿ') firstDiv.innerText = isKn ? 'ಮಾನ್ಯತೆಯ ಅವಧಿ' : 'Valid Thru';
        }
    });

    // Quick Transfer Card in Right Sidebar
    const qtForm = document.getElementById('quick-transfer-form');
    if (qtForm) {
        const heading = qtForm.parentElement ? qtForm.parentElement.querySelector('h3') : null;
        if (heading) heading.innerText = isKn ? 'ತ್ವರಿತ ಹಣ ವರ್ಗಾವಣೆ' : 'Quick Transfer';
        const labels = qtForm.querySelectorAll('label');
        if (labels[0]) labels[0].innerText = isKn ? 'ಸ್ವೀಕರಿಸುವವರ ಖಾತೆ ಸಂಖ್ಯೆ' : 'Payee Account Number';
        if (labels[1]) labels[1].innerText = isKn ? 'ಮೊತ್ತ (₹)' : 'Amount (₹)';
        const accInp = document.getElementById('transfer-acc');
        if (accInp) accInp.placeholder = isKn ? 'ಉದಾ: ACC80001' : 'e.g. ACC80001';
        const chkLabel = qtForm.querySelector('label[style*="cursor: pointer"] span') || qtForm.querySelector('#is-recurring')?.parentElement;
        if (chkLabel) {
            const chkBox = chkLabel.querySelector('input');
            chkLabel.innerHTML = '';
            if (chkBox) chkLabel.appendChild(chkBox);
            chkLabel.append(isKn ? ' ಪ್ರತಿ ತಿಂಗಳು ಪುನರಾವರ್ತಿಸಿ (Standing Instruction)' : ' Set as Recurring Monthly');
        }
        const dayLabel = qtForm.querySelector('#recur-fields label, #recur-day-group label');
        if (dayLabel) dayLabel.innerText = isKn ? 'ಕಾರ್ಯಗತಗೊಳಿಸುವ ದಿನಾಂಕ (1-28)' : 'Execution Day (1-28)';
        const sendBtn = qtForm.querySelector('button[type="submit"]');
        if (sendBtn) sendBtn.innerHTML = isKn ? 'ವರ್ಗಾವಣೆ ಪ್ರಾರಂಭಿಸಿ' : 'Initialize Instruction';
    }

    // Credit Services (Loan form) in Right Sidebar
    const loanForm = document.getElementById('loan-form');
    if (loanForm) {
        const h3 = loanForm.parentElement ? loanForm.parentElement.querySelector('h3') : null;
        if (h3) h3.innerText = isKn ? 'ಸಾಲದ ಸೇವೆಗಳು' : 'Credit Services';
        const labels = loanForm.querySelectorAll('label');
        if (labels[0]) labels[0].innerText = isKn ? 'ಕೋರಿದ ಸಾಲದ ಮೊತ್ತ (₹)' : 'Requested Loan Amount (₹)';
        if (labels[1]) labels[1].innerText = isKn ? 'ಸಾಲದ ಉದ್ದೇಶ' : 'Purpose of Loan';
        const amtInp = document.getElementById('loan-amt');
        if (amtInp) amtInp.placeholder = isKn ? 'ಕನಿಷ್ಠ ₹5,000' : 'Minimum ₹5,000';
        const purInp = document.getElementById('loan-purpose');
        if (purInp) purInp.placeholder = isKn ? 'ಉದಾ: ಮನೆ ನವೀಕರಣ' : 'e.g. Home Renovation';
        const btn = document.getElementById('loan-submit-btn');
        if (btn) btn.innerText = isKn ? 'ಸಾಲಕ್ಕಾಗಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ' : 'Apply for Loan';
    }

    const sugHead = document.querySelector('#right-sidebar-panel .glass-card:last-child h4');
    if (sugHead) sugHead.innerText = isKn ? 'ಸೂಚಿಸಲಾದ ಸ್ವೀಕೃತದಾರರು' : 'Suggested Payees';

    // ── 5. PAY PAGE (pay.html) ──
    const pSearch = document.getElementById('payee-search-input');
    if (pSearch) pSearch.placeholder = isKn ? "ಹೆಸರು, ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ಅಥವಾ ಯುಪಿಐ ಐಡಿ ಹುಡುಕಿ" : "Search name, phone number or UPI ID";

    const payQaMap = [
        { fn: 'bank-transfer', kn: 'ಬ್ಯಾಂಕ್ ವರ್ಗಾವಣೆ', en: 'Bank Transfer' },
        { fn: 'pay-phone', kn: 'ಮೊಬೈಲ್‌ಗೆ', en: 'To Mobile' },
        { fn: 'location.href=\'/pay\'', kn: 'ಸ್ವಂತ ವರ್ಗಾವಣೆ', en: 'Self Trans' },
        { fn: 'upi-pay', kn: 'ಯುಪಿಐ ಐಡಿಗೆ', en: 'To UPI ID' }
    ];
    payQaMap.forEach(item => {
        const el = document.querySelector(`.action-item[onclick*="${item.fn}"] .action-label`);
        if (el) el.innerText = isKn ? item.kn : item.en;
    });

    const vVoice = document.querySelector('.btn-voice-fill span');
    if (vVoice) vVoice.innerText = isKn ? 'ಧ್ವನಿ ಮೂಲಕ ಭರ್ತಿ ಮಾಡಿ' : 'Fill by Voice';

    const vAll = document.querySelector('.glass-card a[style*="var(--primary-color)"]');
    if (vAll && (vAll.innerText === 'View All' || vAll.innerText === 'ಎಲ್ಲವನ್ನೂ ವೀಕ್ಷಿಸಿ')) {
        vAll.innerText = isKn ? 'ಎಲ್ಲವನ್ನೂ ವೀಕ್ಷಿಸಿ' : 'View All';
    }

    document.querySelectorAll('.pay-label').forEach(lbl => {
        const t = lbl.innerText.trim();
        if (t === 'Manage UPI Numbers' || t === 'ಯುಪಿಐ ಸಂಖ್ಯೆಗಳನ್ನು ನಿರ್ವಹಿಸಿ') lbl.innerText = isKn ? 'ಯುಪಿಐ ಸಂಖ್ಯೆಗಳನ್ನು ನಿರ್ವಹಿಸಿ' : 'Manage UPI Numbers';
        else if (t === 'Autopay Settings' || t === 'Manage Autopay' || t === 'ಸ್ವಯಂಚಾಲಿತ ಪಾವತಿ ಸೆಟ್ಟಿಂಗ್ಸ್' || t === 'ಸ್ವಯಂಚಾಲಿತ ಪಾವತಿ ನಿರ್ವಹಿಸಿ') lbl.innerText = isKn ? 'ಸ್ವಯಂಚಾಲಿತ ಪಾವತಿ ಸೆಟ್ಟಿಂಗ್ಸ್' : 'Autopay Settings';
        else if (t === 'Security & Limits' || t === 'ಭದ್ರತೆ ಮತ್ತು ಮಿತಿಗಳು') lbl.innerText = isKn ? 'ಭದ್ರತೆ ಮತ್ತು ಮಿತಿಗಳು' : 'Security & Limits';
    });

    // Pay offers in right sidebar
    const offerCards = document.querySelectorAll('#default-sidebar-content .glass-card div[style*="border-radius"]');
    if (offerCards.length >= 2) {
        const p1 = offerCards[0].querySelectorAll('p');
        if (p1[0]) p1[0].innerText = isKn ? 'ಫ್ಲಾಟ್ ₹50 ಕ್ಯಾಶ್‌ಬ್ಯಾಕ್' : 'Flat ₹50 Cashback';
        if (p1[1]) p1[1].innerText = isKn ? 'ನಿಮ್ಮ ಮೊದಲ ವಿದ್ಯುತ್ ಬಿಲ್ ಪಾವತಿಯಲ್ಲಿ' : 'On your first electricity bill';
        const p2 = offerCards[1].querySelectorAll('p');
        if (p2[0]) p2[0].innerText = isKn ? 'ಸ್ಕ್ರ್ಯಾಚ್ ಕಾರ್ಡ್ ಗೆಲ್ಲಿರಿ' : 'Win Scratch Cards';
        if (p2[1]) p2[1].innerText = isKn ? '₹500 ಕ್ಕಿಂತ ಹೆಚ್ಚಿನ ಪ್ರತಿ ವರ್ಗಾವಣೆಯಲ್ಲಿ' : 'On every transfer above ₹500';
    }

    // ── 6. ATM SERVICES PAGE (atm.html) ──
    const segDebit = document.querySelector('.segmented-control button:first-of-type');
    if (segDebit) segDebit.innerText = isKn ? 'ಡೆಬಿಟ್ ಕಾರ್ಡ್' : 'Debit Card';
    const segCredit = document.querySelector('.segmented-control button:last-of-type');
    if (segCredit) segCredit.innerText = isKn ? 'ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್' : 'Credit Card';

    document.querySelectorAll('.card-visual').forEach(card => {
        const labels = card.querySelectorAll('div[style*="uppercase"]');
        labels.forEach(l => {
            const txt = l.innerText.trim();
            if (txt === 'CARD HOLDER' || txt === 'ಕಾರ್ಡ್‌ದಾರರು') l.innerText = isKn ? 'ಕಾರ್ಡ್‌ದಾರರು' : 'CARD HOLDER';
            else if (txt === 'EXPIRES' || txt === 'ಮುಕ್ತಾಯ') l.innerText = isKn ? 'ಮುಕ್ತಾಯ' : 'EXPIRES';
            else if (txt === 'CREDIT LIMIT' || txt === 'ಕ್ರೆಡಿಟ್ ಮಿತಿ') l.innerText = isKn ? 'ಕ್ರೆಡಿಟ್ ಮಿತಿ' : 'CREDIT LIMIT';
        });
    });

    const notEligibleH3 = document.querySelector('.slider-item .glass-card h3');
    if (notEligibleH3 && (notEligibleH3.innerText.includes('Not Eligible') || notEligibleH3.innerText.includes('ಅರ್ಹರಲ್ಲ'))) {
        notEligibleH3.innerText = isKn ? 'ಈಗ ಅರ್ಹರಲ್ಲ' : 'Not Eligible Now';
    }
    const notEligibleP = document.querySelector('.slider-item .glass-card p');
    if (notEligibleP && (notEligibleP.innerText.includes('Complete 3 more') || notEligibleP.innerText.includes('ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್'))) {
        notEligibleP.innerText = isKn ? 'ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್ ಅನ್‌ಲಾಕ್ ಮಾಡಲು ಇನ್ನೂ 3 ತಿಂಗಳು ನಿರಂತರ ಬ್ಯಾಂಕಿಂಗ್ ಮುಂದುವರಿಸಿ.' : 'Complete 3 more months of consistent usage to unlock your Credit Card.';
    }

    const debViewText = document.getElementById('debit-view-text');
    if (debViewText) debViewText.innerText = isKn ? 'ಕಾರ್ಡ್ ವಿವರಗಳನ್ನು ವೀಕ್ಷಿಸಿ' : 'View Details';
    const debBlockText = document.getElementById('debit-block-text');
    if (debBlockText) debBlockText.innerText = isKn ? 'ಕಾರ್ಡ್ ಬ್ಲಾಕ್ ಮಾಡಿ' : 'Block Card';

    const credViewText = document.getElementById('credit-view-text');
    if (credViewText) credViewText.innerText = isKn ? 'ಕಾರ್ಡ್ ವಿವರಗಳನ್ನು ವೀಕ್ಷಿಸಿ' : 'View Details';
    const credBlockText = document.getElementById('credit-block-text');
    if (credBlockText) credBlockText.innerText = isKn ? 'ಕಾರ್ಡ್ ಬ್ಲಾಕ್ ಮಾಡಿ' : 'Block Card';

    const atmActionMap = [
        { en: 'View Details', kn: 'ಕಾರ್ಡ್ ವಿವರಗಳನ್ನು ವೀಕ್ಷಿಸಿ' },
        { en: 'Usage Limits', kn: 'ಬಳಕೆಯ ಮಿತಿಗಳು' },
        { en: 'Reset PIN', kn: 'ಪಿನ್ ಮರುಹೊಂದಿಸಿ' },
        { en: 'Block Card', kn: 'ಕಾರ್ಡ್ ಬ್ಲಾಕ್ ಮಾಡಿ' },
        { en: 'Monthly Statements', kn: 'ಮಾಸಿಕ ಸ್ಟೇಟ್‌ಮೆಂಟ್‌ಗಳು' },
        { en: 'Set Credit Limits', kn: 'ಕ್ರೆಡಿಟ್ ಮಿತಿಗಳನ್ನು ಹೊಂದಿಸಿ' },
        { en: 'Rewards & Offers', kn: 'ಬಹುಮಾನಗಳು ಮತ್ತು ಆಫರ್‌ಗಳು' }
    ];
    document.querySelectorAll('.action-row .pay-label').forEach(row => {
        const t = row.innerText.trim();
        const match = atmActionMap.find(m => m.en === t || m.kn === t);
        if (match) row.innerText = isKn ? match.kn : match.en;
    });

    const atmSubtexts = [
        { en: 'Show number, expiry, CVV', kn: 'ಸಂಖ್ಯೆ, ಮುಕ್ತಾಯ, ಸಿವಿವಿ ನೋಡಿ' },
        { en: 'ATM & Online limits', kn: 'ಎಟಿಎಂ ಮತ್ತು ಆನ್‌ಲೈನ್ ಮಿತಿಗಳು' },
        { en: 'Set new 4-digit PIN', kn: 'ಹೊಸ 4-ಅಂಕಿಯ ಪಿನ್ ಹೊಂದಿಸಿ' },
        { en: 'Instantly disable card', kn: 'ಕಾರ್ಡ್ ತಕ್ಷಣ ನಿಷ್ಕ್ರಿಯಗೊಳಿಸಿ' }
    ];
    document.querySelectorAll('.action-row div[style*="font-size: 0.75rem"]').forEach(sub => {
        const t = sub.innerText.trim();
        const match = atmSubtexts.find(m => m.en === t || m.kn === t);
        if (match) sub.innerText = isKn ? match.kn : match.en;
    });

    const cardSvcHead = document.querySelector('.atm-sidebar-dark h3');
    if (cardSvcHead) cardSvcHead.innerText = isKn ? 'ಹೊಸ ಕಾರ್ಡ್ ವಿನಂತಿ' : 'New Card Request';
    const cardSvcP = document.querySelector('.atm-sidebar-dark p');
    if (cardSvcP) cardSvcP.innerText = isKn ? 'ಬದಲಿ ಅಥವಾ ಹೆಚ್ಚುವರಿ ಕಾರ್ಡ್ ಆದೇಶಿಸಿ' : 'Order replacement or add-on card';
    const applyCardBtn = document.querySelector('.atm-apply-btn');
    if (applyCardBtn) applyCardBtn.innerHTML = `<i class="fa-solid fa-plus" style="margin-right:8px;"></i>${isKn ? "ಈಗಲೇ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ" : "Apply Now"}`;

    const secTips = document.querySelectorAll('.sec-tip span');
    if (secTips.length >= 3) {
        secTips[0].innerText = isKn ? 'ಬ್ಯಾಂಕ್ ಸಿಬ್ಬಂದಿ ಸೇರಿದಂತೆ ಯಾರಿಗೂ ನಿಮ್ಮ ಒಟಿಪಿ ಅಥವಾ ಎಟಿಎಂ ಪಿನ್ ಹಂಚಿಕೊಳ್ಳಬೇಡಿ.' : 'Never share your OTP or ATM PIN with anyone, including bank staff.';
        secTips[1].innerText = isKn ? 'ನಿಮ್ಮ ಭದ್ರತೆಗಾಗಿ ಅಂತಾರಾಷ್ಟ್ರೀಯ ವಹಿವಾಟುಗಳನ್ನು ಪೂರ್ವನಿಯೋಜಿತವಾಗಿ ನಿಷ್ಕ್ರಿಯಗೊಳಿಸಲಾಗಿದೆ.' : 'International transactions are disabled by default for your security.';
        secTips[2].innerText = isKn ? 'ಪ್ರತಿ ಕಾರ್ಡ್ ವಹಿವಾಟಿನ ತ್ವರಿತ ಅಧಿಸೂಚನೆ ಪಡೆಯಲು SMS ಎಚ್ಚರಿಕೆಗಳನ್ನು ಸಕ್ರಿಯಗೊಳಿಸಿ.' : 'Enable SMS alerts to get notified of every card transaction instantly.';
    }
    const safetyGuide = document.querySelector('.glass-card a[href="#"][style*="var(--primary-color)"]');
    if (safetyGuide && (safetyGuide.innerText.includes('Safety Guide') || safetyGuide.innerText.includes('ಸುರಕ್ಷತಾ'))) {
        safetyGuide.innerHTML = `${isKn ? "ಕಾರ್ಡ್ ಸುರಕ್ಷತಾ ಮಾರ್ಗದರ್ಶಿ" : "Card Safety Guide"} <i class="fa-solid fa-arrow-right" style="font-size:0.7rem;margin-left:4px;"></i>`;
    }

    // ATM Modals (atm.html)
    const blockModalH3 = document.querySelector('#block-modal h3');
    if (blockModalH3) blockModalH3.innerText = isKn ? "ಕಾರ್ಡ್ ಬ್ಲಾಕ್ ಮಾಡಬೇಕೇ?" : "Block Card?";
    const blockModalP = document.querySelector('#block-modal p');
    if (blockModalP) blockModalP.innerText = isKn ? "ಇದು ಈ ಕಾರ್ಡ್‌ನಲ್ಲಿನ ಎಲ್ಲಾ ವಹಿವಾಟುಗಳನ್ನು ತಕ್ಷಣವೇ ನಿಷ್ಕ್ರಿಯಗೊಳಿಸುತ್ತದೆ." : "This will instantly disable all transactions on this card. This action can only be reversed by visiting a branch.";
    const blockModalConfirm = document.querySelector('#block-modal button[onclick*="confirmBlock"]');
    if (blockModalConfirm) blockModalConfirm.innerText = isKn ? "ಹೌದು, ಬ್ಲಾಕ್ ಮಾಡಿ" : "Yes, Block it";
    const blockModalCancel = document.querySelector('#block-modal button[onclick*="closeModal"]');
    if (blockModalCancel) blockModalCancel.innerText = isKn ? "ರದ್ದುಮಾಡಿ" : "Cancel";

    const limitsModalH3 = document.querySelector('#limits-modal h3');
    if (limitsModalH3) limitsModalH3.innerText = isKn ? "ಕಾರ್ಡ್ ಬಳಕೆಯ ಮಿತಿಗಳು" : "Set Usage Limits";
    const limitsLabels = document.querySelectorAll('#limits-modal label');
    if (limitsLabels[0]) limitsLabels[0].innerText = isKn ? "ದೈನಂದಿನ ಎಟಿಎಂ ನಗದು ಮಿತಿ" : "Daily ATM Withdrawal";
    if (limitsLabels[1]) limitsLabels[1].innerText = isKn ? "ಆನ್‌ಲೈನ್ (E-com) ವಹಿವಾಟುಗಳು" : "Online (E-com) Transactions";
    const limitsSaveBtn = document.querySelector('#limits-modal button[onclick*="saveLimits"]');
    if (limitsSaveBtn) limitsSaveBtn.innerText = isKn ? "ಮಿತಿಗಳನ್ನು ಉಳಿಸಿ" : "Save Limits";
    const limitsCloseBtn = document.querySelector('#limits-modal button[onclick*="closeModal"]');
    if (limitsCloseBtn) limitsCloseBtn.innerText = isKn ? "ಮುಚ್ಚಿ" : "Close";

    const pinModalH3 = document.querySelector('#pin-modal h3');
    if (pinModalH3) pinModalH3.innerText = isKn ? "ಎಟಿಎಂ ಪಿನ್ ಮರುಹೊಂದಿಸಿ" : "Reset ATM PIN";
    const pinModalLabel = document.querySelector('#pin-modal label');
    if (pinModalLabel) pinModalLabel.innerText = isKn ? "ಹೊಸ 4-ಅಂಕಿಯ ಪಿನ್ ನಮೂದಿಸಿ" : "Enter New 4-Digit PIN";
    const pinModalSave = document.querySelector('#pin-modal button[onclick*="savePin"]');
    if (pinModalSave) pinModalSave.innerText = isKn ? "ಹೊಸ ಪಿನ್ ದೃಢೀಕರಿಸಿ" : "Confirm New PIN";
    const pinModalCancel = document.querySelector('#pin-modal button[onclick*="closeModal"]');
    if (pinModalCancel) pinModalCancel.innerText = isKn ? "ರದ್ದುಮಾಡಿ" : "Cancel";

    const applyModalH3 = document.querySelector('#apply-modal h3');
    if (applyModalH3) applyModalH3.innerText = isKn ? "ಹೊಸ ಕಾರ್ಡ್ ಅರ್ಜಿ" : "New Card Application";
    const applyModalLabels = document.querySelectorAll('#apply-modal label');
    if (applyModalLabels[0]) applyModalLabels[0].innerText = isKn ? "ಕಾರ್ಡ್ ನೆಟ್‌ವರ್ಕ್ ಆಯ್ಕೆಮಾಡಿ" : "Select Card Network";
    if (applyModalLabels[1]) applyModalLabels[1].innerText = isKn ? "ಕಾರ್ಡ್ ಮೇಲಿನ ಹೆಸರು" : "Name on Card";
    if (applyModalLabels[2]) applyModalLabels[2].innerText = isKn ? "ಕಾರ್ಡ್ ವಿಧ" : "Card Variant";
    if (applyModalLabels[3]) applyModalLabels[3].innerText = isKn ? "ವಿತರಣಾ ವಿಳಾಸ" : "Delivery Address";
    const applySubmitBtn = document.querySelector('#apply-modal button[onclick*="submitApplication"]');
    if (applySubmitBtn) applySubmitBtn.innerText = isKn ? "ಅರ್ಜಿ ಸಲ್ಲಿಸಿ" : "Submit Application";
    const applyCancelBtn = document.querySelector('#apply-modal button[onclick*="closeModal"]');
    if (applyCancelBtn) applyCancelBtn.innerText = isKn ? "ರದ್ದುಮಾಡಿ" : "Cancel";

    // ── 7. AADHAAR KYC PAGE (kyc.html) ──
    const dot1 = document.querySelector('#step-dot-1 span');
    if (dot1) dot1.innerText = isKn ? 'ವಿವರಗಳು' : 'Details';
    const dot2 = document.querySelector('#step-dot-2 span');
    if (dot2) dot2.innerText = isKn ? 'ಒಟಿಪಿ' : 'OTP';
    const dot3 = document.querySelector('#step-dot-3 span');
    if (dot3) dot3.innerText = isKn ? 'ಮುಖದ ಸ್ಕ್ಯಾನ್' : 'Face';
    const dot4 = document.querySelector('#step-dot-4 span');
    if (dot4) dot4.innerText = isKn ? 'ಪೂರ್ಣಗೊಂಡಿದೆ' : 'Done';

    const kyc1 = document.getElementById('kyc-step-1');
    if (kyc1) {
        const h3 = kyc1.querySelector('h3');
        if (h3) h3.innerText = isKn ? 'ಗುರುತಿನ ಪರಿಶೀಲನೆ' : 'Identity Verification';
        const p = kyc1.querySelector('p');
        if (p) p.innerText = isKn ? 'ಪ್ರಾರಂಭಿಸಲು ನಿಮ್ಮ 12-ಅಂಕಿಯ ಆಧಾರ್ ಸಂಖ್ಯೆಯನ್ನು ನಮೂದಿಸಿ.' : 'Enter your 12-digit Aadhaar number to begin.';
        
        const voiceBtns = kyc1.querySelectorAll('.btn-voice-fill span');
        if (voiceBtns[0]) voiceBtns[0].innerText = isKn ? 'ಧ್ವನಿ ಮೂಲಕ ಭರ್ತಿ ಮಾಡಿ' : 'Fill Details by Voice';
        if (voiceBtns[1]) voiceBtns[1].innerText = isKn ? 'AI ಮೂಲಕ ಸ್ವಯಂ ಪರಿಶೀಲಿಸಿ' : 'Simulate All by AI';

        const labels = kyc1.querySelectorAll('.input-group label');
        if (labels[0]) labels[0].innerText = isKn ? 'ಪೂರ್ಣ ಕಾನೂನುಬದ್ಧ ಹೆಸರು (ಆಧಾರ್ ಪ್ರಕಾರ)' : 'Full Legal Name (as per Aadhaar)';
        if (labels[1]) labels[1].innerText = isKn ? 'ಹುಟ್ಟಿದ ದಿನಾಂಕ' : 'Date of Birth';
        if (labels[2]) labels[2].innerText = isKn ? 'ಆಧಾರ್ ಸಂಖ್ಯೆ' : 'Aadhaar Number';
        const nameInp = document.getElementById('kyc-full-name');
        if (nameInp) nameInp.placeholder = isKn ? 'ಪೂರ್ಣ ಹೆಸರು ನಮೂದಿಸಿ' : 'Enter full name';
        const consentSpan = kyc1.querySelector('label[style*="cursor: pointer"] span');
        if (consentSpan) consentSpan.innerText = isKn ? 'ಪರಿಶೀಲನಾ ಉದ್ದೇಶಕ್ಕಾಗಿ ಯುಐಡಿಎಐ ನಿಂದ ನನ್ನ ಇ-ಕೆವೈಸಿ ವಿವರಗಳನ್ನು ಪಡೆಯಲು ನಾನು ಸಿರಿ ಬ್ಯಾಂಕ್‌ಗೆ ಸಮ್ಮತಿ ನೀಡುತ್ತೇನೆ.' : 'I hereby give my consent to SIRI BANK to fetch my e-KYC details from UIDAI for verification purposes.';
        const genOtpBtn = kyc1.querySelector('button[type="submit"]');
        if (genOtpBtn) genOtpBtn.innerHTML = `${isKn ? "ಆಧಾರ್ ಒಟಿಪಿ ಪಡೆಯಿರಿ" : "Get OTP"}`;
    }

    const kyc2 = document.getElementById('kyc-step-2');
    if (kyc2) {
        const h3 = kyc2.querySelector('h3');
        if (h3) h3.innerText = isKn ? 'ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ಪರಿಶೀಲಿಸಿ' : 'Verify Mobile Number';
        const p = kyc2.querySelector('p');
        if (p) p.innerText = isKn ? 'ನಿಮ್ಮ ಆಧಾರ್ ಲಿಂಕ್ ಆದ ಮೊಬೈಲ್‌ಗೆ 6-ಅಂಕಿಯ ಒಟಿಪಿ ಕಳುಹಿಸಲಾಗಿದೆ.' : 'An OTP has been sent to your Aadhaar-linked mobile (XXXXXX5678).';
        const otpLbl = kyc2.querySelector('.input-group label');
        if (otpLbl) otpLbl.innerText = isKn ? '6-ಅಂಕಿಯ ಒಟಿಪಿ ನಮೂದಿಸಿ' : '6-Digit OTP';
        const resendP = kyc2.querySelector('p[style*="text-align: center"]');
        if (resendP) {
            resendP.innerHTML = `${isKn ? "ಒಟಿಪಿ ಬಂದಿಲ್ಲವೇ?" : "Didn't receive?"} <a href="#" style="color: var(--primary-color); font-weight: 600;">${isKn ? "30 ಸೆಕೆಂಡುಗಳಲ್ಲಿ ಮರುಕಳುಹಿಸಿ" : "Resend in 30s"}</a>`;
        }
        const verifyBtn = kyc2.querySelector('button[type="submit"]');
        if (verifyBtn) verifyBtn.innerHTML = `${isKn ? "ಒಟಿಪಿ ಪರಿಶೀಲಿಸಿ" : "Verify OTP"}`;
    }

    const kyc3 = document.getElementById('kyc-step-3');
    if (kyc3) {
        const h3 = kyc3.querySelector('h3');
        if (h3) h3.innerText = isKn ? 'ಮುಖದ ಲೈವ್ ಪರಿಶೀಲನೆ' : 'Face Liveness Check';
        const p = kyc3.querySelector('p');
        if (p) p.innerText = isKn ? 'ನಿಮ್ಮ ಮುಖವನ್ನು ಮಧ್ಯದಲ್ಲಿ ಇರಿಸಿ ಮತ್ತು ಸೂಚನೆಗಳನ್ನು ಅನುಸರಿಸಿ.' : 'Position your face in the center and follow the instructions.';
        const faceInst = document.getElementById('face-instructions');
        if (faceInst && (faceInst.innerText === 'Ready to Start?' || faceInst.innerText === 'ಪ್ರಾರಂಭಿಸಲು ಸಿದ್ಧವೇ?')) {
            faceInst.innerText = isKn ? 'ಪ್ರಾರಂಭಿಸಲು ಸಿದ್ಧವೇ?' : 'Ready to Start?';
        }
        const scanBtn = document.getElementById('start-scan-btn') || document.getElementById('btn-capture-face');
        if (scanBtn) scanBtn.innerText = isKn ? 'ಮುಖದ ಸ್ಕ್ಯಾನ್ ಪ್ರಾರಂಭಿಸಿ' : 'Start Liveness Check';
    }

    const kyc4 = document.getElementById('kyc-step-4');
    if (kyc4) {
        const h2 = kyc4.querySelector('h2');
        if (h2) h2.innerText = isKn ? 'ಕೆವೈಸಿ ಯಶಸ್ವಿಯಾಗಿ ಸಲ್ಲಿಸಲಾಗಿದೆ!' : 'KYC Completed!';
        const p = kyc4.querySelector('p');
        if (p) p.innerText = isKn ? 'ನಿಮ್ಮ ವಿವರಗಳನ್ನು ಸಲ್ಲಿಸಲಾಗಿದೆ ಮತ್ತು ಅನುಮೋದನೆ ಪ್ರಕ್ರಿಯೆಯಲ್ಲಿದೆ. ಶೀಘ್ರದಲ್ಲೇ ಖಾತೆ ನವೀಕರಣಗೊಳ್ಳಲಿದೆ.' : 'Your documents have been submitted and are pending approval. Your account will be updated shortly.';
        const goBtn = kyc4.querySelector('button');
        if (goBtn) goBtn.innerText = isKn ? 'ಮುಖಪುಟಕ್ಕೆ ಹೋಗಿ' : 'Go to Dashboard';
    }

    const kycStatusH2 = document.querySelector('.glass-card h2');
    if (kycStatusH2) {
        const t = kycStatusH2.innerText.trim();
        if (t.includes('Verified') || t.includes('ಪರಿಶೀಲಿಸಲಾಗಿದೆ')) {
            kycStatusH2.innerText = isKn ? 'ಕೆವೈಸಿ ಪರಿಶೀಲಿಸಲಾಗಿದೆ' : 'KYC Verified';
            const statP = kycStatusH2.parentElement ? kycStatusH2.parentElement.querySelector('p') : null;
            if (statP) statP.innerText = isKn ? 'ನಿಮ್ಮ ಖಾತೆಯನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಪರಿಶೀಲಿಸಲಾಗಿದೆ. ಹೆಚ್ಚಿನ ಮಿತಿಯ ವರ್ಗಾವಣೆ ಸೇರಿದಂತೆ ಎಲ್ಲಾ ಸೇವೆಗಳನ್ನು ನೀವು ಬಳಸಬಹುದು.' : 'Your account is fully verified. You have access to all premium features including high-limit transfers.';
        } else if (t.includes('Pending') || t.includes('ಪ್ರಕ್ರಿಯೆಯಲ್ಲಿದೆ')) {
            kycStatusH2.innerText = isKn ? 'ಪರಿಶೀಲನೆ ಪ್ರಕ್ರಿಯೆಯಲ್ಲಿದೆ' : 'Verification Pending';
            const statP = kycStatusH2.parentElement ? kycStatusH2.parentElement.querySelector('p') : null;
            if (statP) statP.innerText = isKn ? 'ನಾವು ನಿಮ್ಮ ದಾಖಲೆಗಳನ್ನು ಪರಿಶೀಲಿಸುತ್ತಿದ್ದೇವೆ. ಪರಿಶೀಲನೆ ಮುಗಿದ ತಕ್ಷಣ ನಿಮಗೆ ತಿಳಿಸಲಾಗುತ್ತದೆ.' : "We are currently reviewing your documents. This usually takes 24-48 hours. We'll notify you once it's done.";
        } else if (t.includes('Rejected') || t.includes('ತಿರಸ್ಕರಿಸಲಾಗಿದೆ')) {
            kycStatusH2.innerText = isKn ? 'ಪರಿಶೀಲನೆ ತಿರಸ್ಕರಿಸಲಾಗಿದೆ' : 'Verification Rejected';
            const rejReasonP = document.querySelector('.glass-card p[style*="#dc2626"]');
            if (rejReasonP && rejReasonP.innerText.includes('Reason:')) {
                rejReasonP.innerHTML = rejReasonP.innerHTML.replace('Reason:', isKn ? 'ಕಾರಣ:' : 'Reason:');
            } else if (rejReasonP && rejReasonP.innerText.includes('ಕಾರಣ:')) {
                rejReasonP.innerHTML = rejReasonP.innerHTML.replace('ಕಾರಣ:', isKn ? 'ಕಾರಣ:' : 'Reason:');
            }
            const descP = document.querySelector('.glass-card p[style*="64748b"]');
            if (descP) descP.innerText = isKn ? 'ದುರದೃಷ್ಟವಶಾತ್ ನಿಮ್ಮ ಪರಿಶೀಲನೆ ಯಶಸ್ವಿಯಾಗಿಲ್ಲ. ದಯವಿಟ್ಟು ವಿವರಗಳನ್ನು ಪರಿಶೀಲಿಸಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.' : 'Unfortunately, your verification was not successful. Please re-check your details and try again.';
        }
    }
    const retryBtn = document.querySelector('button[onclick*="/aadhaar-kyc?retry=true"]');
    if (retryBtn) retryBtn.innerText = isKn ? 'ಮತ್ತೆ ಕೆವೈಸಿ ಮಾಡಿ' : 'Retry KYC';
    const backDashBtn = document.querySelector('button[onclick*="/home"]');
    if (backDashBtn) backDashBtn.innerText = isKn ? 'ಮುಖಪುಟಕ್ಕೆ ಹಿಂತಿರುಗಿ' : 'Back to Dashboard';

    // ── 8. REQUEST HISTORY PAGE (history.html) ──
    const statHistoryMap = [
        { id: 'stat-total-requests', kn: 'ಒಟ್ಟು ವಿನಂತಿಗಳು', en: 'Total Requests' },
        { id: 'stat-pending-requests', kn: 'ಪರಿಶೀಲನೆಯಲ್ಲಿರುವವು', en: 'Pending Review' },
        { id: 'stat-approved-requests', kn: 'ಅನುಮೋದಿತ / ಸಕ್ರಿಯ', en: 'Approved / Active' },
        { id: 'stat-total-txns', kn: 'ವಹಿವಾಟುಗಳು', en: 'Transactions' }
    ];
    statHistoryMap.forEach(item => {
        const el = document.getElementById(item.id);
        if (el && el.parentElement) {
            const h4 = el.parentElement.querySelector('h4');
            if (h4) h4.innerText = isKn ? item.kn : item.en;
        }
    });

    const stmtBtn = document.querySelector('button[onclick*="statement"]');
    if (stmtBtn) stmtBtn.innerHTML = `<i class="fa-solid fa-download" style="margin-right: 5px;"></i> ${isKn ? "ಸ್ಟೇಟ್‌ಮೆಂಟ್ ಡೌನ್‌ಲೋಡ್" : "Download Statement"}`;

    const tAll = document.getElementById('tab-all');
    if (tAll) tAll.innerHTML = `<i class="fa-solid fa-layer-group"></i> ${isKn ? "ಎಲ್ಲಾ ಇತಿಹಾಸ" : "All History"}`;
    const tReqs = document.getElementById('tab-requests');
    if (tReqs) {
        const countBadge = document.getElementById('count-badge-reqs');
        const count = countBadge ? countBadge.innerText : '0';
        tReqs.innerHTML = `<i class="fa-solid fa-id-card"></i> ${isKn ? "ಸೇವಾ ವಿನಂತಿಗಳು" : "Service Requests"} (<span id="count-badge-reqs">${count}</span>)`;
    }
    const tTxns = document.getElementById('tab-transactions');
    if (tTxns) {
        const countBadge = document.getElementById('count-badge-txns');
        const count = countBadge ? countBadge.innerText : '0';
        tTxns.innerHTML = `<i class="fa-solid fa-arrow-right-arrow-left"></i> ${isKn ? "ವಹಿವಾಟುಗಳು" : "Transactions"} (<span id="count-badge-txns">${count}</span>)`;
    }

    const secReqH3 = document.querySelector('#section-service-requests .section-header h3');
    if (secReqH3) secReqH3.innerHTML = `<i class="fa-solid fa-bell-concierge" style="color:var(--primary-color);"></i> ${isKn ? "ಬ್ಯಾಂಕಿಂಗ್ ಸೇವಾ ವಿನಂತಿಗಳು" : "Banking Service Requests"}`;
    const secTxnH3 = document.querySelector('#section-transactions .section-header h3');
    if (secTxnH3) secTxnH3.innerHTML = `<i class="fa-solid fa-receipt" style="color:#059669;"></i> ${isKn ? "ಹಣಕಾಸು ವಹಿವಾಟುಗಳು" : "Financial Transactions"}`;

    const reqHeaderKyc = document.querySelector('#section-service-requests a[href="/aadhaar-kyc"]');
    if (reqHeaderKyc) reqHeaderKyc.innerHTML = `<i class="fa-solid fa-id-card"></i> ${isKn ? "ಆಧಾರ್ ಕೆವೈಸಿ" : "Aadhaar KYC"}`;
    const reqHeaderAtm = document.querySelector('#section-service-requests a[href="/atm-services"]');
    if (reqHeaderAtm) reqHeaderAtm.innerHTML = `<i class="fa-solid fa-credit-card"></i> ${isKn ? "ಕಾರ್ಡ್ ವಿನಂತಿ" : "Request Card"}`;
    const txnHeaderPay = document.querySelector('#section-transactions a[href="/pay"]');
    if (txnHeaderPay) txnHeaderPay.innerHTML = `<i class="fa-solid fa-paper-plane"></i> ${isKn ? "ಹಣ ಪಾವತಿಸಿ" : "Make Payment"}`;

    // ── 9. PROFILE PAGE (profile.html) ──
    const heroBadge = document.querySelector('.hero-badge');
    if (heroBadge) {
        heroBadge.innerHTML = `<span class="status-dot"></span> ${isKn ? "ದೃಢೀಕರಿಸಿದ ಖಾತೆ" : "VERIFIED ACCOUNT"}`;
    }
    const heroUpi = document.getElementById('hero-upi');
    if (heroUpi && heroUpi.innerText.includes('Fetching')) {
        heroUpi.innerText = isKn ? "ಯುಪಿಐ ಐಡಿ ಪಡೆಯಲಾಗುತ್ತಿದೆ..." : "Fetching UPI ID...";
    }

    const chipBalance = document.querySelector('.stat-chip:nth-child(1) .stat-chip-label');
    if (chipBalance) chipBalance.innerText = isKn ? 'ಖಾತೆ ಬ್ಯಾಲೆನ್ಸ್' : 'Balance';
    const chipCust = document.querySelector('.stat-chip:nth-child(2) .stat-chip-label');
    if (chipCust) chipCust.innerText = isKn ? 'ಗ್ರಾಹಕ ಐಡಿ' : 'Cust. ID';
    const chipStatus = document.querySelector('.stat-chip:nth-child(3) .stat-chip-label');
    if (chipStatus) chipStatus.innerText = isKn ? 'ಖಾತೆ ಸ್ಥಿತಿ' : 'Status';
    const statStatusVal = document.getElementById('stat-status');
    if (statStatusVal) {
        const raw = statStatusVal.innerText.trim();
        if (raw.includes('ACTIVE') || raw.includes('ಸಕ್ರಿಯ') || raw.includes('APPROVED')) {
            statStatusVal.innerHTML = '<span style="color:#059669;font-size:0.8rem;">● ' + (isKn ? 'ಸಕ್ರಿಯ' : 'ACTIVE') + '</span>';
        }
    }

    document.querySelectorAll('.info-card').forEach(card => {
        const title = card.querySelector('.info-card-title');
        if (title) {
            const t = title.innerText.trim();
            if (t.includes('Account Information') || t.includes('ಖಾತೆಯ ಮಾಹಿತಿ')) title.innerHTML = `<i class="fa-solid fa-building-columns"></i> ${isKn ? "ಖಾತೆಯ ಮಾಹಿತಿ" : "Account Information"}`;
            else if (t.includes('Branch') || t.includes('ಶಾಖೆ')) title.innerHTML = `<i class="fa-solid fa-shield-check"></i> ${isKn ? "ಶಾಖೆ ಮತ್ತು ಭದ್ರತೆ" : "Branch & Security"}`;
        }
        card.querySelectorAll('.info-row').forEach(row => {
            const key = row.querySelector('.info-key');
            if (key) {
                const txt = key.innerText.trim();
                if (txt.includes('Account No') || txt.includes('ಖಾತೆ ಸಂಖ್ಯೆ')) key.innerHTML = `<i class="fa-solid fa-hashtag"></i> ${isKn ? "ಖಾತೆ ಸಂಖ್ಯೆ" : "Account No."}`;
                else if (txt.includes('UPI ID') || txt.includes('ಯುಪಿಐ ಐಡಿ')) key.innerHTML = `<i class="fa-solid fa-at"></i> ${isKn ? "ಯುಪಿಐ ಐಡಿ" : "UPI ID"}`;
                else if (txt.includes('IFSC') || txt.includes('IFSC ಕೋಡ್')) key.innerHTML = `<i class="fa-solid fa-landmark"></i> ${isKn ? "IFSC ಕೋಡ್" : "IFSC"}`;
                else if (txt.includes('Branch') || txt.includes('ಶಾಖೆ')) key.innerHTML = `<i class="fa-solid fa-location-dot"></i> ${isKn ? "ಶಾಖೆ" : "Branch"}`;
                else if (txt.includes('Network') || txt.includes('ನೆಟ್‌ವರ್ಕ್')) key.innerHTML = `<i class="fa-solid fa-globe"></i> ${isKn ? "ನೆಟ್‌ವರ್ಕ್" : "Network"}`;
                else if (txt.includes('Security') || txt.includes('ಭದ್ರತೆ')) key.innerHTML = `<i class="fa-solid fa-lock"></i> ${isKn ? "ಭದ್ರತೆ" : "Security"}`;
            }
            const val = row.querySelector('.info-val');
            if (val) {
                const vt = val.innerText.trim();
                if (vt === 'SIRI HQ – Main' || vt === 'ಸಿರಿ ಮುಖ್ಯ ಶಾಖೆ') val.innerText = isKn ? 'ಸಿರಿ ಮುಖ್ಯ ಶಾಖೆ' : 'SIRI HQ – Main';
                else if (vt === 'SIRI AI Banking' || vt === 'ಸಿರಿ AI ಬ್ಯಾಂಕಿಂಗ್') val.innerText = isKn ? 'ಸಿರಿ AI ಬ್ಯಾಂಕಿಂಗ್' : 'SIRI AI Banking';
                else if (vt === 'E2E Encrypted' || vt === 'ಸಂಪೂರ್ಣ ಎನ್‌ಕ್ರಿಪ್ಟ್ ಮಾಡಲಾಗಿದೆ') val.innerText = isKn ? 'ಸಂಪೂರ್ಣ ಎನ್‌ಕ್ರಿಪ್ಟ್ ಮಾಡಲಾಗಿದೆ' : 'E2E Encrypted';
            }
        });
    });

    const profKycBtn = document.querySelector('.btn-action-primary');
    if (profKycBtn) profKycBtn.innerHTML = `<i class="fa-solid fa-id-card"></i> ${isKn ? "ಕೆವೈಸಿ ನವೀಕರಿಸಿ" : "Update KYC"}`;
    const profLogoutBtn = document.querySelector('.btn-action-danger') || document.querySelector('.btn-logout-profile');
    if (profLogoutBtn) profLogoutBtn.innerHTML = `<i class="fa-solid fa-arrow-right-from-bracket"></i> ${isKn ? "ಖಾತೆಯಿಂದ ಲಾಗ್ ಔಟ್ ಮಾಡಿ" : "Sign Out"}`;

    // ── 10. SIDEBAR DYNAMIC ACTION TOOLS (Home & Pay) ──
    // Pay Phone
    const sidePhone = document.getElementById('sidebar-pay-phone');
    if (sidePhone) {
        const h3 = sidePhone.querySelector('h3');
        if (h3) h3.innerText = isKn ? "ಮೊಬೈಲ್ ಸಂಖ್ಯೆಗೆ ಪಾವತಿ" : "Pay to Mobile Number";
        const p = sidePhone.querySelector('p');
        if (p) p.innerText = isKn ? "ತಕ್ಷಣವೇ ಯಾವುದೇ ಸಿರಿ ಬ್ಯಾಂಕ್ ಅಥವಾ ಯುಪಿಐ ಬಳಕೆದಾರರಿಗೆ ಹಣ ಕಳುಹಿಸಿ" : "Instantly transfer funds to any SIRI Bank or UPI user";
        const lblPhone = document.getElementById('lbl-side-pay-phone');
        if (lblPhone) lblPhone.innerText = isKn ? "ಸ್ವೀಕರಿಸುವವರ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ" : "Recipient Mobile Number";
        const lblAmt = document.getElementById('lbl-side-pay-amt');
        if (lblAmt) lblAmt.innerText = isKn ? "ಕಳುಹಿಸಬೇಕಾದ ಮೊತ್ತ (₹)" : "Amount to Send (₹)";
        const inp = document.getElementById('side-pay-phone');
        if (inp) inp.placeholder = isKn ? "10 ಅಂಕಿಯ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ನಮೂದಿಸಿ" : "Enter 10-digit mobile number";
        const btn = document.getElementById('side-confirm-pay');
        if (btn) btn.innerText = isKn ? "ಪಾವತಿ ದೃಢೀಕರಿಸಿ" : "Confirm Payment";
    }

    // Bank Transfer
    const sideBank = document.getElementById('sidebar-bank-transfer');
    if (sideBank) {
        const h3 = sideBank.querySelector('h3');
        if (h3) h3.innerText = isKn ? "ನೇರ ಬ್ಯಾಂಕ್ ವರ್ಗಾವಣೆ" : "Direct Bank Transfer";
        const p = sideBank.querySelector('p');
        if (p) p.innerText = isKn ? "ಖಾತೆ ಸಂಖ್ಯೆ ಬಳಸಿ ಸುರಕ್ಷಿತವಾಗಿ ಹಣ ವರ್ಗಾಯಿಸಿ" : "Securely transfer money using Account Number";
        const labels = sideBank.querySelectorAll('label');
        if (labels[0]) labels[0].innerText = isKn ? "ಸ್ವೀಕರಿಸುವವರ ಖಾತೆ ಸಂಖ್ಯೆ" : "Payee Account Number";
        if (labels[1]) labels[1].innerText = isKn ? "ವರ್ಗಾವಣೆ ಮಾಡಬೇಕಾದ ಮೊತ್ತ (₹)" : "Amount to Transfer (₹)";
        const btn = sideBank.querySelector('button[type="submit"]');
        if (btn) btn.innerText = isKn ? "ವರ್ಗಾವಣೆ ಪೂರ್ಣಗೊಳಿಸಿ" : "Execute Transfer";
    }

    // UPI Pay
    const sideUpi = document.getElementById('sidebar-upi-pay');
    if (sideUpi) {
        const h3 = sideUpi.querySelector('h3');
        if (h3) h3.innerText = isKn ? "ಯುಪಿಐ ಪಾವತಿ" : "UPI Instant Transfer";
        const p = sideUpi.querySelector('p');
        if (p) p.innerText = isKn ? "ವರ್ಚುವಲ್ ಪೇಮೆಂಟ್ ವಿಳಾಸ (VPA) ಗೆ ಹಣ ಕಳುಹಿಸಿ" : "Send money to any Virtual Payment Address (VPA)";
        const labels = sideUpi.querySelectorAll('label');
        if (labels[0]) labels[0].innerText = isKn ? "ಸ್ವೀಕರಿಸುವವರ ಯುಪಿಐ ಐಡಿ" : "Payee UPI ID";
        if (labels[1]) labels[1].innerText = isKn ? "ಮೊತ್ತ (₹)" : "Amount (₹)";
        const btn = sideUpi.querySelector('button[type="submit"]');
        if (btn) btn.innerText = isKn ? "ಯುಪಿಐ ಮೂಲಕ ಪಾವತಿಸಿ" : "Pay via UPI";
    }

    // Instant Loan
    const sideLoan = document.getElementById('sidebar-instant-loan');
    if (sideLoan) {
        const h3 = sideLoan.querySelector('h3');
        if (h3) h3.innerText = isKn ? "ತ್ವರಿತ ಸಾಲ ಸೌಲಭ್ಯ" : "Instant Pre-Approved Loan";
        const p = sideLoan.querySelector('p');
        if (p) p.innerText = isKn ? "ಯಾವುದೇ ಕಾಗದಪತ್ರಗಳಿಲ್ಲದೆ ತಕ್ಷಣವೇ ಸಾಲ ಪಡೆಯಿರಿ" : "Zero documentation instant credit to your account";
        const labels = sideLoan.querySelectorAll('label');
        if (labels[0]) labels[0].innerText = isKn ? "ಅಗತ್ಯವಿರುವ ಸಾಲದ ಮೊತ್ತ (₹)" : "Required Loan Amount (₹)";
        if (labels[1]) labels[1].innerText = isKn ? "ಸಾಲದ ಉದ್ದೇಶ" : "Purpose of Loan";
        const btn = sideLoan.querySelector('button[type="submit"]');
        if (btn) btn.innerText = isKn ? "ಸಾಲದ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ" : "Apply for Loan";
    }

    // Add Money
    const sideAdd = document.getElementById('sidebar-add-money');
    if (sideAdd) {
        const h3 = sideAdd.querySelector('h3');
        if (h3) h3.innerText = isKn ? "ಖಾತೆಗೆ ಹಣ ಸೇರಿಸಿ" : "Add Funds to Account";
        const labels = sideAdd.querySelectorAll('label');
        if (labels[0]) labels[0].innerText = isKn ? "ಠೇವಣಿ ಮೊತ್ತ (₹)" : "Deposit Amount (₹)";
        const btn = sideAdd.querySelector('button[type="submit"]');
        if (btn) btn.innerText = isKn ? "ಹಣ ಸೇರಿಸಿ" : "Add Money";
    }

    // ── 11. CHAT ASSISTANT UI ──
    const chatTitle = document.querySelector('.chat-title');
    if (chatTitle) {
        chatTitle.innerHTML = `<i class="fa-solid fa-shield-halved" style="margin-right: 6px; color: var(--primary-color);"></i> ${isKn ? "ಸಿರಿ ಬ್ಯಾಂಕ್ AI ಸಹಾಯಕ" : "SIRI BANK AI Assistant"}`;
    }

    const initialGreeting = document.querySelector('#chat-messages .initial-bot-greeting');
    if (initialGreeting) {
        initialGreeting.innerText = isKn
            ? "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ SIRI BANK AI ಸಹಾಯಕ. ನೀವು ಕನ್ನಡ ಅಥವಾ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಮಾತನಾಡಬಹುದು!"
            : "Hello! I am your SIRI BANK AI Assistant. You can speak with me in English or Kannada!";
    }
}

function restoreSavedLanguage() {
    let savedLang = localStorage.getItem('siri_bank_lang');
    if (!savedLang || (savedLang !== 'Kannada' && savedLang !== 'English')) {
        const topLang = document.getElementById('language-selector');
        if (topLang && (topLang.value === 'Kannada' || topLang.value === 'English')) {
            savedLang = topLang.value;
        } else {
            savedLang = 'Kannada';
        }
    }
    syncVoiceLanguage(savedLang);
}

function injectVoiceAssistantBar() {
    // 1. Purge separate buttons: Remove topbar button & top voice bar to ensure ONLY 1 single floating AI button
    const oldTopBtn = document.getElementById('topbar-ai-btn');
    if (oldTopBtn) oldTopBtn.remove();

    const oldBar = document.getElementById('voice-assistant-bar');
    if (oldBar) oldBar.remove();

    const savedLang = localStorage.getItem('siri_bank_lang') || 'English';

    // 2. Inject the single unified floating AI button and chat container
    if (!document.getElementById('chat-container')) {
        const chatHtml = `
        <div id="chat-widget-wrapper" style="position: fixed; bottom: 25px; right: 25px; z-index: 999999; display: flex; flex-direction: column; align-items: flex-end; gap: 8px;">
            <div id="ai-callout-badge" class="ai-callout-badge" onclick="toggleChat()" title="Click to chat or say 'Hey Siri' / 'Namaskara'" style="background: rgba(15, 23, 42, 0.94); color: #38bdf8; padding: 6px 14px; border-radius: 20px; font-size: 0.78rem; font-weight: 700; cursor: pointer; box-shadow: 0 8px 24px rgba(0,0,0,0.35); border: 1px solid rgba(56, 189, 248, 0.35); display: flex; align-items: center; gap: 8px; backdrop-filter: blur(12px); transition: all 0.3s ease;">
                <span class="ai-badge-dot" style="width: 8px; height: 8px; border-radius: 50%; background: #10b981; display: inline-block; box-shadow: 0 0 8px #10b981;"></span>
                <span id="ai-badge-text">SIRI AI (${savedLang === 'Kannada' ? "ಹೇಳಿ: 'ಹೇ ಸಿರಿ' / 'ನಮಸ್ಕಾರ'" : "Say 'Hey Siri' / 'Namaskara'"})</span>
            </div>
            <div id="chat-orb-container" class="chat-orb-container state-standby" onclick="toggleChat()">
                <div class="orb-aura-glow"></div>
                <div class="orb-pulse-ring ring-primary"></div>
                <div class="orb-pulse-ring ring-secondary"></div>
                <button id="chat-toggle-btn" class="chat-toggle-btn" title="SIRI AI Assistant" aria-label="Open SIRI AI Assistant">
                    <i class="fa-solid fa-robot"></i>
                </button>
            </div>
        </div>
        <div id="chat-container" class="chat-container" style="position: fixed; bottom: 100px; right: 25px; z-index: 999999; width: 385px; max-width: calc(100vw - 32px); height: 530px; max-height: 80vh; border-radius: 18px; box-shadow: 0 20px 40px rgba(0,0,0,0.25); display: none; flex-direction: column; overflow: hidden; background: #f8fafc; border: 1px solid rgba(226, 232, 240, 0.9);">
            <!-- Chat Header with Unified Controls -->
            <div class="chat-header" style="background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%); color: white; padding: 12px 14px; display: flex; justify-content: space-between; align-items: center; border-radius: 18px 18px 0 0; flex-shrink: 0;">
                <div style="display: flex; align-items: center; gap: 10px; min-width: 0;">
                    <div style="width: 34px; height: 34px; border-radius: 10px; background: rgba(255,255,255,0.15); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <i class="fa-solid fa-robot" style="font-size: 1.1rem; color: #38bdf8;"></i>
                    </div>
                    <div style="min-width: 0;">
                        <h4 style="margin: 0; font-size: 0.92rem; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">SIRI AI Assistant</h4>
                        <span id="chat-header-status" style="font-size: 0.72rem; color: #a5b4fc; display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">💤 ${savedLang === 'Kannada' ? "ಸಿದ್ಧವಾಗಿದೆ (Say 'Hey Siri' or 'ನಮಸ್ಕಾರ')" : "Ready (Say 'Hey Siri' or 'Namaskara')"}</span>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 6px; flex-shrink: 0;">
                    <!-- Single Unified Language Switcher -->
                    <select id="chat-header-lang" onchange="syncVoiceLanguage(this.value)" title="Change Language" style="background: rgba(255,255,255,0.18); color: white; border: 1px solid rgba(255,255,255,0.3); border-radius: 14px; font-size: 0.75rem; font-weight: 600; padding: 4px 8px; cursor: pointer; outline: none;">
                        <option value="English" ${savedLang === 'English' ? 'selected' : ''}>English</option>
                        <option value="Kannada" ${savedLang === 'Kannada' ? 'selected' : ''}>ಕನ್ನಡ</option>
                    </select>
                    <!-- Screen Reader Button -->
                    <button onclick="readCurrentScreenAloud()" title="Read Screen Aloud (ಸ್ಕ್ರೀನ್ ಓದಿ)" style="background: rgba(255,255,255,0.18); color: white; border: 1px solid rgba(255,255,255,0.3); border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 0.8rem; transition: background 0.2s;">
                        <i class="fa-solid fa-volume-high"></i>
                    </button>
                    <!-- Delete Full Chat Button -->
                    <button id="chat-delete-btn" onclick="clearFullChat()" title="Delete Full Chat (ಸಂಪೂರ್ಣ ಸಂಭಾಷಣೆ ಅಳಿಸಿ)" style="background: rgba(239, 68, 68, 0.25); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.45); border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 0.78rem; transition: all 0.2s;" onmouseover="this.style.background='rgba(239,68,68,0.55)'; this.style.color='#ffffff';" onmouseout="this.style.background='rgba(239,68,68,0.25)'; this.style.color='#fca5a5';">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                    <!-- Close Button -->
                    <button onclick="closeChat()" title="Close Assistant" style="background: none; border: none; color: white; cursor: pointer; font-size: 1.15rem; opacity: 0.85; padding: 2px 4px; line-height: 1;">
                        <i class="fa-solid fa-times"></i>
                    </button>
                </div>
            </div>
            
            <!-- Chat Messages Scroll Area -->
            <div class="chat-messages" id="chat-messages" style="flex: 1; height: 320px; overflow-y: auto; padding: 1rem; background: #f8fafc; display: flex; flex-direction: column; gap: 10px;">
                <div class="message bot initial-bot-greeting" style="background: white; padding: 12px 14px; border-radius: 14px; box-shadow: 0 2px 6px rgba(0,0,0,0.04); font-size: 0.88rem; line-height: 1.45; border-left: 3px solid #4f46e5;">
                    ${savedLang === 'Kannada' 
                        ? "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ SIRI BANK AI ಸಹಾಯಕ. ನೀವು ಕನ್ನಡ ಅಥವಾ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಮಾತನಾಡಬಹುದು!" 
                        : "Hello! I am your SIRI BANK AI Assistant. You can speak with me in English or Kannada!"}
                </div>
            </div>

            <!-- Chat Input Area with Live Speech & Activity Reset -->
            <div class="chat-input-area" style="padding: 10px 12px; background: white; border-top: 1px solid #e2e8f0; display: flex; gap: 8px; align-items: center; flex-shrink: 0;">
                <button id="mic-btn" onclick="toggleVoice()" class="idle-pulse" title="Speak to SIRI AI (30s window)" style="background: #eef2ff; color: #4f46e5; border: none; width: 40px; height: 40px; border-radius: 50%; cursor: pointer; font-size: 1.1rem; flex-shrink: 0; display: flex; align-items: center; justify-content: center; transition: all 0.2s;">
                    <i class="fa-solid fa-microphone"></i>
                </button>
                <input type="text" id="chat-input" placeholder="${savedLang === 'Kannada' ? "ಮಾತನಾಡಿ ಅಥವಾ ಟೈಪ್ ಮಾಡಿ..." : "Type a message or use voice..."}" oninput="if(typeof SiriSpeechEngine !== 'undefined') SiriSpeechEngine.resetTimer()" onkeypress="if(event.key === 'Enter') sendMessage()" style="flex-grow: 1; padding: 10px 14px; border: 1px solid #cbd5e1; border-radius: 20px; outline: none; font-size: 0.88rem;">
                <button onclick="sendMessage()" title="Send Message" style="background: linear-gradient(135deg, #4f46e5, #3b82f6); color: white; border: none; width: 40px; height: 40px; border-radius: 50%; cursor: pointer; font-size: 1rem; flex-shrink: 0; display: flex; align-items: center; justify-content: center; box-shadow: 0 3px 8px rgba(79, 70, 229, 0.3);">
                    <i class="fa-solid fa-paper-plane"></i>
                </button>
            </div>
        </div>`;
        document.body.insertAdjacentHTML('beforeend', chatHtml);
    }

    restoreSavedLanguage();
    checkPendingVoiceActions();
    setupSpaNavigation();
    initWakeWordDetector();
}

// Auto-run on DOM Ready across all pages
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectVoiceAssistantBar);
} else {
    injectVoiceAssistantBar();
}


/** PAYMENT MODAL LOGIC **/
function openPayModal(type, data = {}) {
    const overlay = document.getElementById('payment-modal-overlay');
    const title = document.getElementById('modal-title');
    const phoneInput = document.getElementById('pay-phone-number');
    const amountInput = document.getElementById('pay-amount');
    
    if (type === 'phone') {
        title.innerText = 'Pay to Phone Number';
        phoneInput.placeholder = 'Enter 10-digit mobile number';
        if (data.phone) phoneInput.value = data.phone;
    }
    
    overlay.style.display = 'flex';
    phoneInput.focus();
}

function closePayModal() {
    document.getElementById('payment-modal-overlay').style.display = 'none';
    document.getElementById('pay-phone-form').reset();
}

async function executePhoneTransfer() {
    const phone = document.getElementById('pay-phone-number').value;
    const amount = document.getElementById('pay-amount').value;
    const btn = document.getElementById('confirm-payment-btn');
    
    if (!phone || !amount) {
        showToast("Please enter both phone number and amount");
        return;
    }
    
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/transfer/phone', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone_number: phone, amount: amount })
        });
        const data = await response.json();
        
        if (data.success) {
            showToast(`Sent ₹${amount} to ${data.receiver_name}`);
            closePayModal();
            loadUserSummary(); // Refresh dashboard
        } else {
            showToast(data.message);
        }
    } catch (e) {
        showToast("Network error. Try again.");
    } finally {
        btn.innerHTML = 'Confirm Payment';
        btn.disabled = false;
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    const overlays = document.querySelectorAll('.modal-overlay');
    overlays.forEach(overlay => {
        if (event.target == overlay) {
            overlay.style.display = 'none';
        }
    });
}

/** GENERIC MODAL LOGIC **/
function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.style.display = 'flex';
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.style.display = 'none';
}

/** SIDEBAR ACTION LOGIC **/
function showSidebarAction(type) {
    const defaultContent = document.getElementById('default-sidebar-content');
    const dynamicContent = document.getElementById('dynamic-action-content');
    const tools = document.querySelectorAll('.sidebar-tool');
    
    if (!defaultContent || !dynamicContent) return;
    
    // Hide default, show dynamic
    defaultContent.style.display = 'none';
    dynamicContent.style.display = 'block';
    
    // Hide all tools, show selected one
    tools.forEach(tool => tool.style.display = 'none');
    const selectedTool = document.getElementById(`sidebar-${type}`);
    if (selectedTool) selectedTool.style.display = 'block';
    
    // Scroll sidebar to top
    const rightPanel = document.getElementById('right-sidebar-panel');
    if (rightPanel) rightPanel.scrollTop = 0;

    // Ensure dynamic tool is translated
    try {
        const curLang = localStorage.getItem('siri_bank_lang') || 'Kannada';
        applyPageTranslations(curLang);
    } catch(e) {}
}

function resetSidebar() {
    const defaultContent = document.getElementById('default-sidebar-content');
    const dynamicContent = document.getElementById('dynamic-action-content');
    
    if (!defaultContent || !dynamicContent) return;
    
    defaultContent.style.display = 'block';
    dynamicContent.style.display = 'none';
}

async function executeSidebarPhoneTransfer() {
    const phone = document.getElementById('side-pay-phone').value;
    const amount = document.getElementById('side-pay-amt').value;
    const btn = document.getElementById('side-confirm-pay');
    
    if (!phone || !amount) {
        showToast("Please enter both phone number and amount");
        return;
    }
    
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/transfer/phone', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone_number: phone, amount: amount })
        });
        const data = await response.json();
        
        if (data.success) {
            showToast(`Sent ₹${amount} to ${data.receiver_name}`);
            resetSidebar();
            loadUserSummary();
        } else {
            showToast(data.message);
        }
    } catch (e) {
        showToast("Network error. Try again.");
    } finally {
        btn.innerHTML = 'Confirm Payment';
        btn.disabled = false;
    }
}

/** QUICK ACTIONS LOGIC (Updated for Sidebar) **/
async function executeAddMoney() {
    const amount = document.getElementById('side-add-amt').value;
    if (!amount) {
        showToast("Please enter an amount");
        return;
    }
    
    const btn = document.querySelector('#sidebar-add-money .btn-primary');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
    
    setTimeout(() => {
        showToast(`₹${amount} added to your account successfully!`);
        resetSidebar();
        loadUserSummary();
        btn.innerHTML = 'Add Money';
    }, 1500);
}

function processScan() {
    const btn = document.querySelector('#sidebar-scan-pay .btn-primary');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Scanning...';
    
    setTimeout(() => {
        showToast("QR Scanned: Merchant 'SIRI COFFEE'.");
        btn.innerHTML = 'Scan QR Code';
        showSidebarAction('pay-phone'); // Switch to payment tool
    }, 2000);
}

async function applyInstantLoan() {
    const amount = document.getElementById('side-loan-amt').value;
    const emp = document.getElementById('side-loan-emp').value;
    const income = document.getElementById('side-loan-income').value;
    const tenure = document.getElementById('side-loan-tenure').value;
    const btn = document.querySelector('#sidebar-instant-loan .btn-primary');
    
    if (!amount || !income) {
        showToast("Please enter all details including income");
        return;
    }
    
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Verifying Credit...';
    btn.disabled = true;

    try {
        const response = await fetch('/api/user/loan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                amount: amount, 
                purpose: `Instant Loan - ${emp} (${tenure}m) | Monthly Income: ₹${income}` 
            })
        });
        const data = await response.json();
        
        if (data.success) {
            showToast("Application Submitted for Underwriting!");
            resetSidebar();
            loadUserSummary();
        } else {
            showToast(data.message);
        }
    } catch (e) {
        showToast("Network Error. Try again.");
    } finally {
        btn.innerHTML = 'Submit Application';
        btn.disabled = false;
    }
}

async function executeSidebarBankTransfer() {
    const accEl = document.getElementById('side-bank-acc') || document.getElementById('pay-account') || document.getElementById('transfer-account-num');
    const amtEl = document.getElementById('side-bank-amt') || document.getElementById('pay-amount') || document.getElementById('transfer-amount');
    const acc = accEl ? accEl.value.trim() : '';
    const amount = amtEl ? amtEl.value.trim() : '';
    const btn = document.getElementById('side-confirm-bank');
    
    if (!acc || !amount) {
        showToast("Please enter account number and amount");
        return;
    }
    
    if (btn) {
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
        btn.disabled = true;
    }
    
    try {
        const response = await fetch('/api/transfer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ receiver_account: acc, amount: parseFloat(amount) })
        });
        const data = await response.json();
        
        if (data.success) {
            showToast(`₹${amount} transferred to ${acc} successfully!`);
            if (typeof resetSidebar === 'function') resetSidebar();
            if (typeof loadUserSummary === 'function') loadUserSummary();
            if (typeof loadTransactions === 'function') loadTransactions();
            if (typeof loadUserProfile === 'function') loadUserProfile();
        } else {
            showToast(data.message || "Transfer failed");
        }
    } catch (e) {
        showToast("Network error. Try again.");
    } finally {
        if (btn) {
            btn.innerHTML = 'Send Money';
            btn.disabled = false;
        }
    }
}

async function executeSidebarUPITransfer() {
    const upiEl = document.getElementById('side-upi-id');
    const amtEl = document.getElementById('side-upi-amt');
    const upiId = upiEl ? upiEl.value.trim() : '';
    const amount = amtEl ? amtEl.value.trim() : '';
    const btn = document.getElementById('side-confirm-upi');
    
    if (!upiId || !amount) {
        showToast("Please enter UPI ID and amount");
        return;
    }
    
    if (btn) {
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
        btn.disabled = true;
    }
    
    try {
        const response = await fetch('/api/transfer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ receiver_account: upiId, amount: parseFloat(amount) })
        });
        const data = await response.json();
        
        if (data.success) {
            showToast(`₹${amount} paid to ${upiId} successfully!`);
            if (typeof resetSidebar === 'function') resetSidebar();
            if (typeof loadUserSummary === 'function') loadUserSummary();
            if (typeof loadTransactions === 'function') loadTransactions();
            if (typeof loadUserProfile === 'function') loadUserProfile();
        } else {
            showToast(data.message || "Payment failed");
        }
    } catch (e) {
        showToast("Network error. Try again.");
    } finally {
        if (btn) {
            btn.innerHTML = 'Pay UPI ID';
            btn.disabled = false;
        }
    }
}

/** 
 * SINGLE FLOATING AI: SPA NAVIGATION ENGINE 
 * Prevents page reloads when changing tabs so the AI assistant never resets!
 **/
function setupSpaNavigation() {
    if (window._spaNavigationInitialized) return;
    window._spaNavigationInitialized = true;

    document.addEventListener('click', (e) => {
        const link = e.target.closest('.sidebar-nav a.nav-item');
        if (!link) return;

        // Skip logout button
        if (link.classList.contains('logout-btn') || link.getAttribute('onclick')?.includes('logout')) {
            return;
        }

        const href = link.getAttribute('href');
        if (!href || href === '#' || href.startsWith('javascript:')) return;

        e.preventDefault();
        navigateSpa(href, true);
    });

    window.addEventListener('popstate', (e) => {
        const targetUrl = (e.state && e.state.url) ? e.state.url : window.location.pathname;
        navigateSpa(targetUrl, false);
    });
}

async function navigateSpa(url, pushState = true) {
    try {
        const res = await fetch(url);
        if (!res.ok) {
            window.location.href = url;
            return;
        }
        const html = await res.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');

        const newMain = doc.querySelector('.main-content');
        const currentMain = document.querySelector('.main-content');

        if (newMain && currentMain) {
            currentMain.innerHTML = newMain.innerHTML;
            if (doc.title) document.title = doc.title;

            if (pushState) {
                history.pushState({ url: url }, '', url);
            }

            // Sync active sidebar state
            document.querySelectorAll('.sidebar-nav a.nav-item').forEach(item => {
                const itemHref = item.getAttribute('href');
                if (itemHref === url || (url.startsWith(itemHref) && itemHref !== '/')) {
                    item.classList.add('active');
                } else {
                    item.classList.remove('active');
                }
            });

            // Sync topbar language picker if present
            const savedLang = localStorage.getItem('siri_bank_lang') || 'Kannada';
            const topLang = document.getElementById('language-selector');
            if (topLang) topLang.value = savedLang;

            // Copy any styles from doc.head into document.head if not present
            doc.querySelectorAll('head style').forEach(newStyle => {
                document.head.appendChild(newStyle.cloneNode(true));
            });

            // Execute any inline scripts in newly swapped content (in currentMain - the LIVE DOM!)
            const scripts = currentMain.querySelectorAll('script');
            scripts.forEach(oldScript => {
                const newScript = document.createElement('script');
                Array.from(oldScript.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
                newScript.appendChild(document.createTextNode(oldScript.innerHTML));
                oldScript.parentNode.replaceChild(newScript, oldScript);
            });

            // Re-run appropriate page initializers dynamically
            if (url.includes('/home') || url === '/') {
                if (typeof loadUserSummary === 'function') loadUserSummary();
            } else if (url.includes('/pay')) {
                if (typeof loadPaySummary === 'function') loadPaySummary();
            } else if (url.includes('/atm-services')) {
                if (typeof initAtmView === 'function') initAtmView();
            } else if (url.includes('/request-history')) {
                if (typeof loadHistory === 'function') loadHistory();
                else if (typeof loadUserSummary === 'function') loadUserSummary();
            } else if (url.includes('/aadhaar-kyc')) {
                if (url.includes('retry=true') && typeof resetKycWizard === 'function') {
                    resetKycWizard();
                }
            } else if (url.includes('/profile')) {
                if (typeof loadUserProfile === 'function') loadUserProfile();
            }

            // Check if any voice filling was queued for this tab
            checkPendingVoiceActions();
        } else {
            window.location.href = url;
        }
    } catch (err) {
        console.warn("SPA Navigation fetch failed, fallback to location.href:", err);
        window.location.href = url;
    }
}

/** 
 * HANDS-FREE WAKE WORD DETECTOR 
 * Powered by unified SiriSpeechEngine for reliable hands-free interaction.
 * Wakes up on "Hey Siri", "Hey Gemini", "Namaskara" (ನಮಸ್ಕಾರ), "Siri Bank".
 **/
function initWakeWordDetector() {
    if (typeof SiriSpeechEngine !== 'undefined') {
        SiriSpeechEngine.init();
    }
}
