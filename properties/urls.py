from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api

app_name = 'properties'

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'api/properties', api.PropertyViewSet, basename='property-api')

urlpatterns = [
    # Home page
    path('', views.HomeView.as_view(), name='home'),
    
    # Property management (for agents and sellers)
    path('properties/create/', views.PropertyCreateView.as_view(), name='create'),
    path('properties/<slug:slug>/edit/', views.PropertyUpdateView.as_view(), name='update'),
    path('properties/<slug:slug>/delete/', views.PropertyDeleteView.as_view(), name='delete'),
    path('properties/<slug:slug>/images/', views.PropertyImageUploadView.as_view(), name='images'),
    path('properties/image/<int:image_id>/delete/', views.PropertyImageDeleteView.as_view(), name='image_delete'),
    path('properties/<slug:slug>/mark-sold/', views.PropertyMarkSoldView.as_view(), name='mark_sold'),
    
    # Property listings and search
    path('properties/', views.PropertyListView.as_view(), name='list'),
    path('properties/map/', views.PropertyMapView.as_view(), name='map'),
    path('properties/search/', views.PropertySearchView.as_view(), name='search'),
    path('properties/<slug:slug>/', views.PropertyDetailView.as_view(), name='detail'),
    
    # Property actions
    path('properties/<int:pk>/favorite/', views.PropertyFavoriteView.as_view(), name='favorite'),
    path('properties/<int:pk>/inquiry/', views.PropertyInquiryView.as_view(), name='inquiry'),
    
    # Property reviews
    path('properties/<slug:slug>/reviews/create/', views.PropertyReviewCreateView.as_view(), name='review_create'),

    # Newsletter subscription
    path('newsletter/subscribe/', views.NewsletterSubscriptionView.as_view(), name='subscribe'),

    # API URLs - moved to the end
    path('api/', include(router.urls)),
] 