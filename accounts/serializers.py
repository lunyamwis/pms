from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'role', 'phone', 'profile_picture', 'bio', 'website'
        ]
        read_only_fields = ['email']

    def get_full_name(self, obj):
        return obj.get_full_name()

class UserDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    social_links = serializers.SerializerMethodField()
    property_count = serializers.IntegerField(read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'role', 'phone', 'profile_picture', 'bio', 'address',
            'website', 'social_links', 'property_count', 'average_rating',
            'review_count'
        ]
        read_only_fields = ['email', 'role']

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_social_links(self, obj):
        return {
            'website': obj.website,
            'facebook': obj.facebook,
            'twitter': obj.twitter,
            'linkedin': obj.linkedin
        }

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'profile_picture',
            'bio', 'address', 'website', 'facebook', 'twitter', 'linkedin'
        ]

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password1 = serializers.CharField(required=True)
    new_password2 = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError("The two password fields didn't match.")
        return data

class EmailPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'email_notifications',
            'email_newsletter',
            'email_marketing'
        ] 