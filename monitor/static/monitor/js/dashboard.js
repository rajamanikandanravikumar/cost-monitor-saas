// monitor/static/monitor/js/dashboard.js

document.addEventListener("DOMContentLoaded", function () {
  initUserMenu();
  initCharts();
});

function initUserMenu() {
  const trigger = document.getElementById("userMenuTrigger");
  const menu = document.getElementById("userMenuDropdown");
  if (!trigger || !menu) return;

  const wrapper = trigger.closest(".user-menu");

  trigger.addEventListener("click", function (e) {
    e.stopPropagation();
    wrapper.classList.toggle("open");
  });

  // Close when clicking anywhere outside the menu
  document.addEventListener("click", function (e) {
    if (!wrapper.contains(e.target)) {
      wrapper.classList.remove("open");
    }
  });

  // Close on Escape key
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      wrapper.classList.remove("open");
    }
  });
}

function initCharts() {
  // serviceLabels/serviceData/dailyLabels/dailyData are defined in the
  // inline <script> block in dashboard.html, rendered server-side from
  // Django template context before this file loads.
  const fontFamily = "'Inter', sans-serif";
  Chart.defaults.color = '#6b7797';
  Chart.defaults.font.family = fontFamily;
  Chart.defaults.borderColor = '#1e2740';

  const serviceCanvas = document.getElementById('serviceChart');
  if (serviceCanvas && typeof serviceLabels !== 'undefined' && serviceLabels.length) {
    new Chart(serviceCanvas, {
      type: 'doughnut',
      data: {
        labels: serviceLabels,
        datasets: [{
          data: serviceData,
          backgroundColor: ['#35d0e0', '#f5a623', '#7c8aff', '#4ade80', '#ff6b5c'],
          borderColor: '#10162a',
          borderWidth: 3
        }]
      },
      options: {
        plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, padding: 14 } } }
      }
    });
  }

  const trendCanvas = document.getElementById('trendChart');
  if (trendCanvas && typeof dailyLabels !== 'undefined' && dailyLabels.length) {
    new Chart(trendCanvas, {
      type: 'line',
      data: {
        labels: dailyLabels,
        datasets: [{
          label: 'Total daily cost ($)',
          data: dailyData,
          borderColor: '#35d0e0',
          backgroundColor: 'rgba(53, 208, 224, 0.08)',
          fill: true,
          tension: 0.35,
          pointRadius: 0,
          borderWidth: 2
        }]
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: '#1e2740' } }
        }
      }
    });
  }
}