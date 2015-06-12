# -*- coding: utf-8 -*-
from django.contrib.auth.models import User, Group
from pos.models import Table, Product, Category, Employee, Order, OrderItem

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from rest_framework import viewsets
from pos.serializers import EmployeeSerializer, UserSerializer, GroupSerializer, TableSerializer, ProductSerializer, CategorySerializer, OrderSerializer, OrderItemSerializer

from django import template
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, JsonResponse
from django.db import models
from django.db.models import Q, Count, Sum

from datetime import datetime, timedelta
import time
from django.utils import timezone
import csv

try:
    from printer import printReport
except:
    pass


"""
class AuthView(APIView):
    authentication_classes = (QuietBasicAuthentication,)

    def post(self, request, *args, **kwargs):
        login(request, request.user)
        return Response(UserSerializer(request.user).data)

    def delete(self, request, *args, **kwargs):
        logout(request)
        return Response({})
"""
class EmployeeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

class TableViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Table.objects.all()
    serializer_class = TableSerializer

class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows products to be viewed or edited.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows categories to be viewed or edited.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows products to be viewed or edited.
    """
    queryset = Order.objects.filter(status=False)
    serializer_class = OrderSerializer

class OrderItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows products to be viewed or edited.
    """
    queryset = OrderItem.objects.all().filter(order__status=False)
    serializer_class = OrderItemSerializer

def pos(request):
    return render(request, 'pos/index.html')

def test_app(request):
    return render(request, 'pos/login.html')

def auth(request):
    return render(request, 'pos/auth.html')

def pos_op(request):
    return render(request, 'pos/pos_op.html')

def kitchen(request):
    return render(request, 'pos/kitchen.html')

def skara(request):
    return render(request, 'pos/grill.html')

def bar(request):
    return render(request, 'pos/bar.html')

def report(request):
    d_from = datetime.now()
    if request.GET.has_key('date'):
        d_from = datetime.strptime(request.GET['date'], '%Y-%m-%d')

    d_from = d_from + timedelta(hours=9)
    d_to = d_from + timedelta(hours=24)

    orders = models.get_model('pos', 'Order').objects.all().filter(closed__gt=d_from).filter(closed__lt=d_to)

    total2 = 0
    oitems = models.get_model('pos', 'OrderItem').objects.all();
    for o in orders:
        items = oitems.filter(order_id=o.id)
        for oi in items:
            total2 += oi.quantity * oi.product.price

    items = models.get_model('pos', 'OrderItem').objects.all().filter(changed__gt=d_from).filter(changed__lt=d_to)
    orderItems = items.values('product__name', 'product__description', 'product__price').annotate(dcount=Sum('quantity'))

    total = 0
    discounts = 0
    for o in orders:
        total += o.total
        if o.discount > 0:
            perc = (100-o.discount)
            if perc == 0: perc = 1
            discounts += o.total/perc - o.total

    print total2, total

    c = template.RequestContext(request, {
        'today' : d_from.strftime('%d-%m-%Y'),
        'orders' : orders,
        'total' : total,
        'orderItems' : orderItems,
        'discounts': str("{0:.2f}".format(total2-total))
    })

    return render_to_response(['pos/report.html'], c)

