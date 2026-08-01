document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebarToggle');
    if (toggle && sidebar) {
        toggle.addEventListener('click', () => sidebar.classList.toggle('show'));
    }

    document.querySelectorAll('[data-toggle="answer"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const answer = this.nextElementSibling;
            if (answer) {
                answer.style.display = answer.style.display === 'none' ? 'block' : 'none';
                this.textContent = answer.style.display === 'none' ? 'Show Answer' : 'Hide Answer';
            }
        });
    });

    document.querySelectorAll('.flashcard').forEach(card => {
        card.addEventListener('click', function() {
            this.classList.toggle('flipped');
        });
    });

    document.querySelectorAll('[data-print]').forEach(btn => {
        btn.addEventListener('click', () => window.print());
    });
});
