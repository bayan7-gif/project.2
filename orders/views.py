from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)
from .forms import OrderForm
from .models import Order
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from .serializers import OrderSerializer
from django.core.exceptions import ValidationError
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


class OrderViewSet(viewsets.ModelViewSet):
    """
    Набор представлений для работы с заказами через API.

    Attributes:
        queryset (QuerySet): Набор всех заказов.
        serializer_class (Serializer): Сериализатор для Order.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Кастомное действие для поиска заказов.

        Args:
            request (Request): HTTP-запрос.

        Returns:
            Response: Список найденных заказов.
        """
        query = request.query_params.get('q', '')
        status_filter = request.query_params.get('status', '')

        orders = Order.objects.all()

        if query:
            orders = orders.filter(table_number__icontains=query)
        if status_filter:
            orders = orders.filter(status=status_filter)

        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Переопределение создания заказа через API.

        Args:
            request (Request): HTTP-запрос.

        Returns:
            Response: Результат операции.
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers,
            )
        except Exception as e:
            logger.error(f"Ошибка создания заказа: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def update(self, request, *args, **kwargs):
        """
        Переопределение обновления заказа через API.

        Args:
            request (Request): HTTP-запрос.

        Returns:
            Response: Результат операции.
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(
                instance,
                data=request.data,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Ошибка обновления заказа: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


def create_order(request):
    """Страница создания заказа."""
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            try:
                order = form.save(commit=False)
                order.full_clean()
                order.save()
                return redirect('order_list')
            except ValidationError as e:
                form.add_error(None, str(e))
    else:
        form = OrderForm()

    return render(
        request,
        'orders/create_order.html',
        {'form': form},
    )


def order_list(request):
    """Страница со списком заказов."""
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')

    orders = Order.objects.all()

    if query:
        orders = orders.filter(table_number__icontains=query)
    if status_filter:
        orders = orders.filter(status=status_filter)

    return render(
        request,
        'orders/order_list.html',
        {
            'orders': orders,
            'query': query,
            'status_filter': status_filter,
        },
    )


def delete_order(request, pk):
    """Страница подтверждения удаления заказа."""
    try:
        order = Order.objects.get(pk=pk)
    except Order.DoesNotExist:
        return render(
            request,
            'orders/error.html',
            {'message': 'Заказ не найден.'},
        )

    if request.method == 'POST':
        order.delete()
        return redirect('order_list')

    return render(
        request,
        'orders/delete_order.html',
        {'order': order},
    )


def update_order(request, pk):
    """Страница редактирования заказа."""
    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('order_list')
    else:
        form = OrderForm(instance=order)

    return render(
        request,
        'orders/update_order.html',
        {'form': form},
    )


def revenue_report(request):
    """Страница отчета по выручке."""
    paid_orders = Order.objects.filter(status='paid')
    total_revenue = sum(
        order.total_price or 0 for order in paid_orders
    )
    return render(
        request,
        'orders/revenue_report.html',
        {
            'total_revenue': total_revenue,
            'paid_orders': paid_orders,
        },
    )