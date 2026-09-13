from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    user: serializers.StringRelatedField = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['product', 'user', 'created_at']
