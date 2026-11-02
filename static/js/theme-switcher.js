document.addEventListener('DOMContentLoaded', function() {
    const themeButtons = document.querySelectorAll('.theme-btn');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value
                      || getCookie('csrftoken');

    themeButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const newTheme = this.dataset.theme;

            // 1. Update visual langsung (instant feedback)
            document.body.setAttribute('data-theme', newTheme);

            // 2. Update active state di UI
            themeButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            // 3. Simpan ke server (Server-Enforced)
            const formData = new FormData();
            formData.append('theme', newTheme);
            if (csrfToken) {
                formData.append('csrfmiddlewaretoken', csrfToken);
            }

            fetch('/theme/set/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    ...(csrfToken ? {'X-CSRFToken': csrfToken} : {})
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                if (data.status !== 'success') {
                    console.error('Gagal menyimpan tema:', data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                // Rollback visual jika gagal menyimpan ke server
                location.reload();
            });
        });
    });
});

// Helper untuk ambil CSRF token dari cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
