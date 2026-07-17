// accounts/static/accounts/js/auth.js
// Client-side password confirmation check and show/hide toggle.
// Note: this is a UX convenience only — the real validation happens
// server-side in accounts/forms.py, since client-side checks can always
// be bypassed.

document.addEventListener("DOMContentLoaded", function () {
  const form = document.querySelector("form");
  if (!form) return;

  const passwordField = form.querySelector('input[name="password"]');
  const confirmField = form.querySelector('input[name="confirm_password"]');
  const submitBtn = form.querySelector('button[type="submit"]');

  // Add show/hide toggle to every password field on the page
  form.querySelectorAll('input[type="password"]').forEach(function (input) {
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

  // Live password-match check, only relevant on the register page
  if (passwordField && confirmField) {
    let mismatchNotice = document.createElement("div");
    mismatchNotice.className = "error-text";
    mismatchNotice.style.display = "none";
    mismatchNotice.textContent = "Passwords do not match.";
    confirmField.closest(".field-wrap").after(mismatchNotice);

    function checkMatch() {
      const bothFilled = passwordField.value && confirmField.value;
      const mismatch = bothFilled && passwordField.value !== confirmField.value;
      mismatchNotice.style.display = mismatch ? "block" : "none";
      if (submitBtn) submitBtn.disabled = Boolean(mismatch);
    }

    passwordField.addEventListener("input", checkMatch);
    confirmField.addEventListener("input", checkMatch);
  }
});