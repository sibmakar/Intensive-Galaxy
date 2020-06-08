from django.test import TestCase
from main import models
from django.core.files.images import ImageFile
from decimal import Decimal


class TestSignal(TestCase):
    def test_thumbnails_are_generated_on_product_save(self):
        product = models.Product(name="Harry Potter", price=Decimal("10.00"))
        product.save()

        with open("main/fixtures/sample-images/harry-potter.jpg", "rb") as f:
            image = models.ProductImage(
                product=product, image=ImageFile(f, name="hp.jpg")
            )
            with self.assertLogs("main", level="INFO") as cm:
                image.save()

        self.assertGreaterEqual(len(cm.output), 1)
        image.thumbnail.delete(save=False)
        image.image.delete(save=False)
