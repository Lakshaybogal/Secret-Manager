from django.http import JsonResponse
from secret_manager.utili import unique_id


def root(request):
    if request.method == "GET":
        unique_id()
        return JsonResponse({"message": "Jai Mata Di"})
