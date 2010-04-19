from archive.models import *
from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from utils import renders, dates, imagemagick, send_file
import os.path

def generate_page_thumbnail(page):
    abs_thumb = os.path.join(settings.MEDIA_ROOT, page.thumbnail_path)
    if not os.path.exists(abs_thumb):
        if page.page_to == page.page_from + 1: # spread
            abs_page = page.file.path + '[0-1]'
            dims = '400x200'
        else:
            abs_page = page.file.path + '[0]'
            dims = '200x200'
        imagemagick('convert', '-thumbnail', dims, abs_page, abs_thumb)
    return settings.MEDIA_URL + page.thumbnail_path

@renders('archive/pdfissue_index.html')
def archive_index(request):
    object_list = PDFIssue.objects.select_pub()
    return locals()

@renders('archive/pdfissue_year.html')
def archive_year(request, year):
    object_list = PDFIssue.objects.select_pub().filter(date__year=int(year))
    return locals()

@renders('archive/pdfissue_month.html')
def archive_month(request, year, month):
    try:
        m = dates.MONTHS_3_REV[month]
    except KeyError:
        raise Http404
    object_list = PDFIssue.objects.select_pub().filter(
            date__year=int(year), date__month=m)
    month = datetime.date(2010, m, 01).strftime('%B')
    return locals()

@renders('archive/pdfissue_detail.html')
def pdfissue_detail(request, y, m, d, pub):
    try:
        object = PDFIssue.objects.get_by_date_and_publication(y, m, d, pub)
    except PDFIssue.DoesNotExist:
        raise Http404
    object_list = object.pages.all()
    if object.issue:
        issue = object.issue
    if object_list.count() == 1:
        return redirect(object_list[0])
    return locals()

def pdfissue_thumbnail(request, y, m, d, pub):
    try:
        object = PDFIssue.objects.get_by_date_and_publication(y, m, d, pub)
        first_page = object.pages.get(page_from=1)
    except (PDFIssue.DoesNotExist, PDFFile.DoesNotExist):
        raise Http404
    return send_file(generate_page_thumbnail(first_page))

def get_pdf_file(pdfissue, page):
    try:
        return PDFFile.objects.get(pdfissue=pdfissue, page_from=page)
    except PDFFile.DoesNotExist:
        return PDFFile.objects.get(pdfissue=pdfissue, page_from__le=page,
                page_to__ge=page)

def pdfpage_detail(request, y, m, d, pub, page):
    try:
        pdfissue = PDFIssue.objects.get_by_date_and_publication(y, m, d, pub)
        page = get_pdf_file(pdfissue, page)
    except (PDFIssue.DoesNotExist, PDFFile.DoesNotExist):
        return Http404
    return send_file(page.file.url)

def pdfpage_thumbnail(request, y, m, d, pub, page):
    try:
        pdfissue = PDFIssue.objects.get_by_date_and_publication(y, m, d, pub)
        page = get_pdf_file(pdfissue, page)
    except (PDFIssue.DoesNotExist, PDFFile.DoesNotExist):
        raise Http404
    return send_file(generate_page_thumbnail(page))

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
