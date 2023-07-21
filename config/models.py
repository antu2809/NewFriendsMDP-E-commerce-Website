from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
from django_cryptography.fields import encrypt
from django_otp.models import Device


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to='product_images/')  # campo para la imagen del producto

    def __str__(self):
        return self.name


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='OrderItem')
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    # Otros campos relevantes para los pedidos


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()


class Bank(models.Model):
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name


class PaymentMethod(models.Model):
    name = models.CharField(max_length=255)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, null=True, default=None)
    installment_options = models.CharField(max_length=100, default='')

    def __str__(self):
        return self.name


class CreditCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card_number = encrypt(models.CharField(max_length=16))
    expiration_date = encrypt(models.DateField())
    cvv = encrypt(models.CharField(max_length=4))
    otp_secret = models.CharField(max_length=255, blank=True, null=True)
    reference_number = models.CharField(max_length=8, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.otp_secret:
            # Genera un nuevo secreto de autenticación de dos factores para cada nueva instancia de CreditCard
            device = Device.objects.create(name='Credit Card', user=self.user)
            self.otp_secret = device.config_url.split('=')[-1]
        super().save(*args, **kwargs)


class Payment(models.Model):
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.payment_id