'''
mass email serializer
'''
from rest_framework import serializers
from main.models import MassEmail

class MassEmailSerializer(serializers.Serializer):
    '''
    serialize REST version of mass email model
    '''
    id = serializers.IntegerField(read_only=True)
    
    message_subject = serializers.CharField(max_length=300)
    message_text = serializers.CharField(max_length = 10000)                          
    user_list = serializers.JSONField()                                                              
    email_result = serializers.JSONField()                          
    memo = serializers.CharField(max_length = 300)
    app = serializers.CharField(required=False)
    timestamp = serializers.DateTimeField(format="%m/%d/%Y %H:%M:%S %Z", required=False)

    def create(self, validated_data):
        """
        Create and return a new 'Payments' instance, given the validated data.
        """
        return Payments.objects.create(**validated_data)

