from django.shortcuts import render

def upgrade_build_home(request):
    return render(request, 'upgrade.html')