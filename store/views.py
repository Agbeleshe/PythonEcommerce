from urllib.request import Request
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
import json
import datetime

from django.template import RequestContext
from django.test import RequestFactory

# from flask import redirect

from .models import *
from .utils import cookieCart, cartData, guestOrder
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from . import forms
from django.conf import settings
from .models import Payment
from django.contrib import messages

import uuid
import json


from django.core.exceptions import ObjectDoesNotExist



# New tesr view

# def process_order(request):
#     if request.method == 'POST':
#         try:
#             # Debugging: Print the request body
#             print(request.body.decode('utf-8'))

#             # Attempt to parse the JSON data from request.body
#             data = json.loads(request.body.decode('utf-8'))
            
#             # Now you can access data like data['name'], data['email'], etc.
#             name = data.get('name')
#             email = data.get('email')
#             total = data.get('total')

#             # Generate a unique payment reference (you can use a combination of timestamp and a random string)
#             payment_ref = str(uuid.uuid4())

#             # Collect user and order information
#             user_email = email  # Use the 'email' from the JSON data
#             total_amount = total  # Use the 'total' from the JSON data

#             # Send payment request to Paystack
#             paystack_api_key = 'sk_test_b2c04cb22485f1a7206c9435c1c9cc2ab8f96d8a'
#             paystack_url = 'https://api.paystack.co/transaction/initialize'
            
#             headers = {
#                 'Authorization': f'Bearer {paystack_api_key}',
#                 'Content-Type': 'application/json',
#             }

#             payload = {
#                 'reference': payment_ref,
#                 'email': user_email,
#                 'amount': total_amount,
#             }

#             try:
#                 response = Request.post(paystack_url, json=payload, headers=headers)
                
#                 # Check if the response contains valid JSON data
#                 if response.status_code == 200:
#                     payment_data = response.json()
#                 else:
#                     return JsonResponse({'error': 'Failed to connect to Paystack API'})

#                 # Handle the Paystack response and redirect the user
#                 if payment_data.get('status'):
#                     payment_url = payment_data.get('data').get('authorization_url')
#                     return redirect(payment_url)
#                 else:
#                     # Handle payment request error
#                     return JsonResponse({'error': 'Payment request failed'})
            
#             except RequestFactory.exceptions.RequestException as e:
#                 return JsonResponse({'error': f'RequestException: {str(e)}'})

#         except json.JSONDecodeError as e:
#             return JsonResponse({'error': f'JSON Decode Error: {str(e)}'})

#     return JsonResponse({'error': 'Invalid request method'})




# Create your views here.


def initiate_payment(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        payment_form = forms.PaymentForm(request.POST)
        if payment_form.is_valid():
            payment = payment_form.save()

            # Access the related Customer object for the logged-in user
            try:
                customer = request.user.customer
            except ObjectDoesNotExist:
                customer = None  # If the customer doesn't exist, set it to None or handle the error as needed

            return render(request, '.make_Payment.html', {'payment': payment, 'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY})
        else:
            payment_form = forms.PaymentForm()
            render(request, '.initiate_payment.html', {'payment_form': payment_form})
            # This should be a redirect template in case payment isn't sent


def verify_payment(request: HttpRequest, ref: str) -> HttpResponse:
    payment = get_object_or_404(Payment, ref=ref)
    verified = payment.verify_payment()
    if verified:
        messages.success(request, 'Verification Successful')
    else:
     messages.error(request, 'Verification Failed ')
     return redirect('initiate-payment')
    
def calculate_cart_total(cart):
    total = 0
    for item in cart:
        total += item['quantity'] * item['price']
    return total

def store(request):
    data = cartData(request)
    cartItems = data['cartItems']
    products = Product.objects.all()
    context = {'products': products, 'cartItems': cartItems}
    return render(request, 'store/store.html', context)


def cart(request):

    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/cart.html', context)


def checkout(request):

    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/checkout.html', context)


def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']

    print('Action:', action)
    print('productId:', productId)

    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(
        customer=customer, complete=False)
    orderItem, created = OrderItem.objects.get_or_create(
        order=order, product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)


def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(
            customer=customer, complete=False)

    else:
        customer, order = guestOrder(request, data)

    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == order.get_cart_total:
        order.complete = True
    order.save()

    if order.shipping == True:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            zipcode=data['shipping']['zipcode'],
        )

    return JsonResponse('Payment Complete!', safe=False)
