// Kross 9 Gym - Admin & Automation Scripts

let currentSelectedMember = null;

// -----------------------------------------------------------------------------
// 1. Trigger Automation Audit
// -----------------------------------------------------------------------------
async function triggerAutomationAudit(targetDate = null) {
    const btn = document.getElementById('runAuditBtn') || document.getElementById('runAuditBtnTop');
    let originalHtml = '';
    if (btn) {
        originalHtml = btn.innerHTML;
        btn.innerHTML = `<span class="inline-block animate-spin mr-2">&#9696;</span> Auditing Members...`;
        btn.disabled = true;
    }

    try {
        const payload = targetDate ? { target_date: targetDate } : {};
        const res = await fetch('/api/automations/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (res.ok && data.status === 'success') {
            const count = data.messages_generated_count;
            showToast(`Automation audit completed! ${count} expiration reminder messages generated.`, 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showToast(data.error || 'Failed to complete automation scan.', 'error');
        }
    } catch (err) {
        console.error(err);
        showToast('Error executing automation scan.', 'error');
    } finally {
        if (btn) {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
        }
    }
}

// -----------------------------------------------------------------------------
// 2. Quick Message Modal Logic
// -----------------------------------------------------------------------------
function openQuickMessageModal(memberId, name, phone, plan, endDate, lockerNum, lockerEndDate) {
    currentSelectedMember = {
        id: memberId,
        name: name,
        phone: phone,
        plan: plan,
        end_date: endDate,
        locker_number: lockerNum && lockerNum !== 'None' ? lockerNum : '',
        locker_end_date: lockerEndDate && lockerEndDate !== 'None' ? lockerEndDate : ''
    };

    document.getElementById('modalMemberName').innerText = name;
    document.getElementById('modalMemberPhone').innerText = phone;
    document.getElementById('modalTemplateSelect').value = 'sub_warning_3d';

    populateModalTemplate();
    document.getElementById('quickMessageModal').classList.remove('hidden');
}

function closeQuickMessageModal() {
    document.getElementById('quickMessageModal').classList.add('hidden');
    currentSelectedMember = null;
}

function populateModalTemplate() {
    if (!currentSelectedMember) return;
    const trigger = document.getElementById('modalTemplateSelect').value;
    const textarea = document.getElementById('modalMessageText');

    const name = currentSelectedMember.name;
    const plan = currentSelectedMember.plan;
    const endDate = currentSelectedMember.end_date;
    const locker = currentSelectedMember.locker_number || 'your assigned locker';
    const lockerEnd = currentSelectedMember.locker_end_date || endDate;
    const gymPhone = "+91 74780 13363";

    let text = "";
    if (trigger === 'sub_warning_3d') {
        text = `Hi ${name}! 🏋️ Your Kross 9 Gym membership (${plan}) expires in 3 days on ${endDate}. Renew today to keep your fitness streak uninterrupted! Call ${gymPhone} or visit reception.`;
    } else if (trigger === 'sub_warning_1d') {
        text = `Reminder: Hi ${name}, tomorrow (${endDate}) is the last day of your Kross 9 Gym ${plan} plan. Don't lose your workout momentum! Renew at reception today.`;
    } else if (trigger === 'sub_expired') {
        text = `Hi ${name}, your Kross 9 Gym membership has expired today (${endDate}). We miss you on the gym floor! Re-activate your membership today at our desk: ${gymPhone}.`;
    } else if (trigger === 'locker_warning_3d') {
        text = `Notice from Kross 9 Gym: Your locker #${locker} rental ends in 3 days on ${lockerEnd}. Please renew your locker or arrange to collect your belongings.`;
    } else if (trigger === 'locker_expired') {
        text = `Alert: Locker #${locker} at Kross 9 Gym has expired today. Unrenewed lockers are scheduled for clearing. Please visit reception or call ${gymPhone}.`;
    } else if (trigger === 'welcome_member') {
        text = `Welcome to the Kross 9 Gym family, ${name}! 💥 Your ${plan} membership is active until ${endDate}. Our hours are Mon-Sat 6 AM to 10 PM at Bakultala More, Cooch Behar. Crush your goals!`;
    } else {
        text = `Hi ${name}, message from Kross 9 Gym Cooch Behar: `;
    }

    textarea.value = text;
}

async function dispatchModalMessage(channel) {
    if (!currentSelectedMember) return;
    const message = document.getElementById('modalMessageText').value.trim();
    if (!message) {
        alert('Please enter a message.');
        return;
    }

    const payload = {
        member_id: currentSelectedMember.id,
        member_name: currentSelectedMember.name,
        phone: currentSelectedMember.phone,
        channel: channel,
        trigger_type: document.getElementById('modalTemplateSelect').value,
        message: message
    };

    try {
        const res = await fetch('/api/notifications/send-custom', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (res.ok) {
            showToast(`Notification queued & logged successfully!`, 'success');
            if (channel === 'whatsapp' && data.data && data.data.whatsapp_url) {
                window.open(data.data.whatsapp_url, '_blank');
            }
            closeQuickMessageModal();
        } else {
            showToast(data.error || 'Failed to dispatch message.', 'error');
        }
    } catch (err) {
        console.error(err);
        showToast('Error communicating with server.', 'error');
    }
}

// -----------------------------------------------------------------------------
// 3. Member CRUD Handlers
// -----------------------------------------------------------------------------
function openAddMemberModal() {
    document.getElementById('addMemberModal').classList.remove('hidden');
}

function closeAddMemberModal() {
    document.getElementById('addMemberModal').classList.add('hidden');
}

async function submitNewMember(e) {
    e.preventDefault();
    const payload = {
        name: document.getElementById('addName').value.trim(),
        phone: document.getElementById('addPhone').value.trim(),
        email: document.getElementById('addEmail').value.trim(),
        plan_name: document.getElementById('addPlan').value,
        plan_amount: document.getElementById('addAmount').value,
        start_date: document.getElementById('addStartDate').value,
        end_date: document.getElementById('addEndDate').value,
        locker_number: document.getElementById('addLockerNum').value,
        locker_end_date: document.getElementById('addLockerEndDate').value,
        notes: document.getElementById('addNotes').value.trim()
    };

    try {
        const res = await fetch('/api/members', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
            showToast('Member enrolled successfully! Welcome alert logged.', 'success');
            if (data.welcome_notification && data.welcome_notification.whatsapp_url) {
                if (confirm('Member added! Would you like to send the Welcome message on WhatsApp now?')) {
                    window.open(data.welcome_notification.whatsapp_url, '_blank');
                }
            }
            setTimeout(() => window.location.reload(), 600);
        } else {
            showToast(data.error || 'Failed to add member', 'error');
        }
    } catch (err) {
        console.error(err);
        showToast('Error registering member.', 'error');
    }
}

function openEditMemberModal(member) {
    document.getElementById('editMemberId').value = member.id;
    document.getElementById('editName').value = member.name;
    document.getElementById('editPhone').value = member.phone;
    document.getElementById('editPlan').value = member.plan_name;
    document.getElementById('editStatus').value = member.status;
    document.getElementById('editStartDate').value = member.start_date;
    document.getElementById('editEndDate').value = member.end_date;
    document.getElementById('editLockerNum').value = member.locker_number || '';
    document.getElementById('editLockerEndDate').value = member.locker_end_date || '';

    document.getElementById('editMemberModal').classList.remove('hidden');
}

function closeEditMemberModal() {
    document.getElementById('editMemberModal').classList.add('hidden');
}

async function submitEditMember(e) {
    e.preventDefault();
    const id = document.getElementById('editMemberId').value;
    const payload = {
        name: document.getElementById('editName').value.trim(),
        phone: document.getElementById('editPhone').value.trim(),
        plan_name: document.getElementById('editPlan').value,
        status: document.getElementById('editStatus').value,
        start_date: document.getElementById('editStartDate').value,
        end_date: document.getElementById('editEndDate').value,
        locker_number: document.getElementById('editLockerNum').value,
        locker_end_date: document.getElementById('editLockerEndDate').value
    };

    try {
        const res = await fetch(`/api/members/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
            showToast('Member profile updated!', 'success');
            setTimeout(() => window.location.reload(), 600);
        } else {
            showToast(data.error || 'Failed to update member', 'error');
        }
    } catch (err) {
        console.error(err);
        showToast('Error updating member', 'error');
    }
}

async function deleteMember(id, name) {
    if (!confirm(`Are you sure you want to delete member ${name}? Any assigned locker will be freed.`)) {
        return;
    }

    try {
        const res = await fetch(`/api/members/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (res.ok) {
            showToast('Member deleted', 'success');
            setTimeout(() => window.location.reload(), 500);
        } else {
            showToast(data.error || 'Failed to delete member', 'error');
        }
    } catch (err) {
        console.error(err);
        showToast('Network error deleting member', 'error');
    }
}

// -----------------------------------------------------------------------------
// 4. Filtering Table
// -----------------------------------------------------------------------------
let activeStatusFilter = 'all';

function setFilterStatus(status) {
    activeStatusFilter = status;
    document.querySelectorAll('.status-tab-btn').forEach(btn => {
        if (btn.getAttribute('data-status') === status) {
            btn.className = 'status-tab-btn px-3 py-1.5 rounded-lg bg-orange-600 text-white';
        } else {
            btn.className = 'status-tab-btn px-3 py-1.5 rounded-lg bg-kross-card text-slate-300 border border-kross-border hover:bg-slate-800';
        }
    });
    filterMembersTable();
}

function filterMembersTable() {
    const input = document.getElementById('memberSearchInput');
    const term = input ? input.value.toLowerCase().trim() : '';
    const rows = document.querySelectorAll('.member-row');

    rows.forEach(row => {
        const name = row.getAttribute('data-name') || '';
        const phone = row.getAttribute('data-phone') || '';
        const status = row.getAttribute('data-status') || '';
        const locker = row.getAttribute('data-locker') || '';

        const matchesStatus = (activeStatusFilter === 'all' || status === activeStatusFilter);
        const matchesSearch = term === '' || name.includes(term) || phone.includes(term) || locker.includes(term);

        if (matchesStatus && matchesSearch) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}
