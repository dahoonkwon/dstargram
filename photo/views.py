import logging
import os
from datetime import timezone

from botocore.exceptions import ClientError
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic import DetailView

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Photo
from pathlib import Path

import boto3
from config import settings as st

# Create your views here.

@login_required
def photo_list(request):
    photos = Photo.objects.all()
    return render(request, 'photo/list.html', {'photos':photos})

def upload_file(ACCESS_ID, ACCESS_KEY, file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3',
                            aws_access_key_id=ACCESS_ID,
                            aws_secret_access_key=ACCESS_KEY)
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

class PhotoUploadView(LoginRequiredMixin, CreateView):
    model = Photo
    fields = ['photo', 'text']
    template_name = 'photo/upload.html'

    def form_valid(self, form):
        form.instance.author_id = self.request.user.id
        if form.is_valid():
            form.instance.save()
            return redirect('/')
        else:
            return self.render_to_response({'form':form})

class PhotoDeleteView(LoginRequiredMixin, DeleteView):
    model = Photo
    success_url = '/'
    template_name = 'photo/delete.html'

class PhotoUpdateView(LoginRequiredMixin, UpdateView):
    model = Photo
    fields = ['photo', 'text']
    template_name = 'photo/update.html'

class PhotoDetailView(LoginRequiredMixin, DetailView):
    model = Photo
    fields = ['photo', 'text']
    template_name = 'photo/detail.html'

    def get_object(self):
        ACCESS_ID = st.AWS_ACCESS_KEY_ID
        ACCESS_KEY = st.AWS_SECRET_ACCESS_KEY
        BUCKETNAME = st.AWS_STORAGE_BUCKET_NAME
        obj = super().get_object()
        selectImg = 'media/' + str(obj.photo)
        s3 = boto3.resource('s3',
                            aws_access_key_id=ACCESS_ID,
                            aws_secret_access_key=ACCESS_KEY)
        my_bucket = s3.Bucket(BUCKETNAME)
        imgCheck = False
        for file in my_bucket.objects.all():
            if selectImg == file.key:
                imgCheck = True

        if imgCheck == True:
            print('서버에 이미지가 있어')
        else:
            upload_file(ACCESS_ID, ACCESS_KEY,selectImg, BUCKETNAME)
            print('서버에 이미지 업로드가 필요해')
        return obj