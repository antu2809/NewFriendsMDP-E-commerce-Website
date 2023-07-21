from django.shortcuts import get_object_or_404, render
from .models import Product, PaymentMethod, CreditCard, Bank, Order
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from .forms import ProductForm, PaymentForm
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from django_otp import match_token
from django_otp.decorators import otp_required
from django.urls import reverse
from django.http import request
import mercadopago
from mercadopago.resources import PaymentMethods
import random


def base_view(request):
    products = Product.objects.all()
    
    # Obtener los bancos y los métodos de pago desde la base de datos
    banks = Bank.objects.all()
    payment_methods = PaymentMethod.objects.all()
    
    context = {
        'title': 'New Friends MDP',
        'navbar_links': [
            {'url': '/', 'label': 'Inicio'},
            {'url': '/productos/', 'label': 'Productos'},
            {'url': '/contacto/', 'label': 'Contacto'}
        ],
        'footer_content': 'Contenido del pie de página',
        'products': products,
    }
    return render(request, 'base.html', context)

def product_list(request):
    products = Product.objects.all()
    payment_form = PaymentForm()  # Formulario para capturar información de pago
    return render(request, 'product_list.html', {'products': products, 'payment_form': payment_form})

@login_required
def admin_product_list(request):
    if not request.user.is_superuser:
        return redirect('product_list')
    
    products = Product.objects.all()
    return render(request, 'admin_product_list.html', {'products': products})

@login_required  # Se requiere que el usuario esté autenticado como administrador
def low_stock_notification(request):
    low_stock_products = Product.objects.filter(stock__lt=10)  # Filtra los productos con stock inferior a 10
    # Lógica para enviar notificaciones a los administradores sobre los productos bajos en stock
    return render(request, 'low_stock_notification.html', {'products': low_stock_products})

def add_product(request):
    if not request.user.is_superuser:
        return redirect('product_list')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('admin_product_list')
    else:
        form = ProductForm()

    payment_form = PaymentForm()  # Formulario para capturar información de pago
    return render(request, 'add_product.html', {'form': form, 'payment_form': payment_form})

def update_product(request, product_id):
    if not request.user.is_superuser:
        return redirect('product_list')

    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('admin_product_list')
    else:
        form = ProductForm(instance=product)

    return render(request, 'update_product.html', {'form': form})

def delete_product(request, product_id):
    if not request.user.is_superuser:
        return redirect('product_list')

    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        product.delete()
        return redirect('admin_product_list')

    return render(request, 'delete_product.html', {'product': product})

# Otras vistas y lógica necesaria para la gestión de inventario


# Gestión de usuarios

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

@login_required
def login(request):
    return LoginView.as_view(template_name='login.html')(request)

@login_required
def profile(request):
    user = request.user
    orders = user.order_set.all()
    return render(request, 'profile.html', {'user': user, 'orders': orders})

@login_required
def update_profile(request):
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserChangeForm(instance=request.user)
    
    return render(request, 'update_profile.html', {'form': form})

@login_required
def purchase_history(request):
    user = request.user
    orders = user.order_set.all()
    return render(request, 'purchase_history.html', {'orders': orders})

# Otras vistas y lógica necesaria para la gestión de usuarios

# Vistas y lógica necesaria para el pago
def get_payment_methods():
    mp = mercadopago.SDK("TEST-1320068320570405-070920-5ac5bb2c688585001638eec597a2243c-398042112")
    payment_methods = mp.get("/v1/payment_methods") 
    
    # Filtra los métodos de pago disponibles según tus necesidades
    return payment_methods

def purchase_product(request, product_id):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        form.product_id = product_id #asignar el campo product_id al formulario para mantener el contexto al procesar el pago
        if form.is_valid():
            credit_card = form.save(commit=False)
            otp_code = form.cleaned_data['otp_code']

            if match_token(request.user.creditcard.otp_secret, otp_code):
                credit_card.user = request.user
                credit_card.save()

                try:
                    mp = mercadopago.SDK("TEST-1320068320570405-070920-5ac5bb2c688585001638eec597a2243c-398042112")

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

                    return redirect(preference['response']['init_point'])

                except Exception as e:
                    form.add_error(None, 'Error en el procesamiento del pago')
                    print("ERROR:",e.__str__())

            else:
                form.add_error('otp_code', 'Invalid OTP code')
            
            # Generar el número de referencia único para las transacciones en efectivo
            if form.cleaned_data['payment_method'] in ['rapipago', 'pagofacil']:
                reference_number = generate_reference_number()
                credit_card.reference_number = reference_number
                credit_card.save()
    else:
        form = PaymentForm()

    products = Product.objects.all()
    payment_methods = [
        {'name': 'Tarjeta de crédito', 'id': 'credit_card'},
        {'name': 'Tarjeta de débito', 'id': 'debit_card'},
        {'name': 'Rapipago', 'id': 'rapipago'},
        {'name': 'Pago Fácil', 'id': 'pagofacil'}
    ]

    context = {
        'products': products,
        'payment_form': form,
        'payment_methods': payment_methods,
    }
    
    if product_id:
        # Agrega el product_id al contexto
        context['product_id'] = product_id

    return render(request, 'purchase_product.html', context)


