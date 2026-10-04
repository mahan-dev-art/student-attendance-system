document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.delete-form').forEach(form => {
    form.addEventListener('submit', event => {
      if (!window.confirm('Delete this record? This action cannot be undone.')) event.preventDefault();
    });
  });
  document.querySelectorAll('.flash').forEach(el => setTimeout(() => el.remove(), 4500));
});
