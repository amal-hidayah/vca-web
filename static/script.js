document.addEventListener('DOMContentLoaded', function () {

    // ── Smooth scroll navbar shadow ────────────────────────
    const navbar = document.getElementById('top-navbar');
    window.addEventListener('scroll', function () {
        if (window.scrollY > 10) {
            navbar.style.boxShadow = '0 4px 16px rgba(0,0,0,0.4)';
        } else {
            navbar.style.boxShadow = '0 2px 8px rgba(0,0,0,0.3)';
        }
    });

    // ── Best Deal button ───────────────────────────────────
    const btnDeal = document.getElementById('btn-best-deal');
    if (btnDeal) {
        btnDeal.addEventListener('click', function (e) {
            e.preventDefault();
            alert('Terima kasih! Tim kami akan segera menghubungi Anda untuk penawaran terbaik.');
        });
    }

    // ── Product card click → highlight ─────────────────────
    const cards = document.querySelectorAll('.product-card');
    cards.forEach(function (card) {
        card.style.cursor = 'pointer';
        card.addEventListener('click', function () {
            const name = this.querySelector('.product-name');
            if (name) {
                alert('Detail produk: ' + name.textContent + '\n\nHalaman detail akan segera tersedia.');
            }
        });
    });

    // ── Share buttons ──────────────────────────────────────
    const shareWa = document.getElementById('share-wa');
    if (shareWa) {
        shareWa.addEventListener('click', function (e) {
            e.preventDefault();
            const url = encodeURIComponent(window.location.href);
            const text = encodeURIComponent('Lihat katalog produk PT. Pabrik Haspel Indonesia!');
            window.open('https://wa.me/?text=' + text + '%20' + url, '_blank');
        });
    }

    // ── Btn Masuk ──────────────────────────────────────────
    const btnMasuk = document.getElementById('btn-masuk');
    if (btnMasuk) {
        btnMasuk.addEventListener('click', function (e) {
            e.preventDefault();
            alert('Fitur login akan segera tersedia.');
        });
    }

    // ── Intersection Observer for Scroll Animations ────────
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.15
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.reveal').forEach((el) => {
        observer.observe(el);
    });
});
