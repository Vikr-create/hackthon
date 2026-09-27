/**
 * Student Opportunity Discovery Platform - OpportunityHub
 * Interactive JavaScript components
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Dark Mode Toggle
  const themeToggleBtn = document.getElementById('theme-toggle-btn');
  const currentTheme = localStorage.getItem('hub-theme') || 'light';

  if (currentTheme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
    updateThemeIcon(true);
  }

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', function () {
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      if (isDark) {
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('hub-theme', 'light');
        updateThemeIcon(false);
      } else {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('hub-theme', 'dark');
        updateThemeIcon(true);
      }
    });
  }

  function updateThemeIcon(isDark) {
    if (!themeToggleBtn) return;
    const icon = themeToggleBtn.querySelector('i');
    if (icon) {
      if (isDark) {
        icon.className = 'fas fa-sun text-warning';
      } else {
        icon.className = 'fas fa-moon text-secondary';
      }
    }
  }

  // 2. AJAX Bookmark Toggle
  document.querySelectorAll('.btn-bookmark-action').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      const oppId = this.dataset.oppId;
      if (!oppId) return;

      const heartIcon = this.querySelector('i');

      fetch('/api/bookmark/toggle', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ opportunity_id: parseInt(oppId) })
      })
        .then(response => {
          if (response.status === 401) {
            window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
            return;
          }
          return response.json();
        })
        .then(data => {
          if (data && data.success) {
            if (data.bookmarked) {
              btn.classList.add('active');
              if (heartIcon) heartIcon.className = 'fas fa-bookmark text-danger';
              showToast('Saved', data.message || 'Opportunity bookmarked', 'success');
            } else {
              btn.classList.remove('active');
              if (heartIcon) heartIcon.className = 'far fa-bookmark';
              showToast('Removed', data.message || 'Removed from bookmarks', 'info');
            }

            // Update badge if exists
            const bookmarkBadge = document.getElementById('user-bookmark-count');
            if (bookmarkBadge && data.total_user_bookmarks !== undefined) {
              bookmarkBadge.textContent = data.total_user_bookmarks;
            }
          }
        })
        .catch(err => {
          console.error('Error toggling bookmark:', err);
        });
    });
  });

  // 3. Password Visibility Toggle
  document.querySelectorAll('.toggle-password-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const targetId = this.dataset.target;
      const input = document.getElementById(targetId);
      const icon = this.querySelector('i');
      if (input) {
        if (input.type === 'password') {
          input.type = 'text';
          if (icon) icon.className = 'fas fa-eye-slash';
        } else {
          input.type = 'password';
          if (icon) icon.className = 'fas fa-eye';
        }
      }
    });
  });

  // 4. Copy Opportunity Link
  document.querySelectorAll('.btn-copy-link').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const url = this.dataset.url || window.location.href;
      navigator.clipboard.writeText(url).then(() => {
        showToast('Link Copied!', 'Opportunity link copied to your clipboard.', 'success');
      }).catch(err => {
        showToast('Notice', 'Please copy URL from the address bar.', 'secondary');
      });
    });
  });

  // 5. Toast Notification Helper
  function showToast(title, message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
      document.body.appendChild(container);
    }

    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-bg-${type} border-0 show shadow-lg mb-2`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    toastEl.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">
          <strong>${title}</strong>: ${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    `;

    container.appendChild(toastEl);
    setTimeout(() => {
      toastEl.classList.remove('show');
      setTimeout(() => toastEl.remove(), 300);
    }, 3500);
  }

  // 6. Live Search Autocomplete on Navbar / Search Input
  const liveSearchInput = document.getElementById('live-search-input');
  const suggestionsBox = document.getElementById('search-suggestions-box');

  if (liveSearchInput && suggestionsBox) {
    let timeoutId;
    liveSearchInput.addEventListener('input', function () {
      clearTimeout(timeoutId);
      const query = this.value.trim();
      if (query.length < 2) {
        suggestionsBox.classList.add('d-none');
        suggestionsBox.innerHTML = '';
        return;
      }

      timeoutId = setTimeout(() => {
        fetch(`/api/search/suggestions?q=${encodeURIComponent(query)}`)
          .then(res => res.json())
          .then(data => {
            if (data && data.length > 0) {
              let html = '<div class="list-group list-group-flush shadow-lg border rounded-3 overflow-hidden">';
              data.forEach(item => {
                html += `
                  <a href="/opportunity/${item.id}" class="list-group-item list-group-item-action py-2 px-3">
                    <div class="fw-semibold text-truncate">${item.title}</div>
                    <div class="small text-muted d-flex justify-content-between">
                      <span><i class="fas fa-building me-1"></i>${item.organization}</span>
                      <span class="badge bg-light text-dark border">${item.category}</span>
                    </div>
                  </a>
                `;
              });
              html += '</div>';
              suggestionsBox.innerHTML = html;
              suggestionsBox.classList.remove('d-none');
            } else {
              suggestionsBox.classList.add('d-none');
            }
          })
          .catch(err => console.error(err));
      }, 250);
    });

    document.addEventListener('click', function (e) {
      if (!liveSearchInput.contains(e.target) && !suggestionsBox.contains(e.target)) {
        suggestionsBox.classList.add('d-none');
      }
    });
  }
});
