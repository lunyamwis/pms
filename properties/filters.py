import django_filters
from django.db.models import Q
from .models import Property

class PropertyFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    min_area = django_filters.NumberFilter(field_name='area', lookup_expr='gte')
    max_area = django_filters.NumberFilter(field_name='area', lookup_expr='lte')
    min_bedrooms = django_filters.NumberFilter(field_name='bedrooms', lookup_expr='gte')
    min_bathrooms = django_filters.NumberFilter(field_name='bathrooms', lookup_expr='gte')
    location = django_filters.CharFilter(method='filter_location')
    features = django_filters.CharFilter(method='filter_features')
    amenities = django_filters.CharFilter(method='filter_amenities')
    agent = django_filters.NumberFilter(field_name='agent__id')
    is_featured = django_filters.BooleanFilter()
    year_built_min = django_filters.NumberFilter(field_name='year_built', lookup_expr='gte')
    year_built_max = django_filters.NumberFilter(field_name='year_built', lookup_expr='lte')

    class Meta:
        model = Property
        fields = {
            'property_type': ['exact'],
            'listing_type': ['exact'],
            'status': ['exact'],
            'city': ['exact', 'icontains'],
            'state': ['exact', 'icontains'],
            'zip_code': ['exact', 'startswith'],
        }

    def filter_location(self, queryset, name, value):
        return queryset.filter(
            Q(address__icontains=value) |
            Q(city__icontains=value) |
            Q(state__icontains=value) |
            Q(zip_code__icontains=value)
        )

    def filter_features(self, queryset, name, value):
        feature_ids = [int(x) for x in value.split(',') if x.isdigit()]
        return queryset.filter(features__id__in=feature_ids).distinct()

    def filter_amenities(self, queryset, name, value):
        amenity_ids = [int(x) for x in value.split(',') if x.isdigit()]
        return queryset.filter(amenities__id__in=amenity_ids).distinct() 