from django.urls import path, include

from app1.views import ProductListView, ProductCreateView, ProductUpdateView, ProductDeleteView, UserRegisterView, \
    CustomAuthToken

urlpatterns = [
    path('register/',UserRegisterView.as_view(),name='register-user'),
    path('login/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('getProducts/', ProductListView.as_view(), name='product-list'),
    path('createProducts/', ProductCreateView.as_view(), name='product-list'),
    path('updateProducts/<str:pk>', ProductUpdateView.as_view(), name='product-list'),
    path('deleteProducts/<str:pk>', ProductDeleteView.as_view(), name='product-list'),
]