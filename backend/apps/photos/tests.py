import uuid
from django.test import TestCase
from django.urls import reverse

from .models import Photo


class PhotosViewsTests(TestCase):
    def test_photo_list_ok(self):
        Photo.objects.create(
            id=uuid.uuid4(),
            file_path=r'D:\does-not-exist\1.jpg',
            hash_md5='a' * 32,
        )
        response = self.client.get(reverse('photo_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)

    def test_photo_serve_missing_file_404(self):
        photo = Photo.objects.create(
            id=uuid.uuid4(),
            file_path=r'D:\does-not-exist\2.jpg',
            hash_md5='b' * 32,
        )
        response = self.client.get(reverse('photo_serve', kwargs={'pk': photo.pk}))
        self.assertEqual(response.status_code, 404)

    def test_photo_detail_ok(self):
        photo = Photo.objects.create(
            id=uuid.uuid4(),
            file_path=r'D:\does-not-exist\3.jpg',
            hash_md5='c' * 32,
        )
        response = self.client.get(reverse('photo_detail', kwargs={'pk': photo.pk}))
        self.assertEqual(response.status_code, 200)

    def test_photo_video_missing_404(self):
        photo = Photo.objects.create(
            id=uuid.uuid4(),
            file_path=r'D:\does-not-exist\4.jpg',
            hash_md5='d' * 32,
        )
        response = self.client.get(reverse('photo_video_serve', kwargs={'pk': photo.pk}))
        self.assertEqual(response.status_code, 404)
