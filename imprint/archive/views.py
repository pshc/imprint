from archive.models import *
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, redirect
from utils import renders, dates

@renders('archive/pdfissue_index.html')
def archive_index(request):
    object_list = PDFIssue.objects.all()
    return locals()

@renders('archive/pdfissue_year.html')
def archive_year(request, year):
    object_list = PDFIssue.objects.filter(date__year=int(year))
    return locals()

@renders('archive/pdfissue_month.html')
def archive_month(request, year, month):
    try:
        m = dates.MONTHS_3_REV[month]
    except KeyError:
        raise Http404
    object_list = PDFIssue.objects.filter(date__year=int(year), date__month=m)
    month = datetime.date(2010, m, 01).strftime('%B')
    return locals()

@renders('archive/pdfissue_detail.html')
def pdfissue_detail(request, y, m, d, pub):
    try:
        pub = Publication.objects.get(slug=pub)
        object = PDFIssue.objects.get_by_date_and_publication(y, m, d, pub)
    except (Publication.DoesNotExist, PDFIssue.DoesNotExist):
        raise Http404
    object_list = object.pages.all()
    if object.issue:
        issue = object.issue
    if object_list.count() == 1:
        return redirect(object_list[0])
    return locals()

@renders('archive/pdfpage_detail.html')
def pdfpage_detail(request, y, m, d, pub, page):
    try:
        pub = Publication.objects.get(slug=pub)
        pdfissue = PDFIssue.objects.get_by_date_and_publication(y, m, d, pub)
        try:
            object = PDFFile.objects.get(pdfissue=pdfissue, page_from=page)
        except PDFFile.DoesNotExist:
            object = PDFFile.objects.get(pdfissue=pdfissue, page_from__le=page,
                    page_to__ge=page)
    except (Publication.DoesNotExist, PDFIssue.DoesNotExist,
            PDFFile.DoesNotExist):
        return Http404
    return HttpResponsePermanentRedirect(object.file.url)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
