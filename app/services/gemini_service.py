"""
Gemini AI Service - Marketing & Ad Content Only
No code generation, no developer advice
"""

from google import genai
from google.genai import types
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        """Initialize Gemini AI service"""
        try:
            self.client = genai.Client(
                vertexai=True,
                project="ai-social-ad-generator",
                location="us-central1"
            )
            logger.info("✅ Gemini AI client initialized for Vertex AI")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini AI: {e}")
            raise

    def generate_text(self, prompt: str, context: Optional[str] = None) -> str:
        """
        Generate marketing/ad content only - NO CODE
        """
        try:
            # Strict marketing-only prompt with explicit restrictions
            formatted_prompt = f"""
{context if context else ""}

{prompt}

🚫 STRICT RULES - YOU MUST FOLLOW:
1. NEVER write code (no Python, JavaScript, HTML, CSS, SQL, etc.)
2. NEVER give technical/developer advice
3. NEVER explain how to build software
4. NEVER give programming instructions
5. ONLY provide marketing, advertising, and business content
6. ONLY help with product descriptions, ad scripts, features
7. ONLY provide consumer-focused advice
8. If asked for code or technical help, politely decline

✅ ALLOWED CONTENT:
- Product descriptions
- Ad scripts (TikTok/Instagram/YouTube)
- Marketing ideas and strategies
- Product features and benefits
- Buying guides for consumers
- Slogans and taglines
- Brand voice and tone suggestions
- Consumer tips and advice

📋 RESPONSE FORMAT:
1. Use ## for sections
2. Use bullet points (•) for features
3. Keep paragraphs short (2-3 sentences)
4. Include specific, practical information
5. Make it consumer-friendly

Example Format:
## Overview
[2-3 sentences about the product/service]

## Key Features
• [Feature 1 - brief explanation]
• [Feature 2 - brief explanation]

## Benefits
• [Benefit for the consumer]

## Summary
[1-2 sentences conclusion]

If the user asks about code, programming, or technical development:
"I'm designed to help with marketing and ad content. For technical questions, please consult a developer or technical support."
"""
            
            logger.info(f"📝 Generating marketing content for: {prompt[:50]}...")
            
            models = [
                "publishers/google/models/gemini-2.5-flash",
                "gemini-2.5-flash",
                "publishers/google/models/gemini-1.0-pro-002",
                "gemini-1.0-pro",
            ]
            
            last_error = None
            for model_name in models:
                try:
                    logger.info(f"🔄 Trying model: {model_name}")
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=formatted_prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.6,
                            max_output_tokens=1024,
                        )
                    )
                    
                    if response.text:
                        # Check if the response contains code patterns
                        if self._contains_code(response.text):
                            return self._get_fallback_response()
                        
                        cleaned_text = self._format_response(response.text)
                        logger.info(f"✅ Marketing content generated with {model_name}")
                        return cleaned_text
                except Exception as e:
                    logger.warning(f"⚠️ Model {model_name} failed: {e}")
                    last_error = e
                    continue
            
            logger.error(f"❌ All models failed. Last error: {last_error}")
            return "Sorry, I'm having trouble generating a response. Please try again later."
                
        except Exception as e:
            logger.error(f"❌ Text generation error: {e}")
            return f"Error: {str(e)}"

    def _contains_code(self, text: str) -> bool:
        """
        Check if response contains code patterns
        """
        code_patterns = [
            r'```',  # Code blocks
            r'def\s+\w+\s*\(',  # Python function
            r'class\s+\w+\s*[:\(]',  # Class definition
            r'const\s+\w+\s*=',  # JavaScript constant
            r'let\s+\w+\s*=',  # JavaScript let
            r'var\s+\w+\s*=',  # JavaScript var
            r'function\s+\w+\s*\(',  # JavaScript function
            r'import\s+',  # Import statements
            r'from\s+.*\s+import',  # Python imports
            r'<html>',  # HTML
            r'<\w+\s*>',  # HTML tags
            r'CREATE\s+TABLE',  # SQL
            r'SELECT.*FROM',  # SQL
            r'INSERT\s+INTO',  # SQL
            r'UPDATE\s+.*SET',  # SQL
            r'DELETE\s+FROM',  # SQL
            r'sqlalchemy',  # Specific libraries
            r'fastapi',
            r'django',
            r'react',
            r'vue',
            r'angular',
            r'pip\s+install',
            r'npm\s+install',
            r'yarn\s+add',
            r'//',  # Comments
            r'/\*',  # Multi-line comments
            r'#.*python',  # Python comments
            r'<style>',  # CSS
            r'.*\s*{\s*[\w-]+:',  # CSS rules
        ]
        
        for pattern in code_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _get_fallback_response(self) -> str:
        """
        Fallback response when code is detected
        """
        return """I'm designed to help with marketing and ad content. For technical/developer questions, please consult a developer or technical support.

Here's what I can help with:
• Product descriptions
• Ad scripts (TikTok/Instagram/YouTube)
• Marketing ideas
• Product features & benefits
• Buying guides
• Slogans & taglines

Feel free to ask about any of these!"""

    def _format_response(self, text: str) -> str:
        """
        Clean and format the response
        """
        text = re.sub(r'\n{4,}', '\n\n', text)
        
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted_lines.append('')
                continue
            
            # Format bullet points
            if stripped.startswith('*') or stripped.startswith('-') or stripped.startswith('•'):
                bullet_text = stripped.lstrip('* -•').strip()
                if bullet_text:
                    formatted_lines.append(f'• {bullet_text}')
            elif stripped.startswith('##'):
                formatted_lines.append(stripped)
            else:
                formatted_lines.append(stripped)
        
        return '\n'.join(formatted_lines)

    def generate_product_description(self, product_name: str, features: str = "") -> str:
        """Generate detailed product description - Marketing Only"""
        prompt = f"""Write a detailed product description for {product_name}.

Features: {features if features else "Highlight key consumer features"}

Include:
- 2-3 sentence overview (consumer-focused)
- 4-5 key features with benefits for the user
- 1-2 reasons why this product is good for the consumer
- Call to action

Remember: ONLY marketing content, NO code."""
        return self.generate_text(prompt)

    def generate_ad_script(self, product_name: str, platform: str = "tiktok") -> str:
        """Generate detailed ad script - Marketing Only"""
        prompt = f"""Create a detailed video ad script for {product_name} on {platform}.

Include:
- Scene-by-scene breakdown (5-6 scenes)
- Visual descriptions (consumer-friendly)
- Text overlay (short, catchy)
- Audio suggestions

Remember: ONLY marketing content, NO code."""
        return self.generate_text(prompt)

    def generate_features(self, product_type: str) -> str:
        """Generate detailed features list - Marketing Only"""
        prompt = f"""List and explain key features for {product_type} from a consumer perspective.

For each feature:
- Feature name (consumer-friendly)
- 1-sentence explanation
- Benefit to the user

Include 5-7 features. NO technical jargon."""
        return self.generate_text(prompt)

    def generate_buying_guide(self, product_type: str) -> str:
        """Generate detailed buying guide - Marketing Only"""
        prompt = f"""Create a detailed buying guide for {product_type} for consumers.

Include:
## Overview
[2-3 sentences on what to consider]

## What to Look For
• [Factor 1] - [Consumer-friendly explanation]
• [Factor 2] - [Consumer-friendly explanation]
• [Factor 3] - [Consumer-friendly explanation]

## Top Recommendations
• [Product 1] - [Price, key feature, why it's good for consumers]
• [Product 2] - [Price, key feature, why it's good for consumers]

## Final Tips
[2-3 practical tips for consumers]

Remember: ONLY consumer-focused content, NO code."""
        return self.generate_text(prompt)