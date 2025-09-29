from rest_framework import serializers
from .models import Review, ReviewHelpful, ReviewSummary
from products.models import Product

class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for product reviews.
    """
    user_name = serializers.CharField(source='user.username', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    is_helpful = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'product', 'product_name', 'user_name', 'rating',
            'title', 'comment', 'is_verified_purchase', 'helpful_count',
            'is_helpful', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user_name', 'product_name', 'helpful_count',
            'is_verified_purchase', 'created_at', 'updated_at'
        ]
    
    def get_is_helpful(self, obj):
        """Check if current user found this review helpful"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ReviewHelpful.objects.filter(
                review=obj, 
                user=request.user
            ).exists()
        return False
    
    def validate(self, attrs):
        """Validate that user hasn't already reviewed this product"""
        request = self.context.get('request')
        product = attrs.get('product')
        
        if request and request.user.is_authenticated:
            if self.instance is None:  # Creating new review
                if Review.objects.filter(
                    product=product, 
                    user=request.user
                ).exists():
                    raise serializers.ValidationError(
                        "You have already reviewed this product."
                    )
        return attrs
    
    def create(self, validated_data):
        """Create review with current user"""
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)

class ReviewCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating reviews.
    """
    class Meta:
        model = Review
        fields = ['product', 'rating', 'title', 'comment']
    
    def validate(self, attrs):
        """Validate that user hasn't already reviewed this product"""
        request = self.context.get('request')
        product = attrs.get('product')
        
        if request and request.user.is_authenticated:
            if Review.objects.filter(
                product=product, 
                user=request.user
            ).exists():
                raise serializers.ValidationError(
                    "You have already reviewed this product."
                )
        return attrs

class ReviewListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing reviews.
    """
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_initial = serializers.SerializerMethodField()
    is_helpful = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'rating', 'title', 'comment', 'user_name', 'user_initial',
            'is_verified_purchase', 'helpful_count', 'is_helpful', 'created_at'
        ]
    
    def get_user_initial(self, obj):
        """Get user's first letter for avatar"""
        return obj.user.username[0].upper() if obj.user.username else 'U'
    
    def get_is_helpful(self, obj):
        """Check if current user found this review helpful"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ReviewHelpful.objects.filter(
                review=obj, 
                user=request.user
            ).exists()
        return False

class ReviewHelpfulSerializer(serializers.ModelSerializer):
    """
    Serializer for marking reviews as helpful.
    """
    class Meta:
        model = ReviewHelpful
        fields = ['review']
    
    def create(self, validated_data):
        """Create helpful vote with current user"""
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)
    
    def validate(self, attrs):
        """Validate that user hasn't already marked this review as helpful"""
        request = self.context.get('request')
        review = attrs.get('review')
        
        if request and request.user.is_authenticated:
            if ReviewHelpful.objects.filter(
                review=review, 
                user=request.user
            ).exists():
                raise serializers.ValidationError(
                    "You have already marked this review as helpful."
                )
        return attrs

class ReviewSummarySerializer(serializers.ModelSerializer):
    """
    Serializer for AI-generated review summaries.
    """
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = ReviewSummary
        fields = [
            'id', 'product', 'product_name', 'summary', 'total_reviews',
            'average_rating', 'sentiment_score', 'last_updated'
        ]
        read_only_fields = [
            'product_name', 'total_reviews', 'average_rating',
            'sentiment_score', 'last_updated'
        ]

class ProductReviewStatsSerializer(serializers.Serializer):
    """
    Serializer for product review statistics.
    """
    total_reviews = serializers.IntegerField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    rating_distribution = serializers.DictField()
    
    # Rating distribution fields
    five_star_count = serializers.IntegerField()
    four_star_count = serializers.IntegerField()
    three_star_count = serializers.IntegerField()
    two_star_count = serializers.IntegerField()
    one_star_count = serializers.IntegerField()
    
    five_star_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    four_star_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    three_star_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    two_star_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    one_star_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
