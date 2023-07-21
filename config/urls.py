from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import register
from django.contrib.auth.views import LoginView

urlpatterns = [
    path('admin', admin.site.urls),
    path('', views.base_view, name='base'),
    path('product_list', views.product_list, name='product_list'),
    path('purchase_product/<int:product_id>', views.purchase_product, name='purchase_product'),
    path('payment_view/<int:product_id>', views.payment_view, name='payment_view'),
    path('payment_success', views.payment_success, name='payment_success'),
    path('payment_pending', views.payment_pending, name='payment_pending'),
    path('payment_failure', views.payment_failure, name='payment_failure'),
    path('admin_product_list', views.admin_product_list, name='admin_product_list'),
    path('admin_products_add', views.add_product, name='add_product'),
    path('admin_products_update_<int:product_id>', views.update_product, name='update_product'),
    path('admin_products_delete_<int:product_id>', views.delete_product, name='delete_product'),
    path('low_stock_notification', views.low_stock_notification, name='low_stock_notification'),
    path('accounts', include('allauth.urls')),  # URL base para todas las vistas de autenticación de allauth
    path('register', views.register, name='register'),  # Vista de registro de allauth
    path('login', LoginView.as_view(template_name='login.html'), name='login'),  # Vista de inicio de sesión de allauth
    path('profile', views.profile, name='profile'),
    path('update_profile', views.update_profile, name='update_profile'),
    path('purchase_history', views.purchase_history, name='purchase_history'),
    path('contact', views.contact, name='contact'),
    # Agrega aquí más patrones de URL según las necesidades de tu proyecto
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
