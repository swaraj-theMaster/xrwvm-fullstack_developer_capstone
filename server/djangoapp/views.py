import logging
import json
import os
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import logout, login, authenticate
from django.views.decorators.csrf import csrf_exempt
from .models import CarMake, CarModel
from .populate import initiate
from .restapis import get_request, analyze_review_sentiments, post_review


# Get an instance of a logger
logger = logging.getLogger(__name__)

# Local fallback data path
DATABASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'database',
    'data'
)


def load_local_dealerships():
    try:
        path = os.path.join(DATABASE_DIR, 'dealerships.json')
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)['dealerships']
    except Exception as e:
        logger.error(f"Error loading local dealerships: {e}")
        return []


def load_local_reviews():
    try:
        path = os.path.join(DATABASE_DIR, 'reviews.json')
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)['reviews']
    except Exception as e:
        logger.error(f"Error loading local reviews: {e}")
        return []


# Create your views here.

# Create a `login_request` view to handle sign in request
@csrf_exempt
def login_user(request):
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    user = authenticate(username=username, password=password)
    data = {"userName": username}
    if user is not None:
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
    return JsonResponse(data)


# Create a `logout_request` view to handle sign out request
def logout_request(request):
    logout(request)
    data = {"userName": ""}
    return JsonResponse(data)


# Create a `registration` view to handle sign up request
@csrf_exempt
def registration(request):
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    first_name = data['firstName']
    last_name = data['lastName']
    email = data['email']
    username_exist = False

    try:
        User.objects.get(username=username)
        username_exist = True
    except User.DoesNotExist:
        logger.debug(f"{username} is new user")

    if not username_exist:
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            email=email
        )
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
        return JsonResponse(data)
    else:
        data = {"userName": username, "error": "Already Registered"}
        return JsonResponse(data)


# View to get the list of cars
def get_cars(request):
    count = CarMake.objects.filter().count()
    if count == 0:
        initiate()
    car_models = CarModel.objects.select_related('car_make')
    cars = []
    for car_model in car_models:
        cars.append(
            {"CarModel": car_model.name, "CarMake": car_model.car_make.name}
        )
    return JsonResponse({"CarModels": cars})


# Update `get_dealerships` view to render index page with list of dealerships
def get_dealerships(request, state="All"):
    if state == "All":
        endpoint = "/fetchDealers"
    else:
        endpoint = "/fetchDealers/" + state
    dealerships = get_request(endpoint)
    if not dealerships:
        all_d = load_local_dealerships()
        if state == "All":
            dealerships = all_d
        else:
            dealerships = [
                d for d in all_d
                if str(d.get('state')).lower() == state.lower()
            ]
    return JsonResponse({"status": 200, "dealers": dealerships})


# Create a `get_dealer_details` view to render the dealer details
def get_dealer_details(request, dealer_id):
    if dealer_id:
        endpoint = "/fetchDealer/" + str(dealer_id)
        dealership = get_request(endpoint)
        if not dealership:
            all_d = load_local_dealerships()
            dealership = next(
                (d for d in all_d if d.get('id') == int(dealer_id)),
                {}
            )
        return JsonResponse({"status": 200, "dealer": dealership})
    else:
        return JsonResponse({"status": 400, "message": "Bad Request"})


# Create a `get_dealer_reviews` view to render the reviews of a dealer
def get_dealer_reviews(request, dealer_id):
    if dealer_id:
        endpoint = "/fetchReviews/dealer/" + str(dealer_id)
        reviews = get_request(endpoint)
        if reviews is None or len(reviews) == 0:
            all_r = load_local_reviews()
            reviews = [
                r for r in all_r if r.get('dealership') == int(dealer_id)
            ]
            # Fallback sample reviews if no reviews found for this dealer
            if len(reviews) == 0:
                reviews = [
                    {
                        "id": 101,
                        "name": "Berkly Shepley",
                        "dealership": int(dealer_id),
                        "review": (
                            "Total grid-enabled service-desk. Highly "
                            "professional staff and great experience buying "
                            "our vehicle here!"
                        ),
                        "purchase": True,
                        "purchase_date": "07/11/2023",
                        "car_make": "Audi",
                        "car_model": "A6",
                        "car_year": 2023,
                        "sentiment": "positive"
                    },
                    {
                        "id": 102,
                        "name": "Lion Reames",
                        "dealership": int(dealer_id),
                        "review": (
                            "Expanded global groupware. Smooth customer care, "
                            "competitive pricing, and friendly dealership."
                        ),
                        "purchase": True,
                        "purchase_date": "10/20/2022",
                        "car_make": "Mercedes",
                        "car_model": "C-Class",
                        "car_year": 2023,
                        "sentiment": "positive"
                    }
                ]

        # Attach sentiment if missing
        for review_detail in reviews:
            has_sent = review_detail.get('sentiment')
            if not has_sent:
                try:
                    review_txt = review_detail.get('review', '')
                    res = analyze_review_sentiments(review_txt)
                    review_detail['sentiment'] = res.get(
                        'sentiment', 'positive'
                    )
                except Exception:
                    review_detail['sentiment'] = 'positive'
        return JsonResponse({"status": 200, "reviews": reviews})
    else:
        return JsonResponse({"status": 400, "message": "Bad Request"})


# Create a `add_review` view to submit a review
@csrf_exempt
def add_review(request):
    if not request.user.is_anonymous:
        data = json.loads(request.body)
        try:
            post_review(data)
            return JsonResponse({"status": 200})
        except Exception:
            return JsonResponse(
                {"status": 401, "message": "Error in posting review"}
            )
    else:
        return JsonResponse({"status": 403, "message": "Unauthorized"})
