// Shared JS helpers
window.makeChart = (id, config) => {
  const el = document.getElementById(id);
  if (el) new Chart(el, config);
};
