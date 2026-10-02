from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.conf import settings
import razorpay

from .models import Customer, Restaurant, Item, Cart


def index(request):
    return render(request, "delivery/index.html")


def open_signup(request):
    return render(request, "delivery/signup.html")


def open_signin(request):
    return render(request, "delivery/signin.html")


def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        email = request.POST.get('email', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        address = request.POST.get('address', '').strip()

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return render(request, 'delivery/signup.html', request.POST)

        if Customer.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' already exists. Please choose a different username.")
            return render(request, 'delivery/signup.html', request.POST)

        Customer.objects.create(
            username=username,
            password=password,
            email=email,
            mobile=mobile,
            address=address,
        )
        messages.success(request, f"Welcome {username}! Your account has been created successfully. Please sign in.")
        return redirect('open_signin')

    return render(request, 'delivery/signup.html')


def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        try:
            Customer.objects.get(username=username, password=password)
            messages.success(request, f"Welcome back, {username}!")
            if username == 'admin':
                return redirect('admin_home')
            else:
                return redirect('customer_home', username=username)
        except Customer.DoesNotExist:
            messages.error(request, "Invalid username or password. Please try again.")
            return render(request, 'delivery/signin.html', {"username": username})

    return render(request, 'delivery/signin.html')


def customer_home(request, username):
    customer = get_object_or_404(Customer, username=username)
    restaurantList = Restaurant.objects.all()
    cart = Cart.objects.filter(customer=customer).first()
    cart_count = cart.items.count() if cart else 0
    return render(request, 'delivery/customer_home.html', {
        "restaurantList": restaurantList,
        "username": username,
        "customer": customer,
        "cart_count": cart_count,
    })


def admin_home(request):
    restaurantList = Restaurant.objects.all()
    total_customers = Customer.objects.count()
    total_items = Item.objects.count()
    return render(request, 'delivery/admin_home.html', {
        "restaurantList": restaurantList,
        "total_customers": total_customers,
        "total_restaurants": restaurantList.count(),
        "total_items": total_items,
    })


def open_add_restaurant(request):
    return render(request, 'delivery/add_restaurant.html')


def add_restaurant(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        picture = request.POST.get('picture', '').strip()
        cuisine = request.POST.get('cuisine', '').strip()
        rating = request.POST.get('rating', '4.5')

        if not picture:
            picture = 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=600'

        if Restaurant.objects.filter(name=name).exists():
            messages.error(request, f"Restaurant '{name}' already exists!")
            return render(request, 'delivery/add_restaurant.html', request.POST)

        Restaurant.objects.create(
            name=name,
            picture=picture,
            cuisine=cuisine,
            rating=float(rating) if rating else 4.5,
        )
        messages.success(request, f"Restaurant '{name}' was added successfully!")
        return redirect('open_show_restaurant')

    return render(request, 'delivery/add_restaurant.html')


def open_show_restaurant(request):
    restaurantList = Restaurant.objects.all()
    return render(request, 'delivery/show_restaurant.html', {"restaurantList": restaurantList})


def open_update_restaurant(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    return render(request, 'delivery/update_restaurant.html', {"restaurant": restaurant})


def update_restaurant(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        picture = request.POST.get('picture', '').strip()
        cuisine = request.POST.get('cuisine', '').strip()
        rating = request.POST.get('rating')

        restaurant.name = name
        if picture:
            restaurant.picture = picture
        restaurant.cuisine = cuisine
        if rating:
            restaurant.rating = float(rating)

        restaurant.save()
        messages.success(request, f"Restaurant '{restaurant.name}' updated successfully!")
        return redirect('open_show_restaurant')

    return render(request, 'delivery/update_restaurant.html', {"restaurant": restaurant})


def delete_restaurant(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    name = restaurant.name
    restaurant.delete()
    messages.success(request, f"Restaurant '{name}' has been deleted.")
    return redirect('open_show_restaurant')


def open_update_menu(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    itemList = restaurant.items.all()
    return render(request, 'delivery/update_menu.html', {
        "itemList": itemList,
        "restaurant": restaurant,
    })


def update_menu(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price', '0')
        vegeterian = request.POST.get('vegeterian') == 'on'
        picture = request.POST.get('picture', '').strip()

        if not picture:
            picture = 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500'

        if Item.objects.filter(restaurant=restaurant, name=name).exists():
            messages.error(request, f"Item '{name}' already exists in this restaurant menu!")
        else:
            Item.objects.create(
                restaurant=restaurant,
                name=name,
                description=description,
                price=float(price) if price else 0.0,
                vegeterian=vegeterian,
                picture=picture,
            )
            messages.success(request, f"'{name}' added to menu successfully!")

    return redirect('open_update_menu', restaurant_id=restaurant.id)


def delete_menu_item(request, item_id, restaurant_id):
    item = get_object_or_404(Item, id=item_id, restaurant_id=restaurant_id)
    name = item.name
    item.delete()
    messages.success(request, f"'{name}' removed from menu.")
    return redirect('open_update_menu', restaurant_id=restaurant_id)


def view_menu(request, restaurant_id, username):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    itemList = restaurant.items.all()
    customer = Customer.objects.filter(username=username).first()
    cart = Cart.objects.filter(customer=customer).first() if customer else None
    cart_items_ids = list(cart.items.values_list('id', flat=True)) if cart else []
    cart_count = cart.items.count() if cart else 0
    return render(request, 'delivery/customer_menu.html', {
        "itemList": itemList,
        "restaurant": restaurant,
        "username": username,
        "cart_items_ids": cart_items_ids,
        "cart_count": cart_count,
    })


def add_to_cart(request, item_id, username):
    item = get_object_or_404(Item, id=item_id)
    customer = get_object_or_404(Customer, username=username)

    cart, created = Cart.objects.get_or_create(customer=customer)
    cart.items.add(item)
    messages.success(request, f"'{item.name}' added to cart!")

    return redirect('view_menu', restaurant_id=item.restaurant.id, username=username)


def remove_from_cart(request, item_id, username):
    item = get_object_or_404(Item, id=item_id)
    customer = get_object_or_404(Customer, username=username)

    cart = Cart.objects.filter(customer=customer).first()
    if cart:
        cart.items.remove(item)
        messages.info(request, f"'{item.name}' removed from cart.")

    return redirect('show_cart', username=username)


def show_cart(request, username):
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()
    items = cart.items.all() if cart else []
    total_price = cart.total_price() if cart else 0

    return render(request, 'delivery/cart.html', {
        "itemList": items,
        "total_price": total_price,
        "username": username,
        "customer": customer,
    })


def checkout(request, username):
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()
    cart_items = list(cart.items.all()) if cart else []
    total_price = cart.total_price() if cart else 0

    if total_price == 0 or not cart_items:
        messages.warning(request, "Your cart is empty! Please add items before checking out.")
        return render(request, 'delivery/checkout.html', {
            'username': username,
            'customer': customer,
            'cart_items': [],
            'total_price': 0,
            'error': 'Your cart is empty! Please add items before checking out.',
        })

    key_id = getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_TUQqhpWSZ45HbS')
    key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', 'g3pMwZN1JIGYaaBbVNv0idGW')
    amount_in_paise = int(round(total_price * 100))
    order_id = f"order_demo_{int(total_price * 10)}"

    try:
        client = razorpay.Client(auth=(key_id, key_secret))
        order_data = {
            'amount': amount_in_paise,
            'currency': 'INR',
            'payment_capture': '1',
        }
        order = client.order.create(data=order_data)
        order_id = order.get('id', order_id)
    except Exception as e:
        print(f"Razorpay order initialization notice: {e}")

    return render(request, 'delivery/checkout.html', {
        'username': username,
        'customer': customer,
        'cart_items': cart_items,
        'total_price': total_price,
        'amount_in_paise': amount_in_paise,
        'razorpay_key_id': key_id,
        'order_id': order_id,
        'amount': total_price,
    })


def orders(request, username):
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()

    cart_items = list(cart.items.all()) if cart else []
    total_price = cart.total_price() if cart else 0
    payment_id = request.GET.get('payment_id', '')
    order_id = request.GET.get('order_id', '')
    payment_method = request.GET.get('payment_method', 'UPI / Online')

    if cart:
        cart.items.clear()

    return render(request, 'delivery/orders.html', {
        'username': username,
        'customer': customer,
        'cart_items': cart_items,
        'total_price': total_price,
        'payment_id': payment_id,
        'order_id': order_id,
        'payment_method': payment_method,
    })