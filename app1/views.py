import psycopg2
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny, DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.views import APIView
from app1.models import Product
from .serializers import Prodserializer, UserRegisterSerializer, CustomAuthTokenSerializer


# register new user
class UserRegisterView(CreateAPIView):
    serializer_class = UserRegisterSerializer
    #no permission required for registration
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        #get username
        username = request.data.get('username')
        #check if it already exists
        if User.objects.filter(username=username).exists():
            return Response({'message': 'Phone No. Already Used (Try Login)'})

        #get serializer instance
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            #call create() in serializer
            self.perform_create(serializer)
            return Response({'message': 'Account Created'}, status=status.HTTP_201_CREATED)


# login user in using token (authentication)
class CustomAuthToken(APIView):
    # no permission required for registration
    permission_classes = [AllowAny]
    serializer_class = CustomAuthTokenSerializer

    def post(self, request):
        #get serializer instance
        serializer = self.serializer_class(data=request.data, context={'request': request})
        try:
            #call validate() in serializer
            serializer.is_valid(raise_exception=True)
        #if validate() raises ValidationError
        except ValidationError:
            return Response({'message': 'Wrong username or password'})

        #get the user
        user = serializer.validated_data['user']
        #get or create token, created=true if token created and vice versa
        token, created = Token.objects.get_or_create(user=user)
        return Response({'message': 'success', 'token': token.key}, status=status.HTTP_200_OK)


# create custom pagination class
class CustomPagination(PageNumberPagination):
    page_query_param = 'page'
    page_size_query_param = 'page_size'
    page_size = 10
    max_page_size = 30


# Retrieve products
class ProductListView(generics.ListAPIView):
    # add permission class
    permission_classes = [IsAuthenticated]
    # set pagination class
    pagination_class = CustomPagination
    # set serializer class
    serializer_class = Prodserializer

    def get_queryset(self):
        #getting search query
        search_query = self.request.query_params.get('q', None)

        # getting user from token
        token_key = self.request.headers.get('Authorization').split(' ')[1]     #actual token
        token = Token.objects.get(key=token_key)        #get Token instance from db
        user = token.user
        print("--------------USER IS:",user)

        #getting group of user
        user_groups = user.groups.all()
        groups = [group.name for group in user_groups]
        print("--------------GROUP IS:", groups)

        conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT']
        )
        cur = conn.cursor()
        try:
            # search products
            if search_query:
                cur.execute(
                    """
                    SELECT prod_id, name, image_url
                    FROM app1_product 
                    WHERE name ILIKE %s OR prod_id ILIKE %s
                    ORDER BY name;
                    """,
                    (f'%{search_query}%', f'%{search_query}%')
                )
            # get all products
            else:
                cur.execute("SELECT prod_id, name, image_url FROM app1_product ORDER BY name;")

            rows = cur.fetchall()
            products = [Product(prod_id=row[0], name=row[1], image_url=row[2]) for row in rows]
            return products
        except Exception as e:
            return Response(data={'message': f'{e}'}, status=status.HTTP_404_NOT_FOUND)
        finally:
            cur.close()
            conn.close()


# Create Products
class ProductCreateView(generics.CreateAPIView):
    # set serializer class
    serializer_class = Prodserializer
    # add permission class
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):

        # getting user from token
        token_key = self.request.headers.get('Authorization').split(' ')[1]
        token = Token.objects.get(key=token_key)
        user = token.user
        print("--------------USER IS:", user)
        conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT']
        )
        cur = conn.cursor()
        try:
            # deserialize incoming data
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # get validated data from serializer
            data = serializer.validated_data
            cur.execute(
                """
                INSERT INTO app1_product (prod_id, name, image_url) 
                VALUES (%s, %s, %s)
                RETURNING prod_id;
                 """,
                (data['prod_id'], data['name'], data['image_url'])
            )
            conn.commit()
            return Response(data={'message': 'Product Added successfully'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(data={'message': f'{e}'}, status=status.HTTP_501_NOT_IMPLEMENTED)
        finally:
            cur.close()
            conn.close()


# Update products
class ProductUpdateView(generics.UpdateAPIView):
    # add permission class
    permission_classes = [IsAuthenticated]
    # set serializer class
    serializer_class = Prodserializer

    def put(self, request, *args, **kwargs):
        prod_id = self.kwargs.get('pk')
        conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT']
        )
        cur = conn.cursor()
        try:
            instance = Product.objects.get(pk=prod_id)

            serializer = self.get_serializer(instance=instance, data=request.data, partial=False)
            serializer.is_valid(raise_exception=True)

            updated_data = serializer.validated_data
            if updated_data['prod_id'] == prod_id:
                cur.execute("""
                       UPDATE app1_product
                       SET name = %s, image_url = %s 
                       WHERE prod_id = %s;
                   """, (updated_data['name'], updated_data['image_url'], prod_id))
                conn.commit()
                return Response(data={'message': 'Product Updated Successfully'}, status=status.HTTP_200_OK)
            else:
                raise Exception("Please do not change prod_id for the Product.")
        except Exception as e:
            return Response(data={'message': f'{e}'}, status=status.HTTP_501_NOT_IMPLEMENTED)
        finally:
            cur.close()
            conn.close()


# Delete Products
class ProductDeleteView(generics.DestroyAPIView):
    # add permission class
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        prod_id = self.kwargs.get('pk')
        conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT']
        )
        cur = conn.cursor()
        try:
            cur.execute("SELECT prod_id FROM app1_product WHERE prod_id=%s ;", (prod_id,))
            row = cur.fetchone()
            if row:
                cur.execute("DELETE FROM app1_product WHERE prod_id = %s ;", (prod_id,))
                conn.commit()
                return Response(data={"message": "Product deleted successfully."}, status=status.HTTP_202_ACCEPTED)
            else:
                raise Exception("The product does not exists.")
        except Exception as e:
            return Response(data={"message": f'{e}'}, status=status.HTTP_501_NOT_IMPLEMENTED)
        finally:
            cur.close()
            conn.close()