def create_preference(product):
    # Configura tu clave de acceso de Mercado Pago
    mp = mercadopago.MP("TEST-1320068320570405-070920-5ac5bb2c688585001638eec597a2243c-398042112")

    # Crea el objeto de preferencia de pago en Mercado Pago
    preference_data = {
        "items": [
            {
                "title": product.name,
                "quantity": 1,
                "currency_id": "ARS",
                "unit_price": str(product.price)
            }
        ],
        "back_urls": {
            "success": request.build_absolute_uri(reverse('payment_success')),
            "pending": request.build_absolute_uri(reverse('payment_pending')),
            "failure": request.build_absolute_uri(reverse('payment_failure'))
        }
    }
    preference = mp.create_preference(preference_data)

    return preference['response']['init_point']

def generate_reference_number():
    # Genera un número aleatorio de 8 dígitos como número de referencia
    return str(random.randint(10000000, 99999999))

def payment_view(request, product_id):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            credit_card = form.save(commit=False)
            otp_code = form.cleaned_data['otp_code']

            if match_token(request.user.creditcard.otp_secret, otp_code):
                credit_card.user = request.user
                credit_card.save()

                try:
                    product = get_object_or_404(Product, id=product_id)
                    
                    # Generar el número de referencia único para las transacciones en efectivo
                    if form.cleaned_data['payment_method'] in ['rapipago', 'pagofacil']:
                        reference_number = generate_reference_number()
                        credit_card.reference_number = reference_number
                        credit_card.save()

                    # Crea el objeto de preferencia de pago en Mercado Pago
                    init_point = create_preference(product)

                    # Actualiza el método de pago con el ID de pago
                    payment_method = form.cleaned_data['payment_method']
                    payment_method.order = Order.objects.create(user=request.user)
                    payment_method.save()

                    # Redirige al usuario a la página de pago de Mercado Pago
                    return redirect(init_point)

                except Exception as e:
                    # Manejo de excepciones generales
                    form.add_error(None, 'Error en el procesamiento del pago')

            else:
                form.add_error('otp_code', 'Invalid OTP code')
    else:
        form = PaymentForm()

    products = Product.objects.all()
    payment_methods = PaymentMethod.objects.all()
    
    # Agregar opciones de pago en efectivo al contexto payment_methods
    payment_methods = payment_methods.exclude(name__in=['rapipago', 'pagofacil']).values('name', 'id')
    payment_methods = list(payment_methods)
    payment_methods.append({'name': 'Rapipago', 'id': 'rapipago'})
    payment_methods.append({'name': 'Pago Fácil', 'id': 'pagofacil'})


    context = {
        'products': products,
        'payment_form': form,
        'payment_methods': payment_methods,
    }

    return render(request, 'payment.html', context)



def payment_success(request):
    if request.method == 'GET':
        payment_id = request.GET.get('payment_id')
        status = request.GET.get('status')

        # Acciones adicionales basadas en los detalles del pago exitoso.
        # Por ejemplo, actualizar el estado del pedido, enviar notificaciones, etc.

        # Obtener el pedido asociado al pago exitoso
        order = Order.objects.get(payment_id=payment_id)

        # Actualizar el estado del pedido
        order.status = 'completed'
        order.save()

        return render(request, 'payment_success.html', {'payment_id': payment_id, 'status': status})


def payment_pending(request):
    # Lógica adicional para procesar el pago pendiente si es necesario
    if request.method == 'GET':
        payment_id = request.GET.get('payment_id')
        status = request.GET.get('status')

        # Acciones adicionales basadas en los detalles del pago pendiente.
        # Por ejemplo, guardar el estado del pago como pendiente, enviar notificaciones, etc.

        # Obtener el pedido asociado al pago pendiente
        order = Order.objects.get(payment_id=payment_id)

        # Actualizar el estado del pedido
        order.status = 'pending'
        order.save()

        return render(request, 'payment_pending.html', {'payment_id': payment_id, 'status': status})


def payment_failure(request):
    # Lógica adicional para procesar el pago fallido si es necesario
    if request.method == 'GET':
        payment_id = request.GET.get('payment_id')
        status = request.GET.get('status')

        # Acciones adicionales basadas en los detalles del pago fallido.
        # Por ejemplo, guardar el estado del pago como fallido, enviar notificaciones, etc.

        # Obtener el pedido asociado al pago fallido
        order = Order.objects.get(payment_id=payment_id)

        # Actualizar el estado del pedido
        order.status = 'failed'
        order.save()

        return render(request, 'payment_failure.html', {'payment_id': payment_id, 'status': status})


# Otras vistas y lógica necesaria para el pago

# Vistas y lógica necesaria para el contacto

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Lógica para enviar el correo electrónico
        send_mail(
            subject='Mensaje de contacto',
            message=f'Nombre: {name}\nEmail: {email}\nMensaje: {message}',
            from_email=email,
            recipient_list=['contact@newfriendsmdp.com'],
        )

        return render(request, 'contact.html', {'success_message': '¡Gracias por contactarnos! Hemos recibido tu mensaje.'})
    else:
        return render(request, 'contact.html')