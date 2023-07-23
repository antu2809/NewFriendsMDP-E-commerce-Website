# utils.py

import random
import mercadopago
from django.urls import reverse
from django.shortcuts import get_object_or_404
from .models import Product, Order

def generate_reference_number():
    # Genera un número aleatorio de 8 dígitos como número de referencia
    return str(random.randint(10000000, 99999999))

def create_preference(product_id, request):
    # Configura tu clave de acceso de Mercado Pago (Reemplaza "TEST-ACCESS-TOKEN" por tu token real)
    mp = mercadopago.SDK("from settings_local import MERCADOPAGO_ACCESS_TOKEN")

    product = get_object_or_404(Product, id=product_id)

    preference_data = {
        'items': [
            {
                'title': product.name,
                'quantity': 1,
                'currency_id': 'ARS',
                'unit_price': str(product.price)
            }
        ],
        'back_urls': {
            'success': request.build_absolute_uri(reverse('payment_success')),
            'pending': request.build_absolute_uri(reverse('payment_pending')),
            'failure': request.build_absolute_uri(reverse('payment_failure'))
        }
    }
    preference = mp.create_preference(preference_data)

    return preference['response']['init_point']

def process_successful_payment(payment_id):
    # Acciones adicionales basadas en los detalles del pago exitoso.
    # Por ejemplo, actualizar el estado del pedido, enviar notificaciones, etc.

    # Obtener el pedido asociado al pago exitoso
    order = Order.objects.get(payment_id=payment_id)

    # Actualizar el estado del pedido
    order.status = 'completed'
    order.save()

def process_pending_payment(payment_id):
    # Lógica adicional para procesar el pago pendiente si es necesario

    # Obtener el pedido asociado al pago pendiente
    order = Order.objects.get(payment_id=payment_id)

    # Actualizar el estado del pedido
    order.status = 'pending'
    order.save()

def process_failed_payment(payment_id):
    # Lógica adicional para procesar el pago fallido si es necesario

    # Obtener el pedido asociado al pago fallido
    order = Order.objects.get(payment_id=payment_id)

    # Actualizar el estado del pedido
    order.status = 'failed'
    order.save()
