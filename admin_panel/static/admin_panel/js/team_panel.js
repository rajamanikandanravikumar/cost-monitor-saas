// admin_panel/static/admin_panel/js/team_panel.js

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".toggle-remark-form").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const targetId = btn.getAttribute("data-target");
      const form = document.getElementById(targetId);
      if (!form) return;

      const isOpen = form.classList.contains("open");
      form.classList.toggle("open");
      btn.textContent = isOpen ? "+ Add remark" : "− Cancel";

      if (!isOpen) {
        form.querySelector("textarea").focus();
      }
    });
  });
});