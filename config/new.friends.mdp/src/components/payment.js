function processPayment(paymentMethodId) {
    // Realizar cualquier lógica adicional antes de redirigir al cliente
    // Por ejemplo, almacenar el método de pago seleccionado en un campo oculto del formulario

    // Redirige al cliente hacia la vista payment_view con el método de pago seleccionado
    window.location.href = "{% url 'payment_view' product_id %}?payment_method=" + paymentMethodId;
}
