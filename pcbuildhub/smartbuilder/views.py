from django.shortcuts import render

def smart_builder_home(request):
    return render(request, 'smartbuild.html')
