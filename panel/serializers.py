from rest_framework import serializers
from .models import RequestToHIS


class RequestToHISSerializer(serializers.Serializer):
    source = serializers.CharField(max_length=50)
    url = serializers.CharField(max_length=50)
    method = serializers.CharField(max_length=10)
    date_time = serializers.DateTimeField()

    def create(self, validated_data):
        return RequestToHIS.objects.create(**validated_data)
