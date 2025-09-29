from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from products.models import Product

class Review(models.Model):
    """
    Product Review model for customer feedback and ratings.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    title = models.CharField(max_length=200)
    comment = models.TextField()
    is_approved = models.BooleanField(default=True)
    is_verified_purchase = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating} stars)"
    
    class Meta:
        db_table = 'reviews'
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        unique_together = ['product', 'user']  # One review per user per product

class ReviewHelpful(models.Model):
    """
    Model to track which users found a review helpful.
    """
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'review_helpful'
        unique_together = ['review', 'user']

class ReviewSummary(models.Model):
    """
    AI-generated summary of product reviews using OpenAI API.
    """
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='review_summary')
    summary = models.TextField()
    total_reviews = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    sentiment_score = models.DecimalField(
        max_digits=3, decimal_places=2, 
        default=0,
        help_text="Sentiment score from -1 (negative) to 1 (positive)"
    )
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Review Summary for {self.product.name}"
    
    class Meta:
        db_table = 'review_summaries'
        verbose_name = 'Review Summary'
        verbose_name_plural = 'Review Summaries'
