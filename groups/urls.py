from django.urls import path


urlpatterns = [
    path("pets/", PetView.as_view()),
    path("users/<int:user_id>/", PetDetailView.as_view()),
]