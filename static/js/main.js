/* ═══════════════════════════════════════════════════════════════════
   GARAGE SERVICE — JAVASCRIPT
   Hero Carousel, Star Rating, Newsletter AJAX, Scroll Animations
   ═══════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    initHeroCarousel();
    initStarRating();
    initNewsletterForm();
    initScrollAnimations();
    initMobileNav();
    initFlashMessages();
    initModals();
    updateLiveDate();
});


/* ── Hero Carousel ─────────────────────────────────────────────────── */
function initHeroCarousel() {
    const slides = document.querySelectorAll('.hero-slide');
    const dots = document.querySelectorAll('.hero-dot');
    const prevBtn = document.querySelector('.hero-prev');
    const nextBtn = document.querySelector('.hero-next');
    const progressBar = document.querySelector('.hero-progress');

    if (slides.length === 0) return;

    let currentSlide = 0;
    let autoPlayInterval;

    function goToSlide(index) {
        slides.forEach(s => s.classList.remove('active'));
        dots.forEach(d => d.classList.remove('active'));

        currentSlide = (index + slides.length) % slides.length;
        slides[currentSlide].classList.add('active');
        if (dots[currentSlide]) dots[currentSlide].classList.add('active');

        // Reset and restart progress bar animation
        if (progressBar) {
            progressBar.classList.remove('active');
            void progressBar.offsetWidth; // Force DOM reflow to restart CSS animation
            progressBar.classList.add('active');
        }
    }

    function nextSlide() {
        goToSlide(currentSlide + 1);
    }

    function prevSlide() {
        goToSlide(currentSlide - 1);
    }

    function startAutoPlay() {
        autoPlayInterval = setInterval(nextSlide, 5000);
    }

    function stopAutoPlay() {
        clearInterval(autoPlayInterval);
    }

    // Controls
    if (nextBtn) nextBtn.addEventListener('click', () => { stopAutoPlay(); nextSlide(); startAutoPlay(); });
    if (prevBtn) prevBtn.addEventListener('click', () => { stopAutoPlay(); prevSlide(); startAutoPlay(); });

    dots.forEach((dot, i) => {
        dot.addEventListener('click', () => {
            stopAutoPlay();
            goToSlide(i);
            startAutoPlay();
        });
    });

    // Start
    goToSlide(0);
    startAutoPlay();
}


/* ── Star Rating Widget ────────────────────────────────────────────── */
function initStarRating() {
    const starContainers = document.querySelectorAll('.star-rating');

    starContainers.forEach(container => {
        const stars = container.querySelectorAll('.star');
        const hiddenInput = container.parentElement.querySelector('input[name="rating"]');

        stars.forEach((star, index) => {
            star.addEventListener('click', () => {
                const rating = index + 1;
                if (hiddenInput) hiddenInput.value = rating;

                stars.forEach((s, i) => {
                    s.classList.toggle('active', i < rating);
                    s.textContent = i < rating ? '★' : '☆';
                });
            });

            star.addEventListener('mouseenter', () => {
                stars.forEach((s, i) => {
                    s.style.color = i <= index ? '#f4b400' : '';
                });
            });

            star.addEventListener('mouseleave', () => {
                stars.forEach((s, i) => {
                    if (!s.classList.contains('active')) {
                        s.style.color = '';
                    }
                });
            });
        });
    });
}


/* ── Newsletter AJAX ───────────────────────────────────────────────── */
function initNewsletterForm() {
    const form = document.getElementById('newsletter-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;

        submitBtn.textContent = 'SUBSCRIBING...';
        submitBtn.disabled = true;

        try {
            const response = await fetch('/newsletter', {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                body: formData
            });

            const data = await response.json();

            showFlash(data.message, data.status);
            if (data.status === 'success') {
                form.reset();
            }
        } catch (err) {
            showFlash('Something went wrong. Please try again.', 'danger');
        } finally {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    });
}


/* ── Scroll Animations ─────────────────────────────────────────────── */
function initScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    document.querySelectorAll('.fade-up').forEach(el => observer.observe(el));

    // Animate counters
    const counters = document.querySelectorAll('.metric-value[data-count]');
    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                counterObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(counter => counterObserver.observe(counter));
}

