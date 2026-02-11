from rest_framework import serializers
from .models import Property, PropertyImage, PropertyFeature, PropertyAmenity, PropertyReview
from accounts.serializers import UserSerializer

class PropertyFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyFeature
        fields = ['id', 'name', 'icon']

class PropertyAmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyAmenity
        fields = ['id', 'name', 'icon']

class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ['id', 'image', 'caption', 'is_primary', 'created_at']

class PropertyReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = PropertyReview
        fields = ['id', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['user']

class PropertyListSerializer(serializers.ModelSerializer):
    agent = UserSerializer(read_only=True)
    main_image_url = serializers.SerializerMethodField()
    property_type_display = serializers.CharField(source='get_property_type_display', read_only=True)
    listing_type_display = serializers.CharField(source='get_listing_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Property
        fields = [
            'id', 'title', 'slug', 'property_type', 'property_type_display',
            'listing_type', 'listing_type_display', 'status', 'status_display',
            'price', 'area', 'bedrooms', 'bathrooms', 'garage',
            'address', 'city', 'state', 'main_image_url',
            'agent', 'is_featured', 'views_count', 'created_at'
        ]

    def get_main_image_url(self, obj):
        return obj.main_image.url if obj.main_image else None

class PropertyDetailSerializer(serializers.ModelSerializer):
    agent = UserSerializer(read_only=True)
    images = PropertyImageSerializer(many=True, read_only=True)
    features = PropertyFeatureSerializer(many=True, read_only=True)
    amenities = PropertyAmenitySerializer(many=True, read_only=True)
    reviews = PropertyReviewSerializer(many=True, read_only=True)
    property_type_display = serializers.CharField(source='get_property_type_display', read_only=True)
    listing_type_display = serializers.CharField(source='get_listing_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            'id', 'title', 'slug', 'description', 'property_type',
            'property_type_display', 'listing_type', 'listing_type_display',
            'status', 'status_display', 'price', 'area', 'bedrooms',
            'bathrooms', 'garage', 'year_built', 'address', 'city',
            'state', 'zip_code', 'country', 'latitude', 'longitude',
            'features', 'amenities', 'main_image', 'images',
            'video_url', 'virtual_tour_url', 'agent', 'is_featured',
            'views_count', 'reviews', 'average_rating', 'review_count',
            'is_favorited', 'created_at', 'updated_at'
        ]

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorited_by.filter(id=request.user.id).exists()
        return False

class PropertyCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        exclude = ['slug', 'agent', 'views_count', 'favorited_by', 'created_at', 'updated_at']

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    def validate_area(self, value):
        if value < 0:
            raise serializers.ValidationError("Area cannot be negative.")
        return value 