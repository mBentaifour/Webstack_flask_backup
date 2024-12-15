let currentSlide = 1;
const totalSlides = document.querySelectorAll('.slide').length;

// Afficher le premier slide au chargement
document.addEventListener('DOMContentLoaded', () => {
    document.querySelector(`#slide${currentSlide}`).classList.add('active');
});

// Navigation entre les slides
function showSlide(n) {
    // Masquer le slide actuel
    document.querySelector(`#slide${currentSlide}`).classList.remove('active');
    
    // Mettre à jour l'index du slide
    currentSlide = n;
    
    // Gérer la boucle des slides
    if (currentSlide > totalSlides) currentSlide = 1;
    if (currentSlide < 1) currentSlide = totalSlides;
    
    // Afficher le nouveau slide
    document.querySelector(`#slide${currentSlide}`).classList.add('active');
}

function nextSlide() {
    showSlide(currentSlide + 1);
}

function prevSlide() {
    showSlide(currentSlide - 1);
}

// Navigation avec les flèches du clavier
document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight') nextSlide();
    if (e.key === 'ArrowLeft') prevSlide();
});
