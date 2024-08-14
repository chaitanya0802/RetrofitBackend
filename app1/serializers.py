from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate
from .models import Product, Profile
from rest_framework import serializers


#serializer for Products data
class Prodserializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['prod_id', 'name', 'image_url']


#Serializer to register the user
class UserRegisterSerializer(serializers.ModelSerializer):
    #data to validate
    email = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=[('RetrofitUser', 'RetrofitUser'), ('Store', 'Store')])

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'role']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    #create user, assign permissions and add to group,Profile
    def create(self, validated_data):
        email = validated_data.pop('email')
        role = validated_data.pop('role')

        #create user in User Model
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )

        #get user group and add user to group
        user_group = Group.objects.get(name=role)
        user.groups.add(user_group)

        #add email and role for user in Profile model
        Profile.objects.create(user=user, email=email, role=role)
        return user


#Serializer to log in the user
class CustomAuthTokenSerializer(serializers.Serializer):
    #data to validate
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)

    class Meta:
        model = User
        fields = ['username', 'password']

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(request=self.context.get('request'), username=username, password=password)

        if not user:
            raise serializers.ValidationError('Wrong username or password', code='authorization')

        attrs['user'] = user
        return attrs
