from django.urls import path
from . import views

urlpatterns = [
    path('pricing/', views.pricing_page, name='pricing_page'),
    path('pay/initiate/', views.initiate_payment, name='initiate_payment'),

    path('pay/success/', views.payment_success, name='payment_success'),
    path('callback/', views.mpesa_callback, name='mpesa_callback'),
]