import json
import requests
import io
import urllib, base64
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import (AutoMinorLocator, MultipleLocator)
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import render, redirect
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import RequestToHIS
from .serializers import RequestToHISSerializer
matplotlib.use('Agg')


urls = {'servers_url': "servers_url_here",
        'db_url': "db_url_here",
        'auth_url': "auth_url_here"}


def get_info():
    
    his_requests = RequestToHIS.objects.order_by('-date_time')
    ui_requests = RequestToHIS.objects.filter(source='UI').order_by('-date_time')
    service_requests = RequestToHIS.objects.filter(source='service').order_by('-date_time')

    current_dt = timezone.localtime(timezone.now()).replace(second=0, microsecond=0)
    
    latest_requests = {}
    hour_requests = {}
    h_ui_requests = {}
    h_service_requests = {}
    
    if his_requests:
        starting = his_requests[0].date_time.replace(second=0, microsecond=0)
        for delta in range(60, -1, -1):
            startdate = starting - timedelta(minutes = delta)
            delta_requests = RequestToHIS.objects.filter(date_time__range = [startdate, startdate + timedelta(minutes = 1)])
            request_label = startdate + timedelta(hours = 3)
            latest_requests[request_label.strftime("%H:%M")] = delta_requests.count()

    for delta in range(60, -1, -1):

        startdate = current_dt - timedelta(minutes = delta)
        delta_requests = RequestToHIS.objects.filter(date_time__range = [startdate, startdate + timedelta(minutes = 1)])
        hour_requests[startdate.strftime("%H:%M")] = delta_requests.count()

        ui_delta_requests = delta_requests.filter(source='UI')
        h_ui_requests[startdate.strftime("%H:%M")] = ui_delta_requests.count()
        
        service_delta_requests = delta_requests.filter(source='service')
        h_service_requests[startdate.strftime("%H:%M")] = service_delta_requests.count()
    
    plt.gcf().clear()
    
    fig, axs = plt.subplots(2, 2, figsize=(8, 8), sharey=False)

    axs[(0, 0)].bar(latest_requests.keys(), latest_requests.values(), width=0.9, align='edge')
    axs[(0, 1)].bar(hour_requests.keys(), hour_requests.values(), width=0.9, align='edge')
    axs[(1, 0)].bar(h_ui_requests.keys(), h_ui_requests.values(), width=0.9, align='edge')
    axs[(1, 1)].bar(h_service_requests.keys(), h_service_requests.values(), width=0.9, align='edge')
    
    axs[(0, 0)].set_title('Latest requests')
    axs[(0, 1)].set_title('Last hour requests')
    axs[(1, 0)].set_title('Last hour UI requests')
    axs[(1, 1)].set_title('Last hour service requests')

    for i, ax in enumerate(axs.flat):
        ax.xaxis.set_major_locator(MultipleLocator(10))
        ax.yaxis.set_major_locator(MultipleLocator(1))
        ax.xaxis.set_minor_locator(AutoMinorLocator(8))
        ax.yaxis.set_minor_locator(AutoMinorLocator(8))
        ax.grid(which='minor', alpha=0.2)
        ax.grid(which='major', alpha=0.5)

        ax.set_ylim(0, max(5, ax.get_ylim()[1]))
        ax.set(xlabel='time', ylabel='requests')
        
        for tick in ax.get_xticklabels():
            tick.set_rotation(60)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi = 300)
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri =  urllib.parse.quote(string)
    
    return his_requests, ui_requests, service_requests, uri

def index(request):
    his_requests, ui_requests, service_requests, uri = get_info()
    global urls
    servers_st = request.session.get('servers_url_st')
    db_st = request.session.get('db_url_st')
    servers_url = urls['servers_url']
    db_url = urls['db_url']
    
    return render(
        request,
        'index.html',
         context={'num_requests': his_requests.count(), 'his_requests': his_requests, 
                  'ui_requests': ui_requests, 'service_requests': service_requests, 
                  'servers_url': servers_url, 'db_url': db_url,
                  'plot': uri, 'servers_st': servers_st, 'db_st': db_st},
    )