function animateCounter(el) {
    const target = parseInt(el.dataset.count, 10);
    const suffix = el.dataset.suffix || '';
    const duration = 2000;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Ease out
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(eased * target);

        el.textContent = current.toLocaleString() + suffix;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}


/* ── Mobile Nav ────────────────────────────────────────────────────── */
function initMobileNav() {
    const hamburger = document.querySelector('.hamburger');
    const mobileNav = document.querySelector('.mobile-nav');

    if (!hamburger || !mobileNav) return;

    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        mobileNav.classList.toggle('active');
        document.body.style.overflow = mobileNav.classList.contains('active') ? 'hidden' : '';
    });

    // Close on link click
    mobileNav.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            hamburger.classList.remove('active');
            mobileNav.classList.remove('active');
            document.body.style.overflow = '';
        });
    });
}


/* ── Flash Messages ────────────────────────────────────────────────── */
function initFlashMessages() {
    document.querySelectorAll('.flash-close').forEach(btn => {
        btn.addEventListener('click', () => {
            const flash = btn.closest('.flash');
            flash.style.opacity = '0';
            flash.style.transform = 'translateX(20px)';
            setTimeout(() => flash.remove(), 300);
        });
    });

    // Auto-dismiss after 5s
    document.querySelectorAll('.flash').forEach(flash => {
        setTimeout(() => {
            if (flash.parentElement) {
                flash.style.opacity = '0';
                flash.style.transform = 'translateX(20px)';
                setTimeout(() => flash.remove(), 300);
            }
        }, 5000);
    });
}

function showFlash(message, type = 'info') {
    let container = document.querySelector('.flash-messages');
    if (!container) {
        container = document.createElement('div');
        container.className = 'flash-messages';
        document.body.appendChild(container);
    }

    const flash = document.createElement('div');
    flash.className = `flash flash-${type}`;
    flash.innerHTML = `
        <span>${message}</span>
        <button class="flash-close" onclick="this.closest('.flash').remove()">×</button>
    `;

    container.appendChild(flash);

    setTimeout(() => {
        if (flash.parentElement) {
            flash.style.opacity = '0';
            flash.style.transform = 'translateX(20px)';
            setTimeout(() => flash.remove(), 300);
        }
    }, 5000);
}


/* ── Modals ────────────────────────────────────────────────────────── */
function initModals() {
    // Open modal
    document.querySelectorAll('[data-modal]').forEach(trigger => {
        trigger.addEventListener('click', () => {
            const modal = document.getElementById(trigger.dataset.modal);
            if (modal) modal.classList.add('active');
        });
    });

    // Close modal
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', () => {
            btn.closest('.modal-overlay').classList.remove('active');
        });
    });

    // Close on overlay click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.classList.remove('active');
        });
    });
}


/* ── Live Date ─────────────────────────────────────────────────────── */
function updateLiveDate() {
    const dateEl = document.getElementById('live-date');
    if (!dateEl) return;

    function update() {
        const now = new Date();
        const options = {
            weekday: 'short',
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        };
        dateEl.textContent = now.toLocaleDateString('en-US', options);
    }

    update();
    // Update every minute
    setInterval(update, 60000);
}


/* ── Date Availability Check ───────────────────────────────────────── */
async function checkDateAvailability(dateInput) {
    if (!dateInput || !dateInput.value) return;

    const dateStr = dateInput.value;
    const statusEl = document.getElementById('date-availability');
    if (!statusEl) return;

    try {
        const response = await fetch(`/api/date-availability/${dateStr}`);
        const data = await response.json();

        if (data.available) {
            statusEl.innerHTML = `<span class="text-success">✓ ${data.slots_left} slot${data.slots_left !== 1 ? 's' : ''} available</span>`;
        } else {
            statusEl.innerHTML = `<span class="text-danger">✗ Fully booked — please choose another date</span>`;
        }
    } catch {
        statusEl.textContent = '';
    }
}
