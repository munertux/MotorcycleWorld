"""
Service layer for handling business logic related to reviews and AI summaries.
"""
import openai
from django.conf import settings
from reviews.models import Review, ReviewSummary
from products.models import Product
import logging

logger = logging.getLogger(__name__)

class ReviewSummaryService:
    """
    Service for generating AI-powered review summaries using OpenAI API.
    """
    
    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
            self.client = openai
    
    def generate_review_summary(self, product_id):
        """
        Generate an AI summary for all approved reviews of a product.
        
        Args:
            product_id (int): The ID of the product
            
        Returns:
            dict: Summary data including text, sentiment score, etc.
        """
        if not self.client:
            logger.warning("OpenAI API key not configured")
            return self._create_fallback_summary(product_id)
        
        try:
            product = Product.objects.get(id=product_id)
            reviews = Review.objects.filter(product=product, is_approved=True)
            
            if not reviews.exists():
                return {
                    'summary': 'No reviews available for this product yet.',
                    'sentiment_score': 0,
                    'total_reviews': 0,
                    'average_rating': 0
                }
            
            # Prepare review text for AI analysis
            review_texts = []
            total_rating = 0
            
            for review in reviews:
                review_text = f"Rating: {review.rating}/5 - {review.title}: {review.comment}"
                review_texts.append(review_text)
                total_rating += review.rating
            
            combined_reviews = "\n".join(review_texts)
            average_rating = total_rating / len(review_texts)
            
            # Generate summary using OpenAI
            ai_summary = self._call_openai_api(combined_reviews, product.name)
            sentiment_score = self._analyze_sentiment(combined_reviews)
            
            summary_data = {
                'summary': ai_summary,
                'sentiment_score': sentiment_score,
                'total_reviews': len(review_texts),
                'average_rating': round(average_rating, 2)
            }
            
            # Update or create ReviewSummary
            self._update_review_summary(product, summary_data)
            
            return summary_data
            
        except Product.DoesNotExist:
            logger.error(f"Product with ID {product_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error generating review summary: {str(e)}")
            return self._create_fallback_summary(product_id)
    
    def _call_openai_api(self, review_text, product_name):
        """
        Call OpenAI API to generate review summary.
        """
        try:
            prompt = f"""
            Analyze the following customer reviews for the product "{product_name}" and provide a concise summary highlighting:
            1. Main positive points mentioned by customers
            2. Any common concerns or issues
            3. Overall customer satisfaction level
            4. Key features that customers appreciate
            
            Keep the summary between 100-150 words and write it in a professional, helpful tone.
            
            Reviews:
            {review_text}
            
            Summary:
            """
            
            response = self.client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes product reviews."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            return self._create_fallback_text_summary(review_text)
    
    def _analyze_sentiment(self, review_text):
        """
        Analyze sentiment of reviews and return a score between -1 and 1.
        """
        try:
            prompt = f"""
            Analyze the sentiment of the following product reviews and provide a sentiment score.
            Return only a number between -1 (very negative) and 1 (very positive), where 0 is neutral.
            
            Reviews:
            {review_text}
            
            Sentiment Score:
            """
            
            response = self.client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a sentiment analysis expert. Respond only with a number between -1 and 1."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.3
            )
            
            score_text = response.choices[0].message.content.strip()
            try:
                score = float(score_text)
                return max(-1, min(1, score))  # Ensure score is between -1 and 1
            except ValueError:
                return 0  # Default to neutral if parsing fails
                
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            return 0  # Default to neutral sentiment
    
    def _create_fallback_summary(self, product_id):
        """
        Create a basic summary without AI when OpenAI is not available.
        """
        try:
            product = Product.objects.get(id=product_id)
            reviews = Review.objects.filter(product=product, is_approved=True)
            
            if not reviews.exists():
                return {
                    'summary': 'No reviews available for this product yet.',
                    'sentiment_score': 0,
                    'total_reviews': 0,
                    'average_rating': 0
                }
            
            total_rating = sum(review.rating for review in reviews)
            average_rating = total_rating / reviews.count()
            
            # Create basic summary
            summary = f"This product has {reviews.count()} customer reviews with an average rating of {average_rating:.1f} stars. "
            
            if average_rating >= 4:
                summary += "Customers are generally very satisfied with this product."
            elif average_rating >= 3:
                summary += "Customers have mixed feelings about this product."
            else:
                summary += "Some customers have expressed concerns about this product."
            
            summary_data = {
                'summary': summary,
                'sentiment_score': (average_rating - 3) / 2,  # Convert 1-5 rating to -1 to 1 sentiment
                'total_reviews': reviews.count(),
                'average_rating': round(average_rating, 2)
            }
            
            self._update_review_summary(product, summary_data)
            return summary_data
            
        except Exception as e:
            logger.error(f"Error creating fallback summary: {str(e)}")
            return None
    
    def _create_fallback_text_summary(self, review_text):
        """
        Create a simple text summary without AI.
        """
        lines = review_text.split('\n')
        positive_keywords = ['good', 'great', 'excellent', 'amazing', 'love', 'perfect', 'quality']
        negative_keywords = ['bad', 'poor', 'terrible', 'hate', 'awful', 'disappointed', 'problem']
        
        positive_count = sum(1 for line in lines for keyword in positive_keywords if keyword in line.lower())
        negative_count = sum(1 for line in lines for keyword in negative_keywords if keyword in line.lower())
        
        if positive_count > negative_count:
            return f"Based on {len(lines)} reviews, customers are generally satisfied with this product, highlighting positive aspects."
        elif negative_count > positive_count:
            return f"Based on {len(lines)} reviews, customers have raised some concerns about this product."
        else:
            return f"Based on {len(lines)} reviews, customers have mixed opinions about this product."
    
    def _update_review_summary(self, product, summary_data):
        """
        Update or create the ReviewSummary for a product.
        """
        try:
            summary, created = ReviewSummary.objects.update_or_create(
                product=product,
                defaults=summary_data
            )
            
            if created:
                logger.info(f"Created review summary for product {product.name}")
            else:
                logger.info(f"Updated review summary for product {product.name}")
                
        except Exception as e:
            logger.error(f"Error updating review summary: {str(e)}")

# Service instance
review_summary_service = ReviewSummaryService()
