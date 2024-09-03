from django.urls import path

from secret_manager.apps.users.views import (
    register,
    delete_user,
    get_user,
    get_users,
    login,
    update_user,
    set_admin,
    set_moderator,
    refresh,
    logout,
)

urlpatterns = [
    # /users/adduser/?username=lakshay
    path("register/", register, name="register"),
    path("getuser/", get_user, name="getuser"),
    path("login/", login, name="login"),
    path("logout/", logout, name="logout"),
    path("updateuser/", update_user, name="updateuser"),
    path("deleteuser/", delete_user, name="deleteuser"),
    path("getusers/", get_users, name="getusers"),
    path("setadmin/", set_admin, name="setadmin"),
    path("setmoderator/", set_moderator, name="setmoderator"),
    path("refresh/", refresh, name="refresh"),
]
