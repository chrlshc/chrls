#!/usr/bin/env python3
"""
🎨 HUNTER AGENCY - Template Engine with Loom Integration
Advanced email personalization with video thumbnails & tracking
"""

import os
import re
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from jinja2 import Environment, BaseLoader, TemplateError, select_autoescape
from jinja2.sandbox import SandboxedEnvironment
from urllib.parse import urlencode
import base64
import json
import logging
from PIL import Image, ImageDraw, ImageFont
import io
import uuid

logger = logging.getLogger(__name__)

# ============================================================================
# 🎬 LOOM INTEGRATION SERVICE
# ============================================================================

class LoomService:
    """Handle Loom video integration and thumbnail generation"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('LOOM_API_KEY')
        self.base_url = "https://api.loom.com/v1"
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
    
    def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get video information from Loom API"""
        try:
            if not self.api_key:
                # Fallback: generate mock data
                return self._mock_video_info(video_id)
            
            response = self.session.get(f"{self.base_url}/videos/{video_id}")
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'id': data.get('id'),
                    'title': data.get('name'),
                    'duration': data.get('duration'),
                    'thumbnail_url': data.get('thumbnail_url'),
                    'embed_url': data.get('embed_url'),
                    'share_url': data.get('share_url'),
                    'created_at': data.get('created_at')
                }
            else:
                logger.error(f"Failed to get Loom video {video_id}: {response.status_code}")
                return self._mock_video_info(video_id)
                
        except Exception as e:
            logger.error(f"Error fetching Loom video {video_id}: {str(e)}")
            return self._mock_video_info(video_id)
    
    def _mock_video_info(self, video_id: str) -> Dict[str, Any]:
        """Generate mock video info for development"""
        return {
            'id': video_id,
            'title': f'Personal Video Message',
            'duration': 45,
            'thumbnail_url': f'https://cdn.loom.com/sessions/thumbnails/{video_id}-00001.jpg',
            'embed_url': f'https://www.loom.com/embed/{video_id}',
            'share_url': f'https://www.loom.com/share/{video_id}',
            'created_at': datetime.utcnow().isoformat()
        }
    
    def generate_tracking_url(self, video_id: str, lead_id: int, email_id: int) -> str:
        """Generate trackable Loom URL"""
        base_url = f"https://www.loom.com/share/{video_id}"
        
        # Add tracking parameters
        params = {
            'lead_id': lead_id,
            'email_id': email_id,
            'utm_source': 'hunter_agency',
            'utm_medium': 'email',
            'utm_campaign': 'cold_outreach'
        }
        
        return f"{base_url}?{urlencode(params)}"
    
    def create_custom_thumbnail(self, 
                              video_id: str, 
                              lead_name: str, 
                              custom_message: str = "") -> str:
        """Create personalized thumbnail with lead name"""
        try:
            # Create a 1280x720 thumbnail
            img = Image.new('RGB', (1280, 720), color='#1a1a1a')
            draw = ImageDraw.Draw(img)
            
            # Try to load custom font, fallback to default
            try:
                title_font = ImageFont.truetype("arial.ttf", 60)
                subtitle_font = ImageFont.truetype("arial.ttf", 40)
                name_font = ImageFont.truetype("arial.ttf", 80)
            except:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                name_font = ImageFont.load_default()
            
            # Add play button
            play_center = (640, 360)
            play_radius = 80
            draw.ellipse([
                play_center[0] - play_radius,
                play_center[1] - play_radius,
                play_center[0] + play_radius,
                play_center[1] + play_radius
            ], fill='#007bff', outline='#ffffff', width=4)
            
            # Play triangle
            triangle = [
                (play_center[0] - 20, play_center[1] - 30),
                (play_center[0] - 20, play_center[1] + 30),
                (play_center[0] + 25, play_center[1])
            ]
            draw.polygon(triangle, fill='#ffffff')
            
            # Add personalized text
            main_text = f"Hey {lead_name}! 👋"
            bbox = draw.textbbox((0, 0), main_text, font=name_font)
            text_width = bbox[2] - bbox[0]
            draw.text(((1280 - text_width) // 2, 150), main_text, 
                     fill='#ffffff', font=name_font)
            
            # Subtitle
            if custom_message:
                subtitle = custom_message
            else:
                subtitle = "I made this video just for you"
            
            bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
            text_width = bbox[2] - bbox[0]
            draw.text(((1280 - text_width) // 2, 500), subtitle, 
                     fill='#cccccc', font=subtitle_font)
            
            # Duration badge
            duration_text = "0:45"
            draw.rectangle([50, 50, 150, 100], fill='#000000', outline='#ffffff')
            draw.text((70, 65), duration_text, fill='#ffffff', font=subtitle_font)
            
            # Save to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG', quality=95)
            img_bytes.seek(0)
            
            # Convert to base64 for data URL
            img_base64 = base64.b64encode(img_bytes.getvalue()).decode()
            
            # Return data URL
            return f"data:image/jpeg;base64,{img_base64}"
            
        except Exception as e:
            logger.error(f"Failed to create custom thumbnail: {str(e)}")
            # Fallback to default Loom thumbnail
            return f"https://cdn.loom.com/sessions/thumbnails/{video_id}-00001.jpg"

# ============================================================================
# 🎨 ADVANCED TEMPLATE ENGINE
# ============================================================================

class EmailTemplateEngine:
    """Advanced Jinja2-based email template engine with Loom integration"""
    
    def __init__(self, loom_service: Optional[LoomService] = None):
        self.loom_service = loom_service or LoomService()
        
        # Initialize Jinja2 environment with sandbox for security
        self.env = SandboxedEnvironment(
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self._register_filters()
        
        # Add custom functions
        self._register_functions()
    
    def _register_filters(self):
        """Register custom Jinja2 filters"""
        
        @self.env.filter
        def titlecase(value):
            """Convert to title case"""
            if not value:
                return ""
            return str(value).title()
        
        @self.env.filter
        def first_name_only(value):
            """Extract first name from full name"""
            if not value:
                return ""
            return str(value).split()[0]
        
        @self.env.filter
        def format_budget(value):
            """Format budget with currency"""
            if not value:
                return "budget not specified"
            try:
                amount = float(value)
                if amount >= 1000:
                    return f"${amount/1000:.1f}K"
                else:
                    return f"${amount:.0f}"
            except:
                return str(value)
        
        @self.env.filter
        def social_handle(url):
            """Extract handle from social media URL"""
            if not url:
                return ""
            
            # Extract handle from various social media URLs
            patterns = [
                r'instagram\.com/([^/?]+)',
                r'linkedin\.com/in/([^/?]+)',
                r'twitter\.com/([^/?]+)',
                r'tiktok\.com/@([^/?]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return f"@{match.group(1)}"
            
            return url
        
        @self.env.filter
        def time_of_day_greeting(value=None):
            """Generate greeting based on time of day"""
            now = datetime.now()
            hour = now.hour
            
            if 5 <= hour < 12:
                return "Good morning"
            elif 12 <= hour < 17:
                return "Good afternoon"
            elif 17 <= hour < 22:
                return "Good evening"
            else:
                return "Hope you're having a great evening"
    
    def _register_functions(self):
        """Register custom Jinja2 global functions"""
        
        def loom_video(video_id, lead_name="", custom_message="", 
                      lead_id=None, email_id=None):
            """Generate Loom video embed with personalized thumbnail"""
            
            # Get video info
            video_info = self.loom_service.get_video_info(video_id)
            if not video_info:
                return f"<!-- Loom video {video_id} not found -->"
            
            # Generate tracking URL
            if lead_id and email_id:
                video_url = self.loom_service.generate_tracking_url(
                    video_id, lead_id, email_id
                )
            else:
                video_url = video_info['share_url']
            
            # Create personalized thumbnail
            if lead_name:
                thumbnail_url = self.loom_service.create_custom_thumbnail(
                    video_id, lead_name, custom_message
                )
            else:
                thumbnail_url = video_info['thumbnail_url']
            
            # Generate HTML
            duration = video_info.get('duration', 0)
            duration_text = f"{duration//60}:{duration%60:02d}" if duration else "0:45"
            
            html = f"""
            <div style="text-align: center; margin: 30px 0; font-family: Arial, sans-serif;">
                <a href="{video_url}" target="_blank" style="text-decoration: none;">
                    <div style="position: relative; display: inline-block; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 24px rgba(0,0,0,0.15); transition: transform 0.3s ease;">
                        <img src="{thumbnail_url}" 
                             alt="Personal video message for {lead_name or 'you'}" 
                             style="max-width: 100%; height: auto; display: block;">
                        
                        <!-- Play button overlay -->
                        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                                   width: 80px; height: 80px; background: rgba(0,123,255,0.9); 
                                   border-radius: 50%; display: flex; align-items: center; justify-content: center;
                                   border: 3px solid white;">
                            <div style="width: 0; height: 0; border-left: 20px solid white; 
                                       border-top: 12px solid transparent; border-bottom: 12px solid transparent;
                                       margin-left: 4px;"></div>
                        </div>
                        
                        <!-- Duration badge -->
                        <div style="position: absolute; bottom: 12px; right: 12px; 
                                   background: rgba(0,0,0,0.8); color: white; padding: 4px 8px; 
                                   border-radius: 4px; font-size: 12px; font-weight: bold;">
                            {duration_text}
                        </div>
                    </div>
                    
                    <div style="margin-top: 15px; color: #007bff; font-size: 16px; font-weight: 600;">
                        ▶️ Watch my personal message for you
                    </div>
                    
                    <div style="margin-top: 5px; color: #666; font-size: 14px;">
                        {video_info.get('title', 'Personal Video Message')}
                    </div>
                </a>
            </div>
            """
            
            return html
        
        def smart_greeting(lead_data):
            """Generate smart greeting based on lead info"""
            first_name = lead_data.get('first_name', '')
            source = lead_data.get('source', '')
            industry = lead_data.get('industry', '')
            
            greetings = []
            
            if first_name:
                greetings.append(f"Hey {first_name}! 👋")
            else:
                greetings.append("Hello! 👋")
            
            if source == 'instagram':
                greetings.append("I came across your Instagram profile and was impressed!")
            elif source == 'linkedin':
                greetings.append("I found your LinkedIn profile and love what you're doing!")
            elif source == 'twitter':
                greetings.append("Saw your Twitter and had to reach out!")
            
            return " ".join(greetings)
        
        def pain_point_hook(lead_data):
            """Generate pain point hook based on lead industry/source"""
            industry = lead_data.get('industry', '').lower()
            source = lead_data.get('source', '').lower()
            grade = lead_data.get('grade', '').lower()
            
            hooks = {
                'fashion': "Tired of photographers who don't understand your vision?",
                'beauty': "Struggling to find a photographer who captures your true essence?",
                'fitness': "Need photos that show your dedication and results?",
                'business': "Looking for professional headshots that actually convert?",
                'creative': "Want photography that matches your artistic vision?",
            }
            
            if industry in hooks:
                return hooks[industry]
            
            # Fallback based on grade
            if grade == 'hot':
                return "Ready to take your content to the next level?"
            elif grade == 'warm':
                return "Looking for photography that stands out from the crowd?"
            else:
                return "Curious about premium photography services?"
        
        # Register functions
        self.env.globals['loom_video'] = loom_video
        self.env.globals['smart_greeting'] = smart_greeting
        self.env.globals['pain_point_hook'] = pain_point_hook
    
    def render_template(self, 
                       template_content: str, 
                       merge_data: Dict[str, Any],
                       loom_video_id: Optional[str] = None,
                       lead_id: Optional[int] = None,
                       email_id: Optional[int] = None) -> Tuple[str, Dict[str, Any]]:
        """Render email template with merge data and Loom integration"""
        
        try:
            # Prepare enhanced merge data
            enhanced_data = self._prepare_merge_data(merge_data)
            
            # Add Loom data if video ID provided
            if loom_video_id:
                enhanced_data.update({
                    'loom_video_id': loom_video_id,
                    'lead_id': lead_id,
                    'email_id': email_id
                })
            
            # Create template
            template = self.env.from_string(template_content)
            
            # Render with enhanced data
            rendered_content = template.render(**enhanced_data)
            
            # Extract tracking data
            tracking_data = self._extract_tracking_data(rendered_content)
            
            return rendered_content, tracking_data
            
        except TemplateError as e:
            logger.error(f"Template rendering error: {str(e)}")
            raise ValueError(f"Template error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error rendering template: {str(e)}")
            raise ValueError(f"Rendering failed: {str(e)}")
    
    def _prepare_merge_data(self, merge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare and enhance merge data with dynamic values"""
        
        enhanced_data = merge_data.copy()
        
        # Add current date/time data
        now = datetime.now()
        enhanced_data.update({
            'current_date': now.strftime('%B %d, %Y'),
            'current_time': now.strftime('%I:%M %p'),
            'day_of_week': now.strftime('%A'),
            'month': now.strftime('%B'),
            'year': now.year
        })
        
        # Ensure required fields have defaults
        defaults = {
            'first_name': 'there',
            'last_name': '',
            'full_name': enhanced_data.get('first_name', 'there'),
            'company': 'your company',
            'industry': 'your industry',
            'location': 'your area',
            'source': 'online',
            'grade': 'potential',
            'sender_name': 'Alex',
            'sender_company': 'Hunter Agency'
        }
        
        for key, default_value in defaults.items():
            if key not in enhanced_data or not enhanced_data[key]:
                enhanced_data[key] = default_value
        
        # Generate derived fields
        if enhanced_data.get('first_name') and enhanced_data.get('last_name'):
            enhanced_data['full_name'] = f"{enhanced_data['first_name']} {enhanced_data['last_name']}"
        
        # Social media handles
        for platform in ['instagram', 'linkedin', 'twitter']:
            url_key = f'{platform}_url'
            handle_key = f'{platform}_handle'
            if enhanced_data.get(url_key) and not enhanced_data.get(handle_key):
                enhanced_data[handle_key] = self._extract_social_handle(
                    enhanced_data[url_key], platform
                )
        
        return enhanced_data
    
    def _extract_social_handle(self, url: str, platform: str) -> str:
        """Extract social media handle from URL"""
        if not url:
            return ""
        
        patterns = {
            'instagram': r'instagram\.com/([^/?]+)',
            'linkedin': r'linkedin\.com/in/([^/?]+)',
            'twitter': r'twitter\.com/([^/?]+)'
        }
        
        pattern = patterns.get(platform)
        if pattern:
            match = re.search(pattern, url)
            if match:
                return f"@{match.group(1)}"
        
        return url
    
    def _extract_tracking_data(self, rendered_content: str) -> Dict[str, Any]:
        """Extract tracking data from rendered content"""
        tracking_data = {
            'loom_videos': [],
            'links': [],
            'images': []
        }
        
        # Extract Loom video references
        loom_pattern = r'loom\.com/share/([a-zA-Z0-9]+)'
        loom_matches = re.findall(loom_pattern, rendered_content)
        tracking_data['loom_videos'] = list(set(loom_matches))
        
        # Extract all links
        link_pattern = r'href="([^"]+)"'
        link_matches = re.findall(link_pattern, rendered_content)
        tracking_data['links'] = list(set(link_matches))
        
        # Extract images
        img_pattern = r'src="([^"]+)"'
        img_matches = re.findall(img_pattern, rendered_content)
        tracking_data['images'] = list(set(img_matches))
        
        return tracking_data
    
    def validate_template(self, template_content: str) -> Dict[str, Any]:
        """Validate template syntax and extract metadata"""
        try:
            # Parse template
            template = self.env.from_string(template_content)
            
            # Extract variables
            variables = list(template.meta.find_undeclared_variables(template.new_context()))
            
            # Test render with sample data
            sample_data = {
                'first_name': 'John',
                'last_name': 'Doe',
                'company': 'Acme Corp',
                'email': 'john@example.com'
            }
            
            try:
                test_render = template.render(**sample_data)
                render_success = True
            except Exception as e:
                render_success = False
                render_error = str(e)
            
            return {
                'valid': True,
                'variables': variables,
                'render_success': render_success,
                'render_error': render_error if not render_success else None,
                'estimated_length': len(template_content),
                'loom_videos': len(re.findall(r'loom_video\(', template_content))
            }
            
        except TemplateError as e:
            return {
                'valid': False,
                'error': str(e),
                'line': getattr(e, 'lineno', None)
            }

# ============================================================================
# 🎯 TEMPLATE LIBRARY
# ============================================================================

class TemplateLibrary:
    """Pre-built template library for different use cases"""
    
    COLD_OUTREACH_INTRO = """
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333;">{{ smart_greeting(lead_data) }}</h2>
        
        <p>{{ pain_point_hook(lead_data) }}</p>
        
        <p>I'm {{ sender_name }} from {{ sender_company }}, and I specialize in helping {{ industry }} professionals like yourself create stunning visual content that actually converts.</p>
        
        {% if loom_video_id %}
        {{ loom_video(loom_video_id, first_name, "I made this quick video explaining how we can help you", lead_id, email_id) }}
        {% endif %}
        
        <p>Here's what makes us different:</p>
        <ul>
            <li>✅ We understand {{ industry }} aesthetics</li>
            <li>✅ Fast turnaround (24-48 hours)</li>
            <li>✅ Unlimited revisions until perfect</li>
            <li>✅ {{ format_budget(budget_estimate) }} budget-friendly packages</li>
        </ul>
        
        <p>Interested in seeing some examples specific to your niche?</p>
        
        <p>Best,<br>{{ sender_name }}</p>
        
        <div style="margin-top: 30px; padding: 15px; background: #f8f9fa; border-radius: 8px; font-size: 12px; color: #666;">
            P.S. I noticed you're in {{ location }} - we have some amazing location ideas that would be perfect for your style!
        </div>
    </div>
    """
    
    FOLLOW_UP_NO_RESPONSE = """
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333;">{{ time_of_day_greeting() }}, {{ first_name }}!</h2>
        
        <p>I sent you a message last week about premium photography services for {{ industry }} professionals, but I know how busy things can get.</p>
        
        {% if loom_video_id %}
        {{ loom_video(loom_video_id, first_name, "Here's a quick 30-second example of our work", lead_id, email_id) }}
        {% endif %}
        
        <p>I wanted to share a quick success story:</p>
        
        <blockquote style="border-left: 4px solid #007bff; padding-left: 20px; margin: 20px 0; font-style: italic; color: #555;">
            "Working with {{ sender_name }} completely transformed my {{ source }} presence. My engagement went up 300% and I booked 5 new clients in the first month!" 
            <br><strong>- Sarah M., {{ industry }} Professional</strong>
        </blockquote>
        
        <p>Still interested in learning more? I can show you exactly how we achieved these results.</p>
        
        <p>Best,<br>{{ sender_name }}</p>
    </div>
    """
    
    PROPOSAL_READY = """
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333;">Your Custom Photography Proposal is Ready, {{ first_name }}! 🎉</h2>
        
        <p>Thanks for our conversation yesterday! Based on what you told me about your {{ industry }} goals, I've put together a custom proposal that I think you'll love.</p>
        
        {% if loom_video_id %}
        {{ loom_video(loom_video_id, first_name, "Personal walkthrough of your custom proposal", lead_id, email_id) }}
        {% endif %}
        
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; text-align: center; margin: 20px 0;">
            <h3 style="margin: 0 0 10px 0;">Your Investment</h3>
            <div style="font-size: 36px; font-weight: bold;">{{ format_budget(budget_estimate) }}</div>
            <div style="font-size: 14px; opacity: 0.9;">Complete photography package</div>
        </div>
        
        <p><strong>What's included:</strong></p>
        <ul>
            <li>✅ 2-hour premium photoshoot</li>
            <li>✅ 50+ professionally edited photos</li>
            <li>✅ Social media optimization</li>
            <li>✅ Commercial usage rights</li>
            <li>✅ 24-48 hour delivery</li>
        </ul>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="#" style="background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                📅 Book Your Session Now
            </a>
        </div>
        
        <p>Questions? Just reply to this email or call me directly at (555) 123-4567.</p>
        
        <p>Excited to create something amazing with you!</p>
        
        <p>{{ sender_name }}<br>{{ sender_company }}</p>
    </div>
    """

# ============================================================================
# 🎯 EXAMPLE USAGE
# ============================================================================

def demo_template_engine():
    """Demonstrate the template engine capabilities"""
    
    print("🎨 Email Template Engine Demo")
    print("=" * 50)
    
    # Initialize services
    loom_service = LoomService()
    template_engine = EmailTemplateEngine(loom_service)
    
    # Sample lead data
    lead_data = {
        'first_name': 'Sophie',
        'last_name': 'Martin',
        'email': 'sophie@example.com',
        'company': 'SM Photography',
        'industry': 'fashion',
        'location': 'Paris, France',
        'source': 'instagram',
        'grade': 'hot',
        'budget_estimate': 2500,
        'instagram_url': 'https://instagram.com/sophie_model',
        'linkedin_url': 'https://linkedin.com/in/sophie-martin'
    }
    
    # Test template rendering
    template_content = TemplateLibrary.COLD_OUTREACH_INTRO
    
    try:
        rendered_html, tracking_data = template_engine.render_template(
            template_content=template_content,
            merge_data=lead_data,
            loom_video_id='abc123def456',
            lead_id=123,
            email_id=456
        )
        
        print("✅ Template rendered successfully!")
        print(f"📊 Tracking data: {tracking_data}")
        print(f"📝 Content length: {len(rendered_html)} characters")
        
        # Validate template
        validation = template_engine.validate_template(template_content)
        print(f"✅ Template validation: {validation}")
        
    except Exception as e:
        print(f"❌ Template rendering failed: {str(e)}")

if __name__ == "__main__":
    demo_template_engine()