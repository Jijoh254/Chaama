/**
 * ChamaYetu - Main JavaScript File
 * 
 * Handles:
 * - Sidebar toggle
 * - Toast notifications
 * - STK Push status polling
 * - Form validation
 * - Notification badge updates
 */

// ============================================
// Sidebar Toggle Functionality
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    // Menu toggle button
    const menuToggle = document.getElementById('menu-toggle');
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            document.getElementById('wrapper').classList.toggle('toggled');
        });
    }
    
    // Update notification badge on page load
    updateNotificationBadge();
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});

// ============================================
// Toast Notification Helper
// ============================================
function showToast(title, message, type = 'info') {
    const toastEl = document.getElementById('liveToast');
    if (!toastEl) return;
    
    const toastTitle = document.getElementById('toast-title');
    const toastMessage = document.getElementById('toast-message');
    
    if (toastTitle) toastTitle.textContent = title;
    if (toastMessage) toastMessage.textContent = message;
    
    // Set toast color based on type
    const toastHeader = toastEl.querySelector('.toast-header');
    if (toastHeader) {
        toastHeader.classList.remove('bg-success', 'bg-danger', 'bg-warning', 'bg-info');
        if (type === 'success') {
            toastHeader.classList.add('bg-success', 'text-white');
        } else if (type === 'error') {
            toastHeader.classList.add('bg-danger', 'text-white');
        } else if (type === 'warning') {
            toastHeader.classList.add('bg-warning', 'text-dark');
        } else if (type === 'info') {
            toastHeader.classList.add('bg-info', 'text-white');
        }
    }
    
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}

// ============================================
// Notification Badge Update
// ============================================
function updateNotificationBadge() {
    fetch('/api/notifications/unread-count')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('notification-badge');
            if (badge) {
                if (data.count > 0) {
                    badge.textContent = data.count;
                    badge.classList.remove('d-none');
                } else {
                    badge.classList.add('d-none');
                }
            }
        })
        .catch(err => console.error('Error updating notification badge:', err));
}

// ============================================
// STK Push Status Polling
// ============================================
function pollContributionStatus(contributionId, callback) {
    let pollCount = 0;
    const maxPolls = 60; // Max 5 minutes (60 * 5 seconds)
    
    const pollInterval = setInterval(function() {
        if (pollCount >= maxPolls) {
            clearInterval(pollInterval);
            if (callback) callback('timeout', null);
            return;
        }
        
        fetch(`/api/contributions/${contributionId}/status`)
            .then(response => response.json())
            .then(data => {
                pollCount++;
                
                if (data.status === 'confirmed') {
                    clearInterval(pollInterval);
                    if (callback) callback('success', data);
                } else if (data.status === 'failed') {
                    clearInterval(pollInterval);
                    if (callback) callback('failed', data);
                } else {
                    // Still pending, continue polling
                    if (callback) callback('pending', data);
                }
            })
            .catch(err => {
                console.error('Error polling contribution status:', err);
                pollCount++;
            });
    }, 5000); // Poll every 5 seconds
    
    return pollInterval;
}

// ============================================
// Format Currency (Kenyan Shillings)
// ============================================
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-KE', {
        style: 'currency',
        currency: 'KES',
        minimumFractionDigits: 2
    }).format(amount);
}

// ============================================
// Format Date
// ============================================
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString('en-KE', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// ============================================
// Phone Number Formatting (Kenya)
// ============================================
function formatPhoneNumber(phoneNumber) {
    if (!phoneNumber) return '';
    
    // Remove all non-digits
    const cleaned = phoneNumber.replace(/\D/g, '');
    
    // Handle different formats
    if (cleaned.length === 10 && cleaned.startsWith('0')) {
        // Format: 07XX XXX XXX
        return cleaned.replace(/(\d{4})(\d{3})(\d{3})/, '$1 $2 $3');
    } else if (cleaned.length === 12 && cleaned.startsWith('254')) {
        // Format: +254 7XX XXX XXX
        return '+254 ' + cleaned.substring(3).replace(/(\d{3})(\d{3})(\d{3})/, '$1 $2 $3');
    }
    
    return phoneNumber;
}

// ============================================
// Validate Kenyan Phone Number
// ============================================
function validateKenyanPhone(phoneNumber) {
    const cleaned = phoneNumber.replace(/\D/g, '');
    
    // Check for valid Kenyan phone formats
    const patterns = [
        /^07\d{8}$/,      // 07XXXXXXXX
        /^01\d{8}$/,      // 01XXXXXXXX
        /^2547\d{8}$/,    // 2547XXXXXXXX
        /^2541\d{8}$/     // 2541XXXXXXXX
    ];
    
    return patterns.some(pattern => pattern.test(cleaned));
}

// ============================================
// Copy to Clipboard
// ============================================
function copyToClipboard(text, successMessage = 'Copied to clipboard!') {
    navigator.clipboard.writeText(text).then(function() {
        showToast('Success', successMessage, 'success');
    }).catch(function(err) {
        console.error('Failed to copy:', err);
        showToast('Error', 'Failed to copy to clipboard', 'error');
    });
}

// ============================================
// Confirm Action Dialog
// ============================================
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// ============================================
// Loading State for Buttons
// ============================================
function setButtonLoading(button, isLoading, loadingText = 'Loading...') {
    if (!button) return;
    
    if (isLoading) {
        button.disabled = true;
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>${loadingText}`;
    } else {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText || 'Submit';
    }
}

// ============================================
// Modal Helpers
// ============================================
function openModal(modalId) {
    const modalEl = document.getElementById(modalId);
    if (modalEl) {
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }
}

function closeModal(modalId) {
    const modalEl = document.getElementById(modalId);
    if (modalEl) {
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) {
            modal.hide();
        }
    }
}

// ============================================
// API Request Helper with Error Handling
// ============================================
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Request failed:', error);
        showToast('Error', error.message, 'error');
        throw error;
    }
}

// ============================================
// Group Invite Code Generator (Client-side preview)
// ============================================
function generateInviteCodePreview(length = 8) {
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * characters.length));
    }
    return result;
}

// ============================================
// Initialize Tooltips and Popovers
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// ============================================
// Auto-submit Forms on Change (Optional)
// ============================================
function autoSubmitFormOnChange(selector) {
    const elements = document.querySelectorAll(selector);
    elements.forEach(function(element) {
        element.addEventListener('change', function() {
            this.closest('form').submit();
        });
    });
}

// ============================================
// Export for use in other scripts
// ============================================
window.ChamaYetu = {
    showToast,
    updateNotificationBadge,
    pollContributionStatus,
    formatCurrency,
    formatDate,
    formatPhoneNumber,
    validateKenyanPhone,
    copyToClipboard,
    confirmAction,
    setButtonLoading,
    openModal,
    closeModal,
    apiRequest,
    generateInviteCodePreview,
    autoSubmitFormOnChange
};
