from distutils.util import strtobool

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import IntegrityError
from django.db.models import Q, Sum, F
from django.http import JsonResponse
from django_rest_passwordreset.views import ResetPasswordConfirm
from drf_yasg.utils import swagger_auto_schema
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from ujson import loads as load_json

from backend.models import Shop, Category, ProductInfo, Order, OrderItem, Contact, ConfirmEmailToken
from backend.serializers import UserSerializer, CategorySerializer, ShopSerializer, ProductInfoSerializer, \
    OrderItemSerializer, OrderSerializer, ContactSerializer
from backend.signals import new_user_registered
from backend.tasks import send_order, get_price


class RegisterAccount(APIView):
    """
    Для регистрации покупателей
    """

    # Регистрация методом POST
    # @swagger_auto_schema(
    #     operation_summary='register user',
    #     request_body=openapi.SchemaRef("#/definitions/User", schema_view),
    #         # in_=openapi.IN_QUERY,
    #         # type=openapi.CONTENT,
    #         # content=
    #         # properties={
    #         #     'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='Имя пользователя'),
    #         #     'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Фамилия пользователя'),
    #         #     'surname': openapi.Schema(type=openapi.TYPE_STRING, description='Отчество пользователя'),
    #         #     'email': openapi.Schema(type=openapi.TYPE_STRING, description='email пользователя'),
    #         #     'password1': openapi.Schema(type=openapi.TYPE_STRING, description='Пароль'),
    #         #     'password2': openapi.Schema(type=openapi.TYPE_STRING, description='Повтор пароля'),
    #         #     'company': openapi.Schema(type=openapi.TYPE_STRING, description='Компания пользователя'),
    #         #     'position': openapi.Schema(type=openapi.TYPE_STRING, description='Должность пользователя')
    #         # }),
    #     # ),
    #     # default={'first_name': 'User','last_name': 'Last', 'surname': 'Sur',
    #     #          'email': 'a@a.ru', 'password1': 'asdfreq23!', 'password2': 'asdfreq23!',
    #     #          'company': 'Firma', 'position': 'manager'},
    #     responses={200, {'Status': True}},
    #     )
    def post(self, request, *args, **kwargs):

        # проверяем обязательные аргументы
        if {'first_name', 'last_name', 'email', 'password1', 'password2', 'company', 'position'}.issubset(request.data):
            errors = {}

            # проверяем совпадение паролей
            if request.data['password1'] != request.data['password2']:
                return JsonResponse({'Status': False, 'Errors': 'Пароли не совпадают'}, status=400)
            request.data._mutable = True
            request.data['password'] = request.data['password1']

            # проверяем пароль на сложность
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                # проверяем данные для уникальности имени пользователя
                request.data.update({})
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    # сохраняем пользователя
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    new_user_registered.send(sender=self.__class__, user_id=user.id)
                    return JsonResponse({'Status': True})
                else:
                    return JsonResponse({'Status': False, 'Errors': user_serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class PasswordConfirm(ResetPasswordConfirm):
    def post(self, request, *args, **kwargs):
        # проверяем совпадение паролей
        if request.data['password1'] != request.data['password2']:
            return JsonResponse({'Status': False, 'Errors': 'Пароли не совпадают'}, status=400)
        request.data._mutable = True
        request.data['password'] = request.data['password1']
        return ResetPasswordConfirm.post(self, request, *args, **kwargs)


class ConfirmAccount(APIView):
    """
    Класс для подтверждения почтового адреса
    """

    # Регистрация методом POST
    def post(self, request, *args, **kwargs):

        # проверяем обязательные аргументы
        if {'email', 'token'}.issubset(request.data):

            token = ConfirmEmailToken.objects.filter(user__email=request.data['email'],
                                                     key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': 'Неправильно указан токен или email'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class AccountDetails(APIView):
    """
    Класс для работы данными пользователя
    """

    # получить данные
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    # Редактирование методом POST
    @swagger_auto_schema(
        operation_summary='Редактирование users',
        request_body=UserSerializer)
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        # проверяем обязательные аргументы
        if {'password1', 'password2'}.issubset(request.data):

            # проверяем совпадение паролей
            if request.data['password1'] != request.data['password2']:
                return JsonResponse({'Status': False, 'Errors': 'Пароли не совпадают'}, status=400)
            request.data._mutable = True
            request.data['password'] = request.data['password1']

            try:
                # проверяем пароль на сложность
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)

                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                request.user.set_password(request.data['password'])

        # проверяем остальные данные
        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse({'Status': True})
        else:
            return JsonResponse({'Status': False, 'Errors': user_serializer.errors}, status=400)


class LoginAccount(APIView):
    """
    Класс для авторизации пользователей
    """

    # Авторизация методом POST
    def post(self, request, *args, **kwargs):

        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])

            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)

                    return JsonResponse({'Status': True, 'Token': token.key})

            return JsonResponse({'Status': False, 'Errors': 'Не удалось авторизовать'}, status=403)

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class CategoryView(ListAPIView):
    """
    Класс для просмотра категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopView(ListAPIView):
    """
    Класс для просмотра списка магазинов
    """
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer


class ProductInfoView(APIView):
    """
    Класс для поиска товаров
    """

    def get(self, request, *args, **kwargs):

        query = Q(shop__state=True)
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')

        if shop_id:
            query = query & Q(shop_id=shop_id)

        if category_id:
            query = query & Q(product__category_id=category_id)

        # фильтруем и отбрасываем дубликаты
        queryset = ProductInfo.objects.filter(
            query).select_related(
            'shop', 'product__category').prefetch_related(
            'product_parameters__parameter').distinct()

        serializer = ProductInfoSerializer(queryset, many=True)

        return Response(serializer.data)


class BasketView(APIView):
    """
    Класс для работы с корзиной пользователя
    """

    # получить корзину
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        basket = Order.objects.filter(
            user_id=request.user.id, state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)

    # @swagger_auto_schema(
    #     operation_summary='Add items to basket',
    #     # request_body=OrderItemSerializer,
    #     request_body=openapi.Schema(
    #         in_=openapi.IN_FORM,
    #         type=openapi.TYPE_OBJECT,
    #         properties={
    #             'items': openapi.Schema(type=openapi.TYPE_STRING, description='product_info and quantity')
    #         },
    #         default={'items': "[{\"product_info\": 2, \"quantity\": 1}, {\"product_info\": 3, \"quantity\": 2}]"},
    #     ),
    # )
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Login required'}, status=403)

        items_sting = request.data.get('items')
        if items_sting:
            try:
                items_dict = load_json(items_sting)
            except ValueError:
                JsonResponse({'Status': False, 'Errors': 'Неверный формат запроса'})
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
                objects_created = 0
                for order_item in items_dict:
                    order_item.update({'order': basket.id})
                    serializer = OrderItemSerializer(data=order_item)
                    if serializer.is_valid():
                        try:
                            serializer.save()

                        except IntegrityError as error:
                            return JsonResponse({'Status': False, 'Errors': str(error)})
                        else:
                            objects_created += 1

                    else:

                        JsonResponse({'Status': False, 'Errors': serializer.errors})

                return JsonResponse({'Status': True, 'Создано объектов': objects_created})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)

    # @swagger_auto_schema(
    #     operation_description='Удаление продуктов из корзины',
    #     request_body=OrderItemSerializer)
    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
            query = Q()
            objects_deleted = False
            for order_item_id in items_list:
                if order_item_id.isdigit():
                    query = query | Q(order_id=basket.id, id=order_item_id)
                    objects_deleted = True

            if objects_deleted:
                deleted_count = OrderItem.objects.filter(query).delete()[0]
                return JsonResponse({'Status': True, 'Удалено объектов': deleted_count})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)

    # @swagger_auto_schema(
    #     operation_description='Добавление новых позиций в корзину',
    #     request_body=OrderItemSerializer)
    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items_sting = request.data.get('items')
        if items_sting:
            try:
                items_dict = load_json(items_sting)
            except ValueError:
                JsonResponse({'Status': False, 'Errors': 'Неверный формат запроса'})
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
                objects_updated = 0
                for order_item in items_dict:
                    if type(order_item['id']) == int and type(order_item['quantity']) == int:
                        objects_updated += OrderItem.objects.filter(order_id=basket.id, id=order_item['id']).update(
                            quantity=order_item['quantity'])

                return JsonResponse({'Status': True, 'Обновлено объектов': objects_updated})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)


class PartnerUpdate(APIView):
    """
    Класс для обновления прайса от поставщика
    """

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=405)

        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'Error': str(e)}, status=403)
            else:
                # блок для использования в Celery
                job_params = {'url': url, 'user_id': request.user.id}
                get_price.delay(job_params)
                return JsonResponse({'Status': True}, status=200)
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)


class PartnerState(APIView):
    """
    Класс для работы со статусом поставщика
    """

    # получить текущий статус
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=405)

        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    # изменить текущий статус
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=405)
        state = request.data.get('state')
        if state:
            try:
                Shop.objects.filter(user_id=request.user.id).update(state=strtobool(state))
                return JsonResponse({'Status': True})
            except ValueError as error:
                return JsonResponse({'Status': False, 'Errors': str(error)})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)


class PartnerOrders(APIView):
    """
    Класс для получения заказов поставщиками
    """

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=405)

        order = Order.objects.filter(
            ordered_items__product_info__shop__user_id=request.user.id).exclude(state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)


class ContactView(APIView):
    """
    Класс для работы с контактами покупателей
    """

    # получить мои контакты
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        contact = Contact.objects.filter(
            user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    # добавить новый контакт
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if {'city', 'street', 'phone'}.issubset(request.data):
            request.data._mutable = True
            request.data.update({'user': request.user.id})
            serializer = ContactSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'Status': True})
            else:
                JsonResponse({'Status': False, 'Errors': serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)

    # удалить контакт
    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            query = Q()
            objects_deleted = False
            for contact_id in items_list:
                if contact_id.isdigit():
                    query = query | Q(user_id=request.user.id, id=contact_id)
                    objects_deleted = True

            if objects_deleted:
                deleted_count = Contact.objects.filter(query).delete()[0]
                return JsonResponse({'Status': True, 'Удалено объектов': deleted_count})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    # редактировать контакт
    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if 'id' in request.data:
            if request.data['id'].isdigit():
                contact = Contact.objects.filter(id=request.data['id'], user_id=request.user.id).first()
                if contact:
                    serializer = ContactSerializer(contact, data=request.data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return JsonResponse({'Status': True})
                    else:
                        return JsonResponse({'Status': False, 'Errors': serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)


class OrderView(APIView):
    """
    Класс для получения и размещения заказов пользователями
    """

    # получить мои заказы
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        orders = Order.objects.filter(
            user_id=request.user.id).exclude(state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    # разместить заказ из корзины
    def post(self, request, *args, **kwargs):
        """
            Add products to basket
        """

        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if {'id', 'contact'}.issubset(request.data):
            if request.data['id'].isdigit():
                try:
                    is_updated = Order.objects.filter(
                        user_id=request.user.id, id=request.data['id']).update(
                        contact_id=request.data['contact'],
                        state='new')
                except IntegrityError as error:
                    # print(error)
                    return JsonResponse({'Status': False, 'Errors': 'Неправильно указаны аргументы'}, statys=400)
                else:
                    if is_updated:
                        send_order.delay(
                            email=request.user.email,
                            message=f"Заказ {request.data['id']} сформирован"
                        )
                        return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    # Проставление статуса "Подтвержден"
    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if {'id', }.issubset(request.data):
            if request.data['id'].isdigit():
                orders = Order.objects.filter(
                    id=request.data['id'], state='new').prefetch_related(
                    'ordered_items__product_info', 'ordered_items__product_info__product').annotate(
                    # buyer_id=F('orders__id'),
                    update_quantity=F('ordered_items__product_info__quantity') - F('ordered_items__quantity'),
                    product_name=F('ordered_items__product_info__product__name')
                ).distinct()
                error_quantity = {}
                for order in orders:
                    if order.update_quantity < 0:
                        error_quantity[order.product_name] = f'Не хватает {abs(order.update_quantity)} штук'
                if error_quantity:
                    return JsonResponse({'Status': False, 'Errors': error_quantity})
                try:
                    is_updated = Order.objects.filter(
                        id=request.data['id']).update(
                        state='confirmed')
                except IntegrityError as error:
                    # print(error)
                    return JsonResponse({'Status': False, 'Errors': 'Неправильно указаны аргументы'})
                else:
                    if is_updated:
                        send_order.delay(
                            email=request.user.email,
                            message=f"Заказ {request.data['id']} подтвержден"
                        )

                        return JsonResponse({'Status': True})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class StorageAdminView(APIView):

    # Проставление статуса "Собран"
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if {'id', }.issubset(request.data):
            if request.data['id'].isdigit():
                order = Order.objects.filter(id=request.data['id'], state='confirmed').first()
                try:
                    is_updated = Order.objects.filter(
                        user_id=order.user_id, id=order.id).update(
                        state='assembled')
                except IntegrityError as error:
                    # print(error)
                    return JsonResponse({'Status': False, 'Errors': 'Неправильно указаны аргументы'})
                else:
                    if is_updated:
                        send_order.delay(
                            email=request.user.email,
                            message=f"Заказ {request.data['id']} собран"
                        )
                        return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    # Проставление статуса "Отправлен"
    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if {'id', }.issubset(request.data):
            if request.data['id'].isdigit():
                try:
                    is_updated = Order.objects.filter(
                        id=request.data['id'], state='assembled') \
                        .prefetch_related('ordered_items__product_info') \
                        .annotate(product_quantity=F('ordered_items__product_info__quantity') -
                                                   F('ordered_items__quantity'),
                                  product_id=F('ordered_items__product_info_id')
                                  )
                    for updated in is_updated:
                        ProductInfo.objects.filter(product_id=updated.product_id) \
                            .update(quantity=updated.product_quantity)

                except IntegrityError as error:
                    # print(error)
                    return JsonResponse({'Status': False, 'Errors': 'Неправильно указаны аргументы'})
                else:
                    if is_updated:
                        Order.objects.filter(
                            id=request.data['id'], state='assembled').update(state='sent')
                        send_order.delay(
                            email=request.user.email,
                            message=f"Заказ {request.data['id']} отправлен"
                        )
                        return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    # Проставление статуса "Доставлен"
    def patch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if {'id', }.issubset(request.data):
            if request.data['id'].isdigit():
                try:
                    is_updated = Order.objects.filter(
                        user_id=request.user.id, id=request.data['id']).update(
                        state='delivered')
                except IntegrityError as error:
                    # print(error)
                    return JsonResponse({'Status': False, 'Errors': 'Неправильно указаны аргументы'})
                else:
                    if is_updated:
                        send_order.delay(
                            email=request.user.email,
                            message=f"Заказ {request.data['id']} доставлен"
                        )
                        return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    # Удаление заказа
    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        if {'id', }.issubset(request.data):
            if request.data['id'].isdigit():
                order = Order.objects.filter(id=request.data['id']).first()
                if order and order.state in ['new', 'confirmed', 'assembled']:
                    try:
                        is_updated = Order.objects.filter(id=request.data['id']).update(
                            state='canceled')
                    except IntegrityError as error:
                        # print(error)
                        return JsonResponse({'Status': False, 'Errors': 'Неправильно указаны аргументы'})
                    else:
                        if is_updated:
                            send_order.delay(
                                email=request.user.email,
                                message=f"Заказ {request.data['id']} отменен"
                            )
                            return JsonResponse({'Status': True})
                return JsonResponse({'Status': False, 'Errors': 'Данный заказ нельзя отменить'})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})