def change_urls(request):
    if request.method == 'POST':
        form = request.POST
        global urls
        print('old', urls)
        if form['servers_url']:
            urls['servers_url'] = form['servers_url']
            request.session['servers_url'] = form['servers_url']
            print('new', urls['servers_url'])
        if form['db_url']:
            urls['db_url'] = form['db_url']
            request.session['db_url'] = form['db_url']
            print('new', urls['db_url'])
        return redirect(request.META['HTTP_REFERER'])

def do_request(request, url, headers=None, source='', view_url='', method='GET'):
    if not headers:
        headers = {'Content-Type': 'application/json'}
    his_request = RequestToHIS(source=source, url=view_url, method=method)
    his_request.save()
    if method == 'GET':
        r = requests.get(url, data=json.dumps(request.data), headers=headers)
    else:
        r = requests.post(url, data=json.dumps(request.data), headers=headers)
    answer = r.json()
    return answer


def check(request, url):
    if request.method == 'GET':
        global urls
        check_url = urls[url]
        if url == 'db_url':
            check_url += '/db_manager'
        st = post_check(check_url + '/check')
        request.session[url + '_st'] = st
        return redirect(request.META['HTTP_REFERER'])  # , args=(st,))

def post_check(url):
    headers = {'Content-Type': 'application/json'}
    r = requests.post(url, data=json.dumps({}), headers=headers)
    return r.status_code == 200

@api_view(['GET', 'POST'])
def resource(request):
    global urls
    if request.method == 'GET':
        answer = do_request(request, urls['db_url'] + "/db_manager/db_request/", source='service', view_url='resource', 'GET')
    else:
        answer = do_request(request, urls['db_url'] + "/db_manager/post_resource/", source='service', view_url='resource', 'POST')
    return Response(answer)

@api_view(('POST',))
def auth_request(request):
    global urls
    answer = do_request(request, urls['auth_url'] + "/login", source='UI', view_url='auth_request', method='POST')
    return Response(answer)

@api_view(['GET', 'POST'])
def patient(request):
    global urls
    answer = do_request(request, urls['servers_url'] + "/patient", source='UI', view_url='patient', method=request.method)
    return Response(answer)

@api_view(['GET', 'POST'])
def observations(request):
    global urls
    answer = do_request(request, urls['servers_url'] + "/observations", source='UI', view_url='observations', method=request.method)
    return Response(answer)

@api_view(['GET', 'POST'])
def diagnoses(request):
    global urls
    answer = do_request(request, urls['servers_url'] + "/diagnoses", source='UI', view_url='diagnoses', method=request.method)
    return Response(answer)

@api_view(['GET', 'POST'])
def medications(request):
    global urls
    answer = do_request(request, urls['servers_url'] + "/medications", source='UI', view_url='medications', method=request.method)
    return Response(answer)

@api_view(['GET', 'POST'])
def appointment(request):
    global urls
    if request.method == 'GET':
        answer = do_request(request, urls['servers_url'] + "/get_appointments", source='UI', view_url='appointments', method='GET')
    else:
        answer = do_request(request, urls['servers_url'] + "/post_appointment", source='UI', view_url='appointment', method='POST')
    return Response(answer)

@api_view(('GET',))
def slots(request):
    global urls
    answer = do_request(request, urls['servers_url'] + "/slots", source='UI', view_url='slots', method='GET')
    return Response(answer)


class RequestToHISView(APIView):
    def get(self, request):
        his_requests = RequestToHIS.objects.all()
        serializer = RequestToHISSerializer(his_requests, many=True)
        return Response({"his_requests": serializer.data})
    
    def post(self, request):
        data=request.data
        his_request = RequestToHIS(source='Gateway', url='his_requests')
        his_request.save()
        return Response({"success": "Request received successfully"})


def update(request):
    if request.method == 'GET':
        return render(None, 'index.html')
