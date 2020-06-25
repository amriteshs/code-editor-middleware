from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, redirect
from django.utils.encoding import force_bytes,force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from core.forms import SignUpForm
from core.tokens import account_activation_token
from django.contrib.auth import login
from django.contrib.auth.models import User
import requests, json, time

permitted_languages = ["C", "CPP", "CSHARP", "CLOJURE", "CSS", "HASKELL", "JAVA", "JAVASCRIPT", "OBJECTIVEC", "PERL", "PHP", "PYTHON", "R", "RUBY", "RUST", "SCALA"]
servers = [
    {'IP': 'http://172.19.17.19:8000', 'wts': 1, 'max': 1},
    {'IP': 'http://172.19.17.19:9000', 'wts': 2, 'max': 2},
    {'IP': 'http://172.19.17.19:9001', 'wts': 3, 'max': 3},
    {'IP': 'http://172.19.17.19:9002', 'wts': 1, 'max': 1}
]
counter = -1
counter_wt = 0
request_time = 0

"""
Check if source given with the request is empty
"""
def source_empty_check(source):
  if source == "":
    response = {
      "message" : "Source can't be empty!",
    }
    return JsonResponse(response, safe=False)


"""
Check if lang given with the request is valid one or not
"""
def lang_valid_check(lang):
  if lang not in permitted_languages:
    response = {
      "message" : "Invalid language - not supported!",
    }
    return JsonResponse(response, safe=False)


"""
Handle case when at least one of the keys (lang or source) is absent
"""
def missing_argument_error():
  response = {
    "message" : "ArgumentMissingError: insufficient arguments for compilation!",
  }
  return JsonResponse(response, safe=False)


"""
Check Connectivity Error 
"""
def check_connectivity(server):
  url = server['IP'] + "/check_endpoint/"
  r = requests.get(url, timeout=30)
  if r.status_code == 200:
    return r.json()['status']
  else:
    return "Error"


def process_working_check():
  global request_time
  current = time.time()
  if current - request_time > 5:
    for server in servers:
      server['wts'] = server['max']
  request_time = current


"""
Round Robin Normal Load Balancing 
"""
def load_balancing_round_robin():
  global counter
  global servers
  counter += 1
  while check_connectivity(servers[counter % 4]) != 'Working':
    counter += 1
  return servers[counter % 4]


"""
Weighted Round Robin Load Balancing 
"""
def load_balancing_round_robin_weighted():
  global counter_wt
  global servers
  process_working_check()
  print servers[counter_wt % 4]
  if servers[counter_wt % 4]['wts'] <= 0:
    counter_wt += 1
  while check_connectivity(servers[counter_wt % 4]) != 'Working' and servers[counter_wt % 4]['wts'] <= 0:
    counter_wt += 1

  servers[counter_wt % 4]['wts'] -= 1
  return servers[counter_wt % 4]


"""
Dynamic Round Robin Load Balancing 
"""
def load_balancing_round_robin_dynamic():
  global counter_wt
  global servers
  print servers[counter_wt % 4]
  url = servers[counter_wt % 4]['IP'] + "/check_weight/"
  r = requests.get(url)
  if r.status_code != 200 or r.json()['weight'] <= 0:
    counter_wt += 1

  while check_connectivity(servers[counter_wt % 4]) != 'Working' or r.status_code != 200 or r.json()['weight'] <= 0:
    counter_wt += 1
    url = servers[counter_wt % 4]['IP'] + "/check_weight/"
    r = requests.get(url)

  print r.json()['weight']
  return servers[counter_wt % 4]


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.save()
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def editor(request):
  server = load_balancing_round_robin_dynamic()
  print server
  compile_url = server['IP'] + '/compile'
  run_url = server['IP'] + '/run'
  return render(request, 'editor.html',
                {'compile_url': compile_url,
                 'run_url': run_url})