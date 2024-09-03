import json

from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from secret_manager.apps.users.models import User
from secret_manager.utili import decode_jwt, generate_jwt


@csrf_exempt
def set_admin(request):
    if request.method == "POST":
        if User.objects.filter(username="admin").exists():
            return JsonResponse({"error": "Admin already exists"}, status=409)

        try:
            admin = User(
                username="admin",
                email="admin@example.com",
                role="admin",
                password=make_password("admin"),
                firstname="Admin",
                lastname="Admin",
                contact="0000000000",
                lastLogin=timezone.now(),
            )
            admin.save()
            return JsonResponse({"message": "Admin set successfully"})
        except IntegrityError:
            return JsonResponse({"error": "Failed to create admin user"}, status=500)
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def set_moderator(request):
    if request.method == "POST":
        try:
            moderators = User.objects.filter(role="moderator")
            if len(moderators) >= 5:
                return JsonResponse(
                    {"error": "Maximum of 5 moderators allowed"}, status=409
                )

            email = request.GET.get("email")
            if not email:
                return JsonResponse({"error": "Email is required"}, status=400)

            moderator = User(
                username=f"moderator_{len(moderators) + 1}",
                email=email,
                role="moderator",
                password=make_password("moderator"),
                firstname="Moderator",
                lastname="User",
                lastLogin=timezone.now(),
            )
            moderator.save()
            return JsonResponse({"message": "Moderator created successfully"})
        except IntegrityError:
            return JsonResponse(
                {"error": "Moderator with this email already exists"}, status=409
            )
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def register(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get("username")
            email = data.get("email")
            password = data.get("password")
            firstname = data.get("firstname")
            lastname = data.get("lastname")
            contact = data.get("contact")

            if (
                User.objects.filter(email=email).exists()
                or User.objects.filter(username=username).exists()
            ):
                return JsonResponse(
                    {"error": "User with this email or username already exists"},
                    status=409,
                )

            password_hash = make_password(password)

            user = User(
                username=username,
                email=email,
                password=password_hash,
                firstname=firstname,
                lastname=lastname,
                contact=contact,
                lastLogin=timezone.now(),
            )
            user.save()

            token = generate_jwt(user)

            response = JsonResponse(
                {
                    "message": "User created successfully",
                    "data": {
                        "username": user.username,
                        "email": user.email,
                    },
                    "token": token,
                }
            )

            response.set_cookie(key="session_token", value=token, httponly=True)
            return response
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except IntegrityError:
            return JsonResponse({"error": "Failed to create user"}, status=500)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def get_user(request):
    if request.method == "GET":
        token = request.COOKIES.get("session_token")

        if not token:
            return JsonResponse(
                {"error": "Authentication token is missing"}, status=401
            )

        payload = decode_jwt(token)
        if not payload:
            return JsonResponse(
                {"error": "Invalid token or token has expired"}, status=401
            )

        try:
            user = User.objects.get(id=payload["id"])
            return JsonResponse(
                {
                    "message": "Successfully fetched user",
                    "data": {"username": user.username, "email": user.email},
                }
            )
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


def get_users(request):
    if request.method == "GET":
        try:
            users = User.objects.all()
            user_list = [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "contact": user.contact,
                    "lastLogin": user.lastLogin,
                    "createdAt": user.createdAt,
                    "updatedAt": user.updatedAt,
                }
                for user in users
            ]
            return JsonResponse(
                {"message": "Successfully fetched all users", "data": user_list}
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def login(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        password = data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)

        if not check_password(password, user.password):
            return JsonResponse({"error": "Invalid password"}, status=401)

        user.lastLogin = timezone.now()
        user.save()

        token = generate_jwt(user)

        response = JsonResponse(
            {
                "message": "User authenticated successfully",
                "data": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "firstname": user.firstname,
                },
                "token": token,
            }
        )

        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            samesite="Lax",
            secure=False,  # Use secure=True in production with HTTPS
        )

        return response
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def refresh(request):
    if request.method == "GET":
        token = request.COOKIES.get("session_token")
        if not token:
            return JsonResponse(
                {"error": "Authentication token is missing"}, status=401
            )

        payload = decode_jwt(token)
        if not payload:
            return JsonResponse(
                {"error": "Invalid token or token has expired"}, status=401
            )

        user = User.objects.get(id=payload["id"])
        if not user:
            return JsonResponse({"error": "Unauthenticated token"}, status=404)

        token = generate_jwt(user)
        response = JsonResponse(
            {
                "message": "User authenticated successfully",
                "data": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "firstname": user.firstname,
                },
                "token": token,
            }
        )
        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            samesite="Lax",
            secure=False,  # Use secure=True in production with HTTPS
        )
        return response
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


def logout(request):
    if request.method != "GET":
        response = JsonResponse({"message": "User logged out successfully"})
        response.delete_cookie("session_token")
        return response


@csrf_exempt
def update_user(request):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)
            token = request.COOKIES.get("session_token")

            if not token:
                return JsonResponse(
                    {"error": "Authentication token is missing"}, status=401
                )

            payload = decode_jwt(token)
            if not payload:
                return JsonResponse(
                    {"error": "Invalid token or token has expired"}, status=401
                )

            id = payload["id"]

            user = User.objects.get(id=id)

            # Update fields if they are provided
            if "username" in data:
                user.username = data["username"]
            if "email" in data:
                user.email = data["email"]
            if "password" in data:
                user.password = make_password(data["password"])
            if "firstname" in data:
                user.firstname = data["firstname"]
            if "lastname" in data:
                user.lastname = data["lastname"]
            if "contact" in data:
                user.contact = data["contact"]

            user.updatedAt = timezone.now()
            # Save the updated user object
            user.save()

            return JsonResponse(
                {
                    "message": "User updated successfully",
                    "data": {
                        "username": user.username,
                        "email": user.email,
                        "firstname": user.firstname,
                        "lastname": user.lastname,
                        "contact": user.contact,
                        "role": user.role,
                    },
                }
            )
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def delete_user(request):
    if request.method == "DELETE":
        try:
            id = request.GET.get("id")
            user = User.objects.get(id=id)
            user.delete()
            return JsonResponse({"message": "User deleted successfully"})
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)
