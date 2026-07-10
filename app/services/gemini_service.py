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
        
    def recommend_video_config(self, product_name: str, product_description: str = "", 
                           generation_mode: str = "image", 
                           has_first_frame: bool = False, 
                           has_last_frame: bool = False) -> dict:
        """
        Generate video configuration recommendations based on product and images
        
        Args:
            product_name: Name of the product
            product_description: Product description (optional)
            generation_mode: "image" or "first-last"
            has_first_frame: Whether first frame image is provided
            has_last_frame: Whether last frame image is provided
        
        Returns:
            Dictionary with video configuration recommendations
        """
        
        # Build a consumer-focused prompt
        prompt = f"""
    You are a professional video director and social media ad expert. 
    Analyze the following product information and recommend video settings.

    Product Name: {product_name or "Product"}
    Product Description: {product_description or "No description provided"}

    Generation Mode: {generation_mode.upper()}
    Images Provided: 
    - First Frame: {"Yes" if has_first_frame else "No"}
    - Last Frame: {"Yes" if has_last_frame else "No"}

    Based on this information, provide a complete video configuration that would make a compelling social media ad.

    ## Your Recommendations:

    1. Camera Movement: [Suggest what camera motion works best - dolly, pan, tilt, zoom, orbit, etc.]

    2. Lighting: [Suggest lighting style - warm, cool, dramatic, soft, natural, studio, etc.]

    3. Action/Motion: [Describe what should happen - product rotates, model uses product, smooth transition, etc.]

    4. Audio/Music: [Suggest music style and sound effects]

    5. Duration: [Choose 4, 6, or 8 seconds - explain why]

    6. Visual Style: [Describe the aesthetic - cinematic, modern, minimal, luxury, energetic, etc.]

    7. Complete Prompt: [Write a detailed, professional prompt that combines all elements]
    Format: "[Action description]. [Camera movement]. [Lighting]. [Style]. [Product focus]."

    Remember:
    - This is for a SOCIAL MEDIA AD (TikTok/Instagram/YouTube)
    - Keep it consumer-friendly and visually appealing
    - Focus on what would catch a viewer's attention
    - Make the prompt specific and actionable for AI video generation
    - ONLY provide marketing/video content - NO code or technical advice
    """
        
        # Generate the response
        response = self.generate_text(prompt)
        
        # Parse the response into structured data
        recommendations = self._parse_video_recommendations(response)
        
        return recommendations

    def _parse_video_recommendations(self, response: str) -> dict:
        """
        Parse the AI response into structured recommendations
        """
        # Default values
        recs = {
            "camera_movement": "gentle slow pan",
            "lighting": "natural soft lighting",
            "action": "product rotates smoothly to show all angles",
            "audio": "upbeat modern background music",
            "duration_seconds": 6,
            "style": "clean minimal product showcase",
            "prompt_enhancement": "",
            "mood": "professional and premium"
        }
        
        try:
            # Extract camera movement
            import re
            camera_match = re.search(r'Camera Movement:?\s*([^\n.]+[.\n])', response, re.IGNORECASE)
            if camera_match:
                recs["camera_movement"] = camera_match.group(1).strip()
            
            # Extract lighting
            lighting_match = re.search(r'Lighting:?\s*([^\n.]+[.\n])', response, re.IGNORECASE)
            if lighting_match:
                recs["lighting"] = lighting_match.group(1).strip()
            
            # Extract action
            action_match = re.search(r'Action/Motion:?\s*([^\n.]+[.\n])', response, re.IGNORECASE)
            if action_match:
                recs["action"] = action_match.group(1).strip()
            
            # Extract audio
            audio_match = re.search(r'Audio/Music:?\s*([^\n.]+[.\n])', response, re.IGNORECASE)
            if audio_match:
                recs["audio"] = audio_match.group(1).strip()
            
            # Extract duration
            duration_match = re.search(r'Duration:?\s*(\d+)\s*seconds?', response, re.IGNORECASE)
            if duration_match:
                recs["duration_seconds"] = int(duration_match.group(1))
            
            # Extract style
            style_match = re.search(r'Visual Style:?\s*([^\n.]+[.\n])', response, re.IGNORECASE)
            if style_match:
                recs["style"] = style_match.group(1).strip()
            
            # Extract complete prompt
            prompt_match = re.search(r'Complete Prompt:?\s*([^\n]+(?:\n[^\n]+)*)', response, re.IGNORECASE)
            if prompt_match:
                recs["prompt_enhancement"] = prompt_match.group(1).strip()
            
            # Extract mood (optional)
            mood_match = re.search(r'Mood:?\s*([^\n.]+[.\n])', response, re.IGNORECASE)
            if mood_match:
                recs["mood"] = mood_match.group(1).strip()
                
        except Exception as e:
            logger.error(f"Error parsing recommendations: {e}")
        
        return recs
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