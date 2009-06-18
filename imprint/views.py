# -*- coding: utf-8 -*-
from django.contrib.auth.forms import *
from django.http import HttpResponseRedirect
from django_authopenid.forms import *
from utils import renders

@renders('authopenid/profile.html')
def account_profile(request):
    form1 = OpenidSigninForm()
    form2 = AuthenticationForm()
    return locals()

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