def report_service(request):
    d_from = datetime.now()
    w = None
    if request.GET.has_key('date'):
        d_from = datetime.strptime(request.GET['date'], '%Y-%m-%d')

    if request.GET.has_key('w'):
        w = request.GET['w']

    d_from = d_from + timedelta(hours=9)
    d_to = d_from + timedelta(hours=24)

    orders = models.get_model('pos', 'Order').objects.all().filter(closed__gt=d_from).filter(closed__lt=d_to)
    orders = orders.filter(operatedBy=w).order_by('closed')

    oitems = models.get_model('pos', 'OrderItem').objects.all();
    for o in orders:
        items = oitems.filter(order_id=o.id)
        o.orderItems = items
        o.total2 = 0
        for oi in items:
            o.total2 += oi.quantity * oi.product.price


    #orderItems = models.get_model('pos', 'OrderItem').objects.all().filter(changed__gt=d_from).filter(changed__lt=d_to).values('product__name', 'product__price').annotate(dcount=Count('product__name'))

    waiters = models.get_model('auth', 'user').objects.all()

    total = 0
    discounts = 0
    for o in orders:
        total += o.total
        if o.discount > 0:
            perc = (100-o.discount)
            if perc == 0: perc = 1
            discounts += o.total/perc - o.total

    c = template.RequestContext(request, {
        'today' : d_from.strftime('%d-%m-%Y'),
        'orders' : orders,
        'total' : total,
        'discounts': str("{0:.2f}".format(discounts)),
        'waiters' : waiters
    })

    return render_to_response(['pos/report_service.html'], c)

def current_report(request):
    w = None

    if request.GET.has_key('w'):
        w = request.GET['w']

    if w == None: return JsonResponse({'error':True, 'message': u'missing user'})

    orders = models.get_model('pos', 'Order').objects.all()
    orders = orders.filter(operatedBy=w).filter(reported=False)

    waiter = models.get_model('auth', 'user').objects.all().get(id=int(w))

    total = 0
    for o in orders:
        if o.status == False:
            return JsonResponse({'error':True, 'message': u'opened orders'})
        total += o.total

    dt = timezone.now()
    dt = datetime(dt.year, dt.month, dt.day)

    return JsonResponse({'total':total, 'error': False, 'count': len(orders), 'date': dt})

def generate_current_report(request):
    w = None

    if request.GET.has_key('w'):
        w = request.GET['w']

    if w == None: return JsonResponse({'error':True, 'message': u'missing user'})

    orders = models.get_model('pos', 'Order').objects.all()
    orders = orders.filter(operatedBy=w).filter(reported=False)

    waiter = models.get_model('auth', 'user').objects.all().get(id=int(w))

    total = 0
    for o in orders:
        if o.status == False:
            return JsonResponse({'error':True, 'message': u'opened orders'})
        total += o.total

    error = False
    details = None

    try:
        printReport(waiter.first_name, total)
    except Exception, err:
        error = True
        details = 'printer error'

        #return JsonResponse({'error':True, 'message': u'printer problems', 'details': err})
        pass

    dt = timezone.now()
    dt = datetime(dt.year, dt.month, dt.day)

    for o in orders:
        o.reported = True
        o.reportedDate = dt
        o.save()

    return JsonResponse({'total':total, 'error': error, 'count': len(orders), 'details': details})    

def waiter_reports(request):
    w = None

    if request.GET.has_key('w'):
        w = request.GET['w']

    if w == None: return JsonResponse({'error':True, 'message': u'missing user'})

    waiter = models.get_model('pos', 'employee').objects.all().get(id=int(w))

    orders = models.get_model('pos', 'Order').objects.all().filter(operatedBy=waiter.user.id).values('reportedDate').annotate(reportDate=Count('reportedDate'))

    return JsonResponse({'error': False, 'reports': map(lambda o: o['reportedDate'], orders), 'name': waiter.user.username})

def daily_waiter_report(request):
    w = None
    d = None

    if request.GET.has_key('w'):
        w = request.GET['w']

    if w == None: return JsonResponse({'error':True, 'message': u'missing user'})

    if request.GET.has_key('d'):
        d = request.GET['d']

    waiter = models.get_model('pos', 'employee').objects.all().get(id=int(w))

    if d == None: return JsonResponse({'error':True, 'message': u'missing date'})

    try:
        d = datetime.strptime(d, "%Y-%m-%dT%H:%M:%S")
    except:
        return JsonResponse({'error':True, 'message': u'invalid date'})

    orders = models.get_model('pos', 'Order').objects.all().filter(operatedBy=waiter.user.id).filter(reportedDate=d)    

    total = sum(map(lambda o: o.total, orders))

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="report_orders_%s_%s.csv"' % (d.strftime('%Y_%m_%d'), waiter.user.first_name.encode('utf-8', 'ignore'))
    writer = csv.writer(response)
    writer.writerow([u'Маса'.encode('utf-8', 'ignore'), u'Серв.'.encode('utf-8', 'ignore'), u'Дата'.encode('utf-8', 'ignore'), u'Общо Цена'.encode('utf-8', 'ignore')])
    writer.writerow(["","", "", ""])

    for order in orders:
        writer.writerow([order.table.nickname.encode('utf-8', 'ignore'), order.operatedBy.first_name.encode('utf-8', 'ignore'), order.closed, order.total])

    writer.writerow(["","", "", ""])
    writer.writerow(["","", "", ""])
    
    writer.writerow([u'Тотал'.encode('utf-8', 'ignore'),"", "", total])

    return response


