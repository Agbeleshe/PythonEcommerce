from weakref import ref
from django.conf import settings
from django.template import RequestContext
from django.test import RequestFactory



class PayStack:
    PAYSTACK_SECRET_KEY = 'sk_test_b2c04cb22485f1a7206c9435c1c9cc2ab8f96d8a'
    base_url = 'https://api.paystack.co'

    def verify_payment(self, payment_reference):
        path = f'/transaction/verify/{payment_reference}'  # Use the payment_repy ference parameter

        headers = {
            "Authorization": f'Bearer {self.PAYSTACK_SECRET_KEY}',
            "Content-Type": 'application/json',
        }
        url = self.base_url + path

        # Use the 'get' method from the 'requests' library to make the API request
        response = RequestFactory.get(url, headers=headers)

        if response.status_code == 200:
            response_data = response.json()
            return response_data['status'], response_data['data']
        else:
            response_data = response.json()
            return response_data['status'], response_data['message']
