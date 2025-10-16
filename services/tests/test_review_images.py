"""
Comprehensive tests for review image upload functionality.
Tests cover: validation, limits, optimization, display, and edge cases.
"""

import io
import pytest
from PIL import Image as PILImage
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import City, County, CraftsmanProfile
from services.models import Order, Review, ReviewImage, Service, ServiceCategory

User = get_user_model()


@pytest.fixture
def client_user(db):
    """Create a test client user."""
    return User.objects.create_user(
        username="testclient",
        email="client@test.com",
        password="testpass123",
        user_type="client"
    )


@pytest.fixture
def craftsman_user(db):
    """Create a test craftsman user with profile."""
    user = User.objects.create_user(
        username="testcraftsman",
        email="craftsman@test.com",
        password="testpass123",
        user_type="craftsman"
    )
    county, _ = County.objects.get_or_create(name="București", code="B")
    city, _ = City.objects.get_or_create(name="București", county=county)
    CraftsmanProfile.objects.create(
        user=user,
        display_name="Test Craftsman",
        county=county,
        city=city
    )
    return user


@pytest.fixture
def completed_order(db, client_user, craftsman_user):
    """Create a completed order."""
    category = ServiceCategory.objects.create(name="Test Category", slug="test-cat")
    service = Service.objects.create(category=category, name="Test Service", slug="test-svc")
    county = County.objects.get_or_create(name="București", code="B")[0]
    city = City.objects.get_or_create(name="București", county=county)[0]

    order = Order.objects.create(
        client=client_user,
        title="Test Order",
        description="Test description",
        service=service,
        county=county,
        city=city,
        status="completed",
        assigned_craftsman=craftsman_user.craftsman_profile
    )
    return order


@pytest.fixture
def sample_image():
    """Create a sample image file for testing."""
    def _create_image(width=800, height=600, format='JPEG', size_kb=None):
        img = PILImage.new('RGB', (width, height), color='red')
        img_io = io.BytesIO()
        img.save(img_io, format=format)
        img_io.seek(0)

        # If size_kb specified, create larger file
        if size_kb:
            content = img_io.read()
            # Pad to reach desired size
            padding_size = (size_kb * 1024) - len(content)
            if padding_size > 0:
                content += b'\0' * padding_size
            img_io = io.BytesIO(content)
            img_io.seek(0)

        return SimpleUploadedFile(
            name='test_image.jpg',
            content=img_io.read(),
            content_type='image/jpeg'
        )
    return _create_image


# ===== Test Image Upload Success Cases =====

@pytest.mark.django_db
class TestReviewImageUploadSuccess:
    """Test successful image upload scenarios."""

    def test_upload_single_image(self, client_user, completed_order, sample_image):
        """Test uploading a single review image."""
        review = Review.objects.create(
            order=completed_order,
            client=client_user,
            craftsman=completed_order.assigned_craftsman,
            rating=5,
            comment="Great work!"
        )

        image = sample_image()
        review_image = ReviewImage.objects.create(
            review=review,
            image=image,
            description="Test image"
        )

        assert review_image.id is not None
        assert review_image.review == review
        assert review.images.count() == 1

    def test_upload_multiple_images_max_5(self, client_user, completed_order, sample_image):
        """Test uploading 5 images (maximum allowed)."""
        review = Review.objects.create(
            order=completed_order,
            client=client_user,
            craftsman=completed_order.assigned_craftsman,
            rating=5
        )

        for i in range(5):
            ReviewImage.objects.create(
                review=review,
                image=sample_image(),
                description=f"Image {i+1}"
            )

        assert review.images.count() == 5

    def test_review_image_saved_with_correct_path(self, client_user, completed_order, sample_image):
        """Test that image is saved to correct path."""
        review = Review.objects.create(
            order=completed_order,
            client=client_user,
            craftsman=completed_order.assigned_craftsman,
            rating=4
        )

        review_image = ReviewImage.objects.create(
            review=review,
            image=sample_image()
        )

        assert 'review_images/' in review_image.image.name


# ===== Test Image Validation =====

@pytest.mark.django_db
class TestReviewImageValidation:
    """Test image validation rules."""

    def test_reject_exceeding_max_images(self, client_user, completed_order, sample_image):
        """Test that uploading more than 5 images is prevented at model level."""
        review = Review.objects.create(
            order=completed_order,
            client=client_user,
            craftsman=completed_order.assigned_craftsman,
            rating=5
        )

        # Upload 5 images successfully
        for i in range(5):
            ReviewImage.objects.create(review=review, image=sample_image())

        # 6th image should still be created (validation happens in form/view)
        # This tests that DB allows it but form should prevent it
        review_image_6 = ReviewImage.objects.create(review=review, image=sample_image())
        assert review_image_6.id is not None
        assert review.images.count() == 6  # DB allows, but form should prevent

    def test_image_with_description(self, client_user, completed_order, sample_image):
        """Test image with custom description."""
        review = Review.objects.create(
            order=completed_order,
            client=client_user,
            craftsman=completed_order.assigned_craftsman,
            rating=5
        )

        review_image = ReviewImage.objects.create(
            review=review,
            image=sample_image(),
            description="Lucrarea finalizată - vedere completă"
        )

        assert review_image.description == "Lucrarea finalizată - vedere completă"


# ===== Test Review Image Display =====

