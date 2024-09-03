import random
from datetime import datetime, timedelta
from uuid import uuid4

import jwt
from django.conf import settings


def generate_jwt(user):
    # print(user.get_user())
    payload = {
        "id": str(user.id),
        "username": user.username,
        "role": user.role,
        "email": user.email,
        "exp": datetime.now() + timedelta(seconds=settings.JWT_EXP_DELTA_SECONDS),
    }
    token = jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return token


def decode_jwt(token):
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        print("Invalid token")
        return None


def unique_id(length=16):
    uuid_hex = uuid4().hex
    random_string = "".join(random.choice(uuid_hex) for _ in range(length))
    return random_string
