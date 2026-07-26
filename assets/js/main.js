document.addEventListener('DOMContentLoaded', () => {
    // Intersection Observer for scroll animations
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('appear');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe all animated elements
    const animatedElements = document.querySelectorAll('.fade-in, .slide-up');
    animatedElements.forEach(el => observer.observe(el));

    // Staggered animation for blog cards
    const cards = document.querySelectorAll('.blog-card');
    cards.forEach((card, index) => {
        card.style.transitionDelay = `${index * 0.1}s`;
    });
    // Sidebar Toggle Logic
    const sidebarToggle = document.getElementById('sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            document.body.classList.toggle('sidebar-collapsed');
        });
    }

    // Expand / Shrink Bio Text Toggle
    const bioToggleBtn = document.getElementById('bio-toggle-btn');
    const bioExpandable = document.getElementById('bio-expandable');

    if (bioToggleBtn && bioExpandable) {
        bioToggleBtn.addEventListener('click', () => {
            const isExpanded = bioExpandable.classList.toggle('expanded');
            bioToggleBtn.classList.toggle('active', isExpanded);
            bioToggleBtn.setAttribute('aria-expanded', isExpanded);
            
            const btnText = bioToggleBtn.querySelector('.btn-text');
            if (btnText) {
                btnText.textContent = isExpanded ? 'Shrink Details' : 'Expand Details';
            }
        });
    }

    // Convert markdown mermaid blocks to div.mermaid for rendering
    const mermaidNodes = document.querySelectorAll('pre code.language-mermaid');
    mermaidNodes.forEach(node => {
        const div = document.createElement('div');
        div.className = 'mermaid';
        div.textContent = node.textContent;
        // If the code is wrapped in a pre, replace the whole pre
        if (node.parentElement.tagName === 'PRE') {
            node.parentElement.replaceWith(div);
        } else {
            node.replaceWith(div);
        }
    });
});
