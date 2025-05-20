// Main JavaScript File

// Document Ready Function
$(document).ready(function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        $('.alert').alert('close');
    }, 5000);

    // Confirm Delete
    $('.delete-confirm').on('click', function(e) {
        if (!confirm('هل أنت متأكد من رغبتك في الحذف؟')) {
            e.preventDefault();
        }
    });

    // Date picker initialization for date inputs
    if ($('.datepicker').length) {
        $('.datepicker').attr('type', 'date');
    }

    // Print button functionality
    $('.btn-print').on('click', function() {
        window.print();
    });

    // Filter toggle
    $('#filter-toggle').on('click', function() {
        $('#filter-form').toggleClass('d-none');
    });

    // Initialize AdminLTE card widget
    $('.card-tools [data-card-widget="collapse"]').on('click', function() {
        var $card = $(this).closest('.card');
        $card.find('.card-body').slideToggle();
        $(this).find('i').toggleClass('fa-minus fa-plus');
    });

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Calculate total amount in sales forms
    $('#id_quantity, #id_price_per_unit').on('input', function() {
        calculateTotal();
    });

    function calculateTotal() {
        const quantity = parseFloat($('#id_quantity').val()) || 0;
        const price = parseFloat($('#id_price_per_unit').val()) || 0;
        const total = quantity * price;
        $('#total-amount').text(total.toFixed(2));
    }

    // Initialize any calculations on page load
    calculateTotal();
});
