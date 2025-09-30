"""
AI Review Summary Service using OpenAI API.

This service handles the generation and updating of AI-powered review summaries
for products using OpenAI's GPT models.
"""

import openai
import logging
from django.conf import settings
from django.db import transaction
from reviews.models import Review, ReviewSummary
from products.models import Product

logger = logging.getLogger(__name__)

class AIReviewSummaryService:
    """
    Service for generating AI-powered review summaries using OpenAI API.
    """
    
    def __init__(self):
        """Initialize the OpenAI client."""
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured")
            self.client = None
        else:
            openai.api_key = settings.OPENAI_API_KEY
            self.client = openai
    
    def generate_summary(self, product_id: int) -> str:
        """
        Generate an AI summary for a product's reviews.
        
        Args:
            product_id: ID of the product to summarize reviews for
            
        Returns:
            str: Generated summary text
        """
        if not self.client:
            logger.error("OpenAI client not initialized - API key missing")
            return "AI summary unavailable - API key not configured"
        
        try:
            product = Product.objects.get(id=product_id)
            reviews = Review.objects.filter(
                product=product, 
                is_approved=True
            ).order_by('-created_at')
            
            if not reviews.exists():
                return "No reviews available for this product yet."
            
            # Prepare review data for AI analysis
            review_texts = []
            ratings = []
            
            for review in reviews[:50]:  # Limit to recent 50 reviews to avoid token limits
                review_texts.append(f"Rating: {review.rating}/5 - {review.title}: {review.comment}")
                ratings.append(review.rating)
            
            # Calculate basic stats
            avg_rating = sum(ratings) / len(ratings)
            total_reviews = len(ratings)
            
            # Create prompt for OpenAI
            prompt = self._create_summary_prompt(
                product.name, 
                review_texts, 
                avg_rating, 
                total_reviews
            )
            
            # Call OpenAI API
            response = self.client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a helpful assistant that summarizes product reviews for an e-commerce site. Provide concise, balanced summaries that highlight key themes in customer feedback."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Calculate sentiment score (simple approach based on average rating)
            sentiment_score = self._calculate_sentiment_score(avg_rating)
            
            return summary
            
        except Product.DoesNotExist:
            logger.error(f"Product with ID {product_id} not found")
            return "Product not found"
        except Exception as e:
            logger.error(f"Error generating AI summary for product {product_id}: {str(e)}")
            return f"Error generating summary: {str(e)}"
    
    def update_product_summary(self, product_id: int) -> bool:
        """
        Update or create the AI summary for a product.
        
        Args:
            product_id: ID of the product to update summary for
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with transaction.atomic():
                product = Product.objects.get(id=product_id)
                reviews = Review.objects.filter(
                    product=product, 
                    is_approved=True
                )
                
                if not reviews.exists():
                    # Remove existing summary if no reviews
                    ReviewSummary.objects.filter(product=product).delete()
                    return True
                
                # Generate new summary
                summary_text = self.generate_summary(product_id)
                
                # Calculate stats
                avg_rating = reviews.aggregate(
                    avg=models.Avg('rating')
                )['avg'] or 0
                total_reviews = reviews.count()
                sentiment_score = self._calculate_sentiment_score(avg_rating)
                
                # Update or create summary
                summary, created = ReviewSummary.objects.update_or_create(
                    product=product,
                    defaults={
                        'summary': summary_text,
                        'total_reviews': total_reviews,
                        'average_rating': round(avg_rating, 2),
                        'sentiment_score': sentiment_score
                    }
                )
                
                action = "created" if created else "updated"
                logger.info(f"Review summary {action} for product {product.name}")
                return True
                
        except Product.DoesNotExist:
            logger.error(f"Product with ID {product_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error updating summary for product {product_id}: {str(e)}")
            return False
    
    def _create_summary_prompt(self, product_name: str, review_texts: list, 
                              avg_rating: float, total_reviews: int) -> str:
        """
        Create a prompt for OpenAI to generate review summary.
        
        Args:
            product_name: Name of the product
            review_texts: List of review texts
            avg_rating: Average rating
            total_reviews: Total number of reviews
            
        Returns:
            str: Formatted prompt for OpenAI
        """
        reviews_text = "\n".join(review_texts[:20])  # Limit to avoid token limits
        
        prompt = f"""
Please analyze the following customer reviews for "{product_name}" and provide a concise summary.

Product: {product_name}
Average Rating: {avg_rating:.1f}/5 stars
Total Reviews: {total_reviews}

Customer Reviews:
{reviews_text}

Please provide a balanced summary that:
1. Highlights the main positive aspects customers appreciate
2. Notes any common concerns or issues mentioned
3. Mentions the overall sentiment and satisfaction level
4. Keeps the summary concise (2-3 sentences maximum)
5. Uses a professional, neutral tone

Summary:
"""
        return prompt
    
    def _calculate_sentiment_score(self, avg_rating: float) -> float:
        """
        Calculate sentiment score based on average rating.
        
        Args:
            avg_rating: Average rating (1-5 scale)
            
        Returns:
            float: Sentiment score (-1 to 1)
        """
        # Convert 1-5 rating to -1 to 1 sentiment score
        # 1-2 stars = negative (-1 to -0.2)
        # 3 stars = neutral (around 0)
        # 4-5 stars = positive (0.2 to 1)
        
        if avg_rating <= 2:
            return round((avg_rating - 3) / 2, 2)  # Maps 1->-1, 2->-0.5
        elif avg_rating >= 4:
            return round((avg_rating - 3) / 2, 2)  # Maps 4->0.5, 5->1
        else:
            return round((avg_rating - 3) / 2, 2)  # Maps 3->0
    
    def bulk_update_summaries(self, product_ids: list = None) -> dict:
        """
        Update summaries for multiple products.
        
        Args:
            product_ids: List of product IDs to update. If None, updates all products.
            
        Returns:
            dict: Statistics about the update process
        """
        if product_ids is None:
            products = Product.objects.filter(status='active')
        else:
            products = Product.objects.filter(id__in=product_ids, status='active')
        
        stats = {
            'total_products': products.count(),
            'successful_updates': 0,
            'failed_updates': 0,
            'errors': []
        }
        
        for product in products:
            try:
                success = self.update_product_summary(product.id)
                if success:
                    stats['successful_updates'] += 1
                else:
                    stats['failed_updates'] += 1
            except Exception as e:
                stats['failed_updates'] += 1
                stats['errors'].append(f"Product {product.id}: {str(e)}")
        
        logger.info(f"Bulk summary update completed: {stats}")
        return stats


# Service instance
ai_review_service = AIReviewSummaryService()
