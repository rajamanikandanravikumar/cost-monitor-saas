// accounts/static/accounts/js/auth.js

document.addEventListener("DOMContentLoaded", function () {

  // ==========================================
  // 1. INDEPENDENT OTP COUNTDOWN TIMER
  // ==========================================
  const timerDisplay = document.getElementById("otp-timer");

  if (timerDisplay) {
    const otpInput = document.querySelector('input[name="code"], input[name="otp"]');
    const submitBtn = document.querySelector('button[type="submit"]');
    const resendBox = document.getElementById("resend-container");

    // Read seconds from data-seconds attribute
    let secondsAttr = timerDisplay.getAttribute("data-seconds");
    let timeLeft = parseInt(secondsAttr, 10);

    // Fallback if NaN or empty
    if (isNaN(timeLeft) || timeLeft <= 0) {
      timeLeft = 120;
    }

    function updateTimerUI() {
      if (timeLeft <= 0) {
        timerDisplay.textContent = "00:00 (Expired)";
        timerDisplay.style.color = "var(--danger, #ff6b5c)";

        if (otpInput) otpInput.disabled = true;
        if (submitBtn) submitBtn.disabled = true;
        if (resendBox) resendBox.style.display = "block";
        return true;
      }

      let m = Math.floor(timeLeft / 60);
      let s = timeLeft % 60;

      m = m < 10 ? "0" + m : m;
      s = s < 10 ? "0" + s : s;

      timerDisplay.textContent = `${m}:${s}`;
      return false;
    }

    // Run first frame immediately
    let expired = updateTimerUI();

    // Start interval loop
    if (!expired) {
      const timerInterval = setInterval(function () {
        timeLeft--;
        if (updateTimerUI()) {
          clearInterval(timerInterval);
        }
      }, 1000);
    }
  }

  // ==========================================
  // 2. PASSWORD TOGGLE & MATCH CHECK (SAFE)
  // ==========================================
  const form = document.querySelector("form");
  if (!form) return;

  const passwordFields = form.querySelectorAll('input[type="password"]');
  if (passwordFields.length > 0) {
    passwordFields.forEach(function (input) {
      if (input.parentNode.classList.contains("field-wrap")) return;

      const wrapper = document.createElement("div");
      wrapper.className = "field-wrap";
      input.parentNode.insertBefore(wrapper, input);
      wrapper.appendChild(input);

      const toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = "toggle-visibility";
      toggle.textContent = "Show";
      toggle.addEventListener("click", function () {
        const isHidden = input.type === "password";
        input.type = isHidden ? "text" : "password";
        toggle.textContent = isHidden ? "Hide" : "Show";
      });
      wrapper.appendChild(toggle);
    });

    const passwordField = form.querySelector('input[name="password"]');
    const confirmField = form.querySelector('input[name="confirm_password"]');
    const submitBtn = form.querySelector('button[type="submit"]');

    if (passwordField && confirmField) {
      let mismatchNotice = document.createElement("div");
      mismatchNotice.className = "error-text";
      mismatchNotice.style.display = "none";
      mismatchNotice.textContent = "Passwords do not match.";

      const parentWrap = confirmField.closest(".field-wrap") || confirmField;
      parentWrap.after(mismatchNotice);

      function checkMatch() {
        const bothFilled = passwordField.value && confirmField.value;
        const mismatch = bothFilled && passwordField.value !== confirmField.value;
        mismatchNotice.style.display = mismatch ? "block" : "none";
        if (submitBtn) submitBtn.disabled = Boolean(mismatch);
      }

      passwordField.addEventListener("input", checkMatch);
      confirmField.addEventListener("input", checkMatch);
    }
  }
});