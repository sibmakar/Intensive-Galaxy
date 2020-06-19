from main.models import Cart


def cart_middleware(get_response):
    """
    Cart Middleware

    Notes
    -----
    Automatically connects carts to HTTP requests.
    This will help avoid repeating identical calls in different places.

    Parameters
    ----------
    get_response

    Returns
    -------

    """

    def middleware(request):
        if "cart_id" in request.session:
            cart_id = request.session["cart_id"]
            cart = Cart.objects.get(id=cart_id)
            request.cart = cart
        else:
            request.cart = None
        response = get_response(request)
        return response

    return middleware
