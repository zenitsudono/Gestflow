from rest_framework import serializers
from .models import Resource, Category
from apps.accounts.serializers import CustomUserSerializer

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class ResourceSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = Resource
        fields = [
            'id', 'title', 'description', 'status', 'category', 'category_name',
            'owner', 'owner_name', 'department', 'is_archived', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'department', 'is_archived', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['owner'] = request.user
            # Copy owner's department
            if request.user.department:
                validated_data['department'] = request.user.department
        return super().create(validated_data)