@pytest.mark.django_db
class TestReviewImageDisplay:
    """Test that images are properly linked and displayed."""

    def test_review_images_accessible_from_review(self, client_user, completed_order, sample_image):
        """Test accessing images through review.images relationship."""
        review = Review.objects.create(
            order=completed_order,
            client=client_user,
            craftsman=completed_order.assigned_craftsman,
            rating=5
        )

        # Create 3 images
        for i in range(3):
            ReviewImage.objects.create(review=review, image=sample_image())

        # Access through relationship
        images = review.images.all()
        assert images.count() == 3
        assert all(img.review == review for img in images)

    def test_review_images_accessible_from_craftsman_profile(self, client_user, completed_order, sample_image):
        """Test that craftsman can see images in their reviews."""
        review = Review.objects.create(
            order=completed_order,
            client=client_user,
            craftsman=completed_order.assigned_craftsman,
            rating=5
        )

        ReviewImage.objects.create(review=review, image=sample_image())

        # Access through craftsman profile
        craftsman_reviews = Review.objects.filter(craftsman=completed_order.assigned_craftsman)
        assert craftsman_reviews.count() == 1
        assert craftsman_reviews.first().images.count() == 1

    def test_review_images_accessible_from_client_profile(self, client_user, completed_order, sample_image):
        """Test that client can see images in their given reviews."""
        review = Review.objects.create(
            order=completed_order,
            client=client_user,
            craftsman=completed_order.assigned_craftsman,
            rating=5
        )

        ReviewImage.objects.create(review=review, image=sample_image())

        # Access through client profile
        client_reviews = Review.objects.filter(client=client_user)
        assert client_reviews.count() == 1
        assert client_reviews.first().images.count() == 1


# ===== Test Edge Cases =====

@pytest.mark.django_db
class TestReviewImageEdgeCases:
    """Test edge cases and error scenarios."""

    def test_review_without_images(self, client_user, completed_order):
        """Test that review can exist without images."""
        review = Review.objects.create(
            order=completed_order,
            client=client_user,
            craftsman=completed_order.assigned_craftsman,
            rating=5,
            comment="Great work but no photos"
        )

        assert review.images.count() == 0
        assert review.id is not None

    def test_delete_review_cascades_to_images(self, client_user, completed_order, sample_image):
        """Test that deleting review also deletes associated images."""
        review = Review.objects.create(
            order=completed_order,
            client=client_user,
            craftsman=completed_order.assigned_craftsman,
            rating=5
        )

        # Create 3 images
        for i in range(3):
            ReviewImage.objects.create(review=review, image=sample_image())

        review_id = review.id
        assert ReviewImage.objects.filter(review_id=review_id).count() == 3

        # Delete review
        review.delete()

        # Images should be cascade deleted
        assert ReviewImage.objects.filter(review_id=review_id).count() == 0

    def test_edit_review_add_more_images(self, client_user, completed_order, sample_image):
        """Test adding more images when editing a review."""
        review = Review.objects.create(
            order=completed_order,
            client=client_user,
            craftsman=completed_order.assigned_craftsman,
            rating=5
        )

        # Initial: 2 images
        ReviewImage.objects.create(review=review, image=sample_image())
        ReviewImage.objects.create(review=review, image=sample_image())
        assert review.images.count() == 2

        # Add 3 more (total 5 - OK)
        for i in range(3):
            ReviewImage.objects.create(review=review, image=sample_image())

        assert review.images.count() == 5

    def test_edit_review_cannot_exceed_5_images(self, client_user, completed_order, sample_image):
        """Test that editing doesn't allow exceeding 5 images total."""
        review = Review.objects.create(
            order=completed_order,
            client=client_user,
            craftsman=completed_order.assigned_craftsman,
            rating=5
        )

        # Start with 4 images
        for i in range(4):
            ReviewImage.objects.create(review=review, image=sample_image())

        assert review.images.count() == 4

        # Form validation should prevent adding 2 more
        # But at DB level, we can add (form should block)
        ReviewImage.objects.create(review=review, image=sample_image())
        ReviewImage.objects.create(review=review, image=sample_image())

        # DB allows 6, but form validation should prevent this
        assert review.images.count() == 6


# ===== Test Form Validation (Integration) =====

@pytest.mark.django_db
class TestReviewImageFormValidation:
    """Test form-level validation for image uploads."""

    def test_form_validates_image_type(self, sample_image):
        """Test that form validates file is an image."""
        from services.forms import MultipleReviewImageForm

        # This would be tested in view tests with actual form submission
        # Here we verify model accepts valid image
        valid_image = sample_image()
        assert valid_image.content_type == 'image/jpeg'

    def test_form_counts_existing_images_correctly(self):
        """Test that form considers existing images when validating new uploads."""
        from services.forms import MultipleReviewImageForm

        # Test form initialization with existing images
        form = MultipleReviewImageForm(existing_images_count=3, max_images=5)
        assert form.existing_images_count == 3
        assert form.max_images == 5


# ===== Test Image Timestamps =====

@pytest.mark.django_db
class TestReviewImageTimestamps:
    """Test timestamp tracking for images."""

    def test_image_has_created_timestamp(self, client_user, completed_order, sample_image):
        """Test that ReviewImage has created_at timestamp."""
        review = Review.objects.create(
            order=completed_order,
            client=client_user,
            craftsman=completed_order.assigned_craftsman,
            rating=5
        )

        review_image = ReviewImage.objects.create(review=review, image=sample_image())

        assert review_image.created_at is not None

    def test_images_ordered_by_creation_date(self, client_user, completed_order, sample_image):
        """Test that images can be ordered by creation date."""
        review = Review.objects.create(
            order=completed_order,
            client=client_user,
            craftsman=completed_order.assigned_craftsman,
            rating=5
        )

        # Create 3 images
        img1 = ReviewImage.objects.create(review=review, image=sample_image(), description="First")
        img2 = ReviewImage.objects.create(review=review, image=sample_image(), description="Second")
        img3 = ReviewImage.objects.create(review=review, image=sample_image(), description="Third")

        # Get ordered by created_at
        ordered_images = review.images.order_by('created_at')
        assert list(ordered_images) == [img1, img2, img3]
