import json
import logging
import random

import dotenv
import rsa
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from secret_manager.apps.envs.models import Env, EnvSecret
from secret_manager.apps.users.models import User
from secret_manager.utili import decode_jwt

logger = logging.getLogger(__name__)

# Load environment variables
dotenv.load_dotenv()


def error_response(message, status_code):
    """Utility function for generating error responses."""
    return JsonResponse({"error": message}, status=status_code)


@csrf_exempt
def get_envs(request):
    if request.method == "GET":
        envs = Env.objects.all()
        env_list = [
            {
                "id": env.id,
                "name": env.name,
                "value": env.value,
                "user": env.user.email,
                "description": env.description,
                "access_password": env.access_password,
            }
            for env in envs
        ]
        return JsonResponse(
            {"message": "Successfully fetched all envs", "data": env_list}
        )
    return error_response("Invalid request method", 405)


@csrf_exempt
def add_env(request):
    if request.method == "POST":
        try:
            token = request.COOKIES.get("session_token")
            if not token:
                return error_response("Authentication token is missing", 401)

            payload = decode_jwt(token)
            if not payload:
                return error_response("Invalid token or token has expired", 401)

            data = json.loads(request.body)
            name = data.get("name")
            value = data.get("value")
            description = data.get("description")
            if not name:
                return error_response("Secret name is missing", 400)
            if not value:
                return error_response("Secret value is missing", 400)

            user = User.objects.get(id=payload["id"])

            # Generate RSA keys
            publicKey, privateKey = rsa.newkeys(1024)
            encrypted_value = rsa.encrypt(value.encode(), publicKey)

            # Save private key in ENVSecret
            privateKey_instance = EnvSecret(key=privateKey.save_pkcs1().decode("utf-8"))
            privateKey_instance.save()

            access_password = random.randbytes(4).hex()
            env = Env(
                name=name,
                value=encrypted_value.hex(),
                user=user,
                key_id=privateKey_instance,
                description=description,
                access_password=access_password,
            )
            env.save()

            return JsonResponse(
                {
                    "message": "Env created successfully",
                    "data": {
                        "id": env.id,
                        "name": env.name,
                        "value": value,
                        "access_password": env.access_password,
                        "description": env.description,
                    },
                }
            )
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON format")
        except ObjectDoesNotExist:
            return error_response("User does not exist", 404)
        except rsa.pkcs1.CryptoError:
            return error_response("Encryption failed", 500)
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return error_response(str(e), 500)

    return error_response("Invalid request method", 405)


@csrf_exempt
def get_env(request):
    if request.method == "GET":
        try:
            key = request.GET.get("key")
            access_password = request.GET.get("access_password")

            if not key or not access_password:
                return error_response("Missing key or access password", 400)

            env = Env.objects.get(id=key)
            logger.info(f"API Request Count Before: {env.api_requests}")

            if env.api_requests <= 0:
                return JsonResponse(
                    {
                        "message": "Request limit exceeded",
                        "data": {
                            "name": env.name,
                            "value": "",
                            "user": env.user.email,
                        },
                    }
                )
            if access_password != env.access_password:
                return error_response("Invalid access password", 401)

            # Decrypt the value
            private_key = rsa.PrivateKey.load_pkcs1(env.key_id.key.encode())
            encrypted_value = bytes.fromhex(env.value)
            decrypted_value = rsa.decrypt(encrypted_value, private_key).decode()

            env.api_requests -= 1
            env.save()
            logger.info(f"API Request Count After: {env.api_requests}")

            return JsonResponse(
                {
                    "message": "Successfully fetched env",
                    "data": {
                        "name": env.name,
                        "value": decrypted_value,
                        "user": env.user.email,
                    },
                }
            )
        except ObjectDoesNotExist:
            return error_response("Env not found", 404)
        except rsa.pkcs1.CryptoError:
            return error_response("Decryption failed", 500)
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return error_response(str(e), 500)

    return error_response("Invalid request method", 405)


@csrf_exempt
def get_envs_by_user(request):
    if request.method == "GET":
        token = request.COOKIES.get("session_token")
        if not token:
            return error_response("Authentication token is missing", 401)

        payload = decode_jwt(token)
        if not payload:
            return error_response("Invalid token or token has expired", 401)

        try:
            user = User.objects.get(id=payload["id"])
        except User.DoesNotExist:
            return error_response("User not found", 404)

        envs = Env.objects.filter(user=user).select_related("key_id")
        env_list = []

        for env in envs:
            try:
                private_key = rsa.PrivateKey.load_pkcs1(env.key_id.key.encode())
                encrypted_value = bytes.fromhex(env.value)
                decrypted_value = rsa.decrypt(encrypted_value, private_key).decode()
                env_list.append(
                    {
                        "id": env.id,
                        "name": env.name,
                        "value": decrypted_value,
                        "user": env.user.email,
                        "description": env.description,
                        "access_password": env.access_password,
                        "api_requests": env.api_requests,
                    }
                )
            except (ValueError, rsa.DecryptionError) as e:
                logger.error(
                    f"Decryption error for env {env.id}: {str(e)}", exc_info=True
                )
                return error_response(f"Decryption error: {str(e)}", 500)

        return JsonResponse(
            {"message": "Successfully fetched all envs", "data": env_list}
        )

    return error_response("Invalid request method", 405)


@csrf_exempt
def change_access_password(request):
    if request.method == "PUT":
        token = request.COOKIES.get("session_token")
        data = json.loads(request.body)
        name = data.get("name")

        if name is None:
            return error_response("Env name is missing", 400)

        if not token:
            return error_response("Authentication token is missing", 401)

        payload = decode_jwt(token)
        if not payload:
            return error_response("Invalid token or token has expired", 401)

        try:
            user = User.objects.get(id=payload["id"])
            env = Env.objects.get(name=name, user=user)
        except User.DoesNotExist:
            return error_response("User not found", 404)
        except Env.DoesNotExist:
            return error_response("Env not found", 404)

        access_password = random.randbytes(4).hex()
        env.access_password = access_password
        env.save()

        return JsonResponse(
            {
                "message": "Successfully changed access password",
                "data": {"access_password": access_password},
            }
        )

    return error_response("Invalid request method", 405)


@csrf_exempt
def update_env(request):
    if request.method == "PUT":
        token = request.COOKIES.get("session_token")
        data = json.loads(request.body)
        name = data.get("name")

        if name is None:
            return error_response("Env name is missing", 400)

        if not token:
            return error_response("Authentication token is missing", 401)

        payload = decode_jwt(token)
        if not payload:
            return error_response("Invalid token or token has expired", 401)

        try:
            user = User.objects.get(id=payload["id"])
            env = Env.objects.get(name=name, user=user)
        except User.DoesNotExist:
            return error_response("User not found", 404)
        except Env.DoesNotExist:
            return error_response("Env not found", 404)

        value = data.get("value")
        if value:
            # Delete the old EnvSecret and generate a new one
            env.key_id.delete()
            publicKey, privateKey = rsa.newkeys(1024)
            encrypted_value = rsa.encrypt(value.encode(), publicKey)
            privateKey_instance = EnvSecret(key=privateKey.save_pkcs1().decode("utf-8"))
            privateKey_instance.save()
            env.value = encrypted_value.hex()
            env.key_id = privateKey_instance

        description = data.get("description")
        if description:
            env.description = description

        env.save()

        return JsonResponse({"message": "Successfully updated env"})

    return error_response("Invalid request method", 405)
