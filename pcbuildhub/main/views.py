from django.shortcuts import render

def main_page(request):
    return render(request, 'home.html')