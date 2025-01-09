from django.urls import path
from . import views

# urlpatterns = [
#     path('calculator/', views.calculator_view, name='calculator_view'),
# ] Old

urlpatterns = [
    path('', views.calculator_view, name='home'),  # <— capture empty path
    path('calculator/', views.calculator_view, name='calculator_view'),
]