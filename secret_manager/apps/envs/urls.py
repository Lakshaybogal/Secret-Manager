from django.urls import path

from secret_manager.apps.envs.views import (
    add_env,
    change_access_password,
    get_env,
    get_envs,
    get_envs_by_user,
    update_env,
)

urlpatterns = [
    # /users/adduser/?username=lakshay
    path("getenvs/", get_envs, name="getenvs"),
    path("add/", add_env, name="addenv"),
    path("get/", get_env, name="getenv"),
    path("update/", update_env, name="updateenv"),
    path("getuserenvs/", get_envs_by_user, name="getuserenvs"),
    path("accesspassword/", change_access_password, name="accesspassword"),
]
