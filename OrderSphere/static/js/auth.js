(function () {
  // ─────────────────────────────────────────────────────────
  // Password Visibility Toggle
  // ─────────────────────────────────────────────────────────
  document.querySelectorAll('.password-toggle').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const input = document.getElementById(btn.dataset.target);
      const showing = input.type === 'text';
      
      input.type = showing ? 'password' : 'text';
      btn.textContent = showing ? '👁️ Show' : '🙈 Hide';
      btn.style.transition = 'all 0.2s ease';
    });
  });

  // ─────────────────────────────────────────────────────────
  // Password Strength Meter
  // ─────────────────────────────────────────────────────────
  const strengthInput = document.querySelector('[data-strength]');
  const meter = document.querySelector('.strength-meter');
  
  if (strengthInput && meter) {
    function updateStrength() {
      const value = strengthInput.value;
      let score = 0;
      
      // Length check (8+ characters)
      if (value.length >= 8) score += 1;
      
      // Case check (uppercase + lowercase)
      if (/[A-Z]/.test(value) && /[a-z]/.test(value)) score += 1;
      
      // Digit check
      if (/\d/.test(value)) score += 1;
      
      meter.dataset.score = String(score);
      
      // Update label
      const label = meter.parentElement.querySelector('.strength-label');
      if (label) {
        const labels = ['Weak', 'Fair', 'Good', 'Strong'];
        label.textContent = score > 0 ? labels[score - 1] : '';
      }
    }
    
    strengthInput.addEventListener('input', updateStrength);
    strengthInput.addEventListener('focus', updateStrength);
  }

  // ─────────────────────────────────────────────────────────
  // Form Submission Feedback
  // ─────────────────────────────────────────────────────────
  const authForms = document.querySelectorAll('form');
  authForms.forEach((form) => {
    form.addEventListener('submit', function() {
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = '⏳ Processing...';
      }
    });
  });
})();

