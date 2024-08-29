document.addEventListener('DOMContentLoaded', function() {
    // Obtener la fecha actual en formato YYYY-MM-DD
    const today = new Date().toISOString().split('T')[0];
    // Establecer la fecha mínima del input
    document.getElementById('entrada').setAttribute('min', today);
    document.getElementById('salida').setAttribute('min', today);

    // Manejar el scroll para ocultar el header y fijar la barra de búsqueda
    window.addEventListener('scroll', function() {
        const header = document.querySelector('.header');
        const searchBar = document.querySelector('.search-bar');
        
        if (window.scrollY > 60) {
            header.classList.add('hidden');
        }
        else 
        {
            header.classList.remove('hidden');
        }

        if (window.scrollY > 240){
            searchBar.classList.add('fixed');
        }
        else 
        {
            searchBar.classList.remove('fixed');
        }
    });

    document.querySelectorAll('.book-now').forEach(button => {
        button.addEventListener('click', function(event) {
            // Prevenir el comportamiento por defecto del clic
            event.preventDefault();

            const result = this.closest('.result');
            const optionsContainer = result.querySelector('.options-container');

            // Si hay un contenedor de opciones activo y no es el actual, ciérralo
            document.querySelectorAll('.options-container.active').forEach(container => {
                if (container !== optionsContainer) {
                    container.classList.remove('active');
                    container.closest('.result').classList.remove('expanded');
                }
            });

            // Alternar el contenedor de opciones actual
            if (optionsContainer.classList.contains('active')) {
                optionsContainer.classList.remove('active');
                result.classList.remove('expanded');
            } else {
                optionsContainer.classList.add('active');
                result.classList.add('expanded');

                // Ajusta el desplazamiento solo si es necesario
                setTimeout(() => {
                    window.scrollBy({
                        top: optionsContainer.offsetHeight + 20, // Añadir un pequeño margen para evitar el salto
                        behavior: 'smooth'
                    });
                }, 300); // Asegúrate de que el retraso coincide con la duración de la transición
            }
        });
    });
    // Lista de URLs de imágenes para el fondo
    const images = [
        './images/alexis-amz-da-cruz-LjC1vn_AonE-unsplash.jpg',
        './images/john-matychuk-yvfp5YHWGsc-unsplash.jpg', // Cambia estos URLs a las rutas correctas de tus imágenes
        './images/raynaldy-dachlan-dpsOTmcfLig-unsplash.jpg'
    ];

    

    let currentImageIndex = 0;

    function changeBackgroundImage() {
        const header = document.querySelector('.header');

        // Añade la clase para iniciar la transición
        header.classList.add('slide-left');

        currentImageIndex = (currentImageIndex + 1) % images.length;
        document.querySelector('.header').style.backgroundImage = `url('${images[currentImageIndex]}')`;
    }

    // Cambia la imagen de fondo cada 10 segundos (10000 ms)
    setInterval(changeBackgroundImage, 20000);





    const modal = document.getElementById('reservation-modal');
    const closeButton = document.querySelector('.close-button');
    const reservationForm = document.getElementById('reservation-form');
    
    // Agregar event listener a los botones de los distintos planes
    document.querySelectorAll('.option button').forEach(button => {
        button.addEventListener('click', function() {
            const option = button.closest('.option');
            const price = option.querySelector('.price').textContent;
            const location = "Retiro Park Garage"; // Puedes ajustar esto según sea necesario
            const dates = "01/01/2023 - 01/02/2023"; // Puedes ajustar esto según sea necesario

            modal.style.display = 'block';

            // Rellenar los campos del formulario con los datos
            reservationForm.querySelector('#location').value = location;
            reservationForm.querySelector('#dates').value = dates;
            reservationForm.querySelector('#price').value = price;
        });
    });

    // Cerrar el modal al hacer clic en la 'X'
    closeButton.addEventListener('click', function() {
        modal.style.display = 'none';
    });

    // Cerrar el modal al hacer clic fuera de la ventana modal
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });

    // Manejar el envío del formulario (puedes ajustar esto según tus necesidades)
    reservationForm.addEventListener('submit', function(event) {
        event.preventDefault();
        alert('Reservation submitted!');
        modal.style.display = 'none';
    });
});