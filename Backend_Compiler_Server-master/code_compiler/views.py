#!/usr/bin/env python


from django.shortcuts import render
from django.http import JsonResponse, HttpResponseForbidden

import requests, json, os, time

COMPILE_URL = "https://api.hackerearth.com/v3/code/compile/"
RUN_URL = "https://api.hackerearth.com/v3/code/run/"
WEIGHTS = int(os.environ['wts'])
REQUEST_TIME = 0

# access config variable
DEBUG = True
# DEBUG = (os.environ.get('code_compiler_DEBUG') or "").lower() == "true"
CLIENT_SECRET = "6d8030a11f214894330cb039194c762072547560"

permitted_languages = ["C", "CPP", "CSHARP", "CLOJURE", "CSS", "HASKELL", "JAVA", "JAVASCRIPT", "OBJECTIVEC", "PERL", "PHP", "PYTHON", "R", "RUBY", "RUST", "SCALA"]


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
Check connectivity
"""
def check_connectivity_endpoint(request):
  response = {
    "status": "Working"
  }
  return JsonResponse(response, safe=False)


"""
Calculate weights
"""
def check_weight(request):
  global REQUEST_TIME
  global WEIGHTS
  print WEIGHTS
  current = time.time()
  print current - REQUEST_TIME
  if current - REQUEST_TIME > 10:
    WEIGHTS = int(os.environ['wts'])
  response = {
    "weight": WEIGHTS
  }
  return JsonResponse(response, safe=False)


"""
Method catering to AJAX call at /ide/compile/ endpoint,
makes call at HackerEarth's /compile/ endpoint and returns the compile result as a JsonResponse object
"""
def compileCode(request):
  global CLIENT_SECRET
  global COMPILE_URL
  global WEIGHTS
  global REQUEST_TIME
  WEIGHTS -= 1
  REQUEST_TIME = time.time()
  if request.method == 'POST':
    global CLIENT_SECRET
    global COMPILE_URL
    try:
      source = request.POST['source']
      # Handle Empty Source Case
      source_empty_check(source)

      lang = request.POST['lang']
      # Handle Invalid Language Case
      lang_valid_check(lang)

    except KeyError:
      # Handle case when at least one of the keys (lang or source) is absent
      missing_argument_error()

    else:
      compile_data = {
        'client_secret': CLIENT_SECRET,
        'async': 0,
        'source': source,
        'lang': lang,
      }

      r = requests.post(COMPILE_URL, data=compile_data, verify=False)
      print r.json()
      return JsonResponse(r.json(), safe=False)
  else:
    return HttpResponseForbidden();


"""
Method catering to AJAX call at /ide/run/ endpoint,
makes call at HackerEarth's /run/ endpoint and returns the run result as a JsonResponse object
"""
def runCode(request):
  global CLIENT_SECRET
  global RUN_URL  
  global WEIGHTS
  global REQUEST_TIME
  WEIGHTS -= 1
  REQUEST_TIME = time.time()
  if request.method == 'POST':
    global CLIENT_SECRET
    global COMPILE_URL
    try:
      source = request.POST['source']
      # Handle Empty Source Case
      source_empty_check(source)

      lang = request.POST['lang']
      # Handle Invalid Language Case
      lang_valid_check(lang)

    except KeyError:
      # Handle case when at least one of the keys (lang or source) is absent
      missing_argument_error()

    else:
      # default value of 5 sec, if not set
      time_limit = request.POST.get('time_limit', 5)
      # default value of 262144KB (256MB), if not set
      memory_limit = request.POST.get('memory_limit', 262144)

      run_data = {
        'client_secret': CLIENT_SECRET,
        'async': 0,
        'source': source,
        'lang': lang,
        'time_limit': time_limit,
        'memory_limit': memory_limit,
      }

      # if input is present in the request
      code_input = ""
      if 'input' in request.POST:
        run_data['input'] = request.POST['input']
        code_input = run_data['input']

      """
      Make call to /run/ endpoint of HackerEarth API
      and save code and result in database
      """
      r = requests.post(RUN_URL, data=run_data, verify=False)
      r = r.json()
      cs = ""
      rss = ""
      rst = ""
      rsm = ""
      rso = ""
      rsstdr = ""
      try:
        cs = r['compile_status']
      except:
        pass
      try:
        rss=r['run_status']['status']
      except:
        pass
      try:
        rst = r['run_status']['time_used']
      except:
        pass
      try:
        rsm = r['run_status']['memory_used']
      except:
        pass
      try:
        rso = r['run_status']['output_html']
      except:
        pass
      try:
        rsstdr = r['run_status']['stderr']
      except:
        pass

      return JsonResponse(r, safe=False)
  else:
    return HttpResponseForbidden()