def report_waiter(request):
    w = None

    if request.GET.has_key('w'):
        w = request.GET['w']

    if w == None: return render(request, 'pos/empty.html')

    orders = models.get_model('pos', 'Order').objects.all()
    orders = orders.filter(operatedBy=w).filter(reported=False)

    waiter = models.get_model('auth', 'user').objects.all().get(id=int(w))

    total = 0
    for o in orders:
        if o.status == False:
            return render(request, 'pos/error.html')
        total += o.total

    try:
        printReport(waiter.first_name, total)
    except Exception, err:
        c = template.RequestContext(request, {
            'error' : err
        })

        return render_to_response(['pos/print-error.html'], c)
        pass

    for o in orders:
        o.reported = True
        o.save()

    return render(request, 'pos/empty.html')

def report_all(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="report_products.csv"'
    writer = csv.writer(response)
    writer.writerow([u'Продукт'.encode('utf-8', 'ignore'), u'Общо продадени'.encode('utf-8', 'ignore'), u'Единична Цена'.encode('utf-8', 'ignore'), u'Общо Цена'.encode('utf-8', 'ignore')])


    products = models.get_model('pos', 'Product').objects.all();
    for product in products:
        orderitems = models.get_model('pos', 'OrderItem').objects.filter(product=product)
        sum = 0
        price = 0
        for orderitem in orderitems:
            sum = sum + orderitem.quantity
            price = price + orderitem.quantity*product.price

        product.orderCount = sum
        product.totalPrice = price

        name = product.name.encode('utf-8', 'ignore')

        writer.writerow([name, sum, product.price, price])


    return response



def report_csv(request):
    d_from = datetime.now()
    if request.GET.has_key('date'):
        d_from = datetime.strptime(request.GET['date'], '%Y-%m-%d')

    d_from = d_from + timedelta(hours=9)
    d_to = d_from + timedelta(hours=24)

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="report_quantities.csv"'

    items = models.get_model('pos', 'OrderItem').objects.all().filter(changed__gt=d_from).filter(changed__lt=d_to).order_by('product__name')
    orderItems = items.values('product__name', 'product__description', 'product__price').annotate(dcount=Sum('quantity'))

    writer = csv.writer(response)
    writer.writerow([u'Item', u'Count', u'Price'])

    for oi in orderItems:
        product = oi['product__name'].encode('utf-8', 'ignore')
        if oi['product__description'] != None and len(oi['product__description']) > 0:
            product += '-' + oi['product__description'].encode('utf-8', 'ignore')
        writer.writerow([product, oi['dcount'], oi['product__price']])

    writer.writerow([u''])


    orders = models.get_model('pos', 'Order').objects.all().filter(closed__gt=d_from).filter(closed__lt=d_to)

    total = 0
    discounts = 0
    for o in orders:
        total += o.total
        if o.discount > 0:
            perc = (100-o.discount)
            if perc == 0: perc = 1
            discounts += o.total/perc - o.total

    total2 = 0
    for oi in items:
        total2 += oi.quantity * oi.product.price

    writer.writerow([u'Turnover', u'Discounts'])
    writer.writerow([total, str("{0:.2f}".format(total2-total))])

    return response