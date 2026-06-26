from rest_framework import serializers
from .models import Document
import os

class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    file_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'file', 'file_type', 'size', 'resource', 
            'uploaded_by', 'uploaded_by_name', 'file_name', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'file_type', 'size', 'uploaded_by', 'created_at', 'updated_at']

    def get_file_name(self, obj):
        if obj.file:
            return os.path.basename(obj.file.name)
        return ""

    def validate_file(self, value):
        # 10MB size limit check
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size exceeds the 10MB limit.")

        # Allowed extension check (OWASP top 10 secure file validation)
        ext = os.path.splitext(value.name)[1].lower()
        allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg', '.gif', '.txt', '.csv']
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type {ext} not allowed. Supported types: {', '.join(allowed_extensions)}"
            )
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['uploaded_by'] = request.user
        return super().create(validated_data)
