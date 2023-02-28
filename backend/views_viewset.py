from django.db import IntegrityError
from rest_framework import viewsets, permissions
from django.db.models import Q, Sum, F
from rest_framework.decorators import action
from rest_framework.response import Response
from ujson import loads as load_json

from backend.models import Order, OrderItem
from backend.serializers import OrderSerializer, OrderItemSerializer
from django.http import JsonResponse


class BasketViewSet(viewsets.ModelViewSet):
    """
        Класс для работы с корзиной пользователя через ViewSet

    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = [OrderSerializer, OrderItemSerializer, ]

    def create(self, request, *args, **kwargs):
        items_sting = request.data.get('items')
        print(request.user.id)
        if items_sting:
            try:
                items_dict = load_json(items_sting)
            except ValueError:
                JsonResponse({'Status': False, 'Errors': 'Неверный формат запроса'})
            else:
                queryset = self.get_queryset()
                objects_created = 0
                for order_item in items_dict:
                    order_item.update({'order': queryset[0].id})
                    serializer = self.get_serializer(data=order_item)
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

    @action(methods=['put'], detail=False, url_path='update')
    def update_basket(self, request):
        items_sting = request.data.get('items')
        if items_sting:
            try:
                items_dict = load_json(items_sting)
            except ValueError:
                JsonResponse({'Status': False, 'Errors': 'Неверный формат запроса'})
            else:
                queryset = self.get_queryset()
                objects_updated = 0
                for order_item in items_dict:
                    if type(order_item['id']) == int and type(order_item['quantity']) == int:
                        request.data._mutable = True
                        request.data['id'] = order_item['id']
                        request.data['quantity'] = order_item['quantity']
                        objects_updated += OrderItem.objects.filter(order_id=queryset[0].id,
                                                                    id=order_item['id'])\
                            .update(quantity=order_item['quantity'])

                return JsonResponse({'Status': True, 'Обновлено объектов': objects_updated})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)

    @action(methods=['delete'], detail=False, url_path='delete')
    def destroy_product(self, request):
        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            queryset = self.get_queryset()
            query = Q()
            objects_deleted = False
            for order_item_id in items_list:
                if order_item_id.isdigit():
                    query = query | Q(order_id=queryset[0].id, id=order_item_id)
                    objects_deleted = True

            if objects_deleted:
                deleted_count = OrderItem.objects.filter(query).delete()[0]
                return JsonResponse({'Status': True, 'Удалено объектов': deleted_count})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)

    def list(self, request, *args, **kwargs):
        queryset = Order.objects.filter(user_id=self.request.user.id, state='basket').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self,  *args, **kwargs):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return Order.objects.none()
        return Order.objects.get_or_create(user_id=self.request.user.id, state='basket')

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            return OrderSerializer(*args, **kwargs)
        elif self.action == 'create':
            return OrderItemSerializer(*args, **kwargs)
        else:
            return JsonResponse({'Status': False, 'Errors': 'Метод не разрешен'}, status=405)
