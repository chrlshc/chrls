#!/usr/bin/env python3
"""
⚡ HUNTER AGENCY - Email Sequence Automation Engine
Mass personalized email campaigns with intelligent triggers & scheduling
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import logging
from celery import Celery
from celery.schedules import crontab
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import requests
import json
import time
from dataclasses import dataclass
from enum import Enum

from .models import (
    EmailSequence, SequenceStep, SequenceEnrollment, Email, 
    EmailTemplate, Lead, EmailStatus, SequenceStatus, TriggerType
)
from .template_engine import EmailTemplateEngine, LoomService

logger = logging.getLogger(__name__)

# ============================================================================
# 🔧 CELERY CONFIGURATION
# ============================================================================

# Initialize Celery for background tasks
celery_app = Celery(
    'email_automation',
    broker='redis://localhost:6379/1',
    backend='redis://localhost:6379/1'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        'process-email-sequences': {
            'task': 'email_automation.process_sequences',
            'schedule': crontab(minute='*/5'),  # Every 5 minutes
        },
        'send-scheduled-emails': {
            'task': 'email_automation.send_scheduled_emails',
            'schedule': crontab(minute='*/2'),  # Every 2 minutes
        },
        'update-email-metrics': {
            'task': 'email_automation.update_metrics',
            'schedule': crontab(minute='*/10'),  # Every 10 minutes
        },
    }
)

# ============================================================================
# 📧 EMAIL DELIVERY SERVICES
# ============================================================================

class EmailProvider(str, Enum):
    SMTP = "smtp"
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"
    SES = "ses"

@dataclass
class EmailDeliveryResult:
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    provider_response: Optional[Dict] = None

class EmailDeliveryService:
    """Handle email delivery through multiple providers"""
    
    def __init__(self, provider: EmailProvider = EmailProvider.SMTP):
        self.provider = provider
        self.smtp_config = {
            'host': 'smtp.gmail.com',
            'port': 587,
            'username': 'your-email@gmail.com',
            'password': 'your-app-password',
            'use_tls': True
        }
        self.sendgrid_api_key = None  # Set from environment
        self.mailgun_config = {}
    
    async def send_email(self, 
                        to_email: str,
                        to_name: str,
                        from_email: str,
                        from_name: str,
                        subject: str,
                        html_content: str,
                        text_content: Optional[str] = None) -> EmailDeliveryResult:
        """Send email through configured provider"""
        
        try:
            if self.provider == EmailProvider.SMTP:
                return await self._send_via_smtp(
                    to_email, to_name, from_email, from_name, subject, html_content, text_content
                )
            elif self.provider == EmailProvider.SENDGRID:
                return await self._send_via_sendgrid(
                    to_email, to_name, from_email, from_name, subject, html_content, text_content
                )
            else:
                return EmailDeliveryResult(
                    success=False, 
                    error=f"Provider {self.provider} not implemented"
                )
                
        except Exception as e:
            logger.error(f"Email delivery failed: {str(e)}")
            return EmailDeliveryResult(success=False, error=str(e))
    
    async def _send_via_smtp(self, to_email, to_name, from_email, from_name, 
                           subject, html_content, text_content) -> EmailDeliveryResult:
        """Send via SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = f"{to_name} <{to_email}>"
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                if self.smtp_config['use_tls']:
                    server.starttls()
                
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                
                result = server.send_message(msg)
                
                return EmailDeliveryResult(
                    success=True,
                    message_id=f"smtp_{int(time.time())}",
                    provider_response={'smtp_result': str(result)}
                )
                
        except Exception as e:
            return EmailDeliveryResult(success=False, error=str(e))
    
    async def _send_via_sendgrid(self, to_email, to_name, from_email, from_name,
                               subject, html_content, text_content) -> EmailDeliveryResult:
        """Send via SendGrid API"""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            if not self.sendgrid_api_key:
                return EmailDeliveryResult(success=False, error="SendGrid API key not configured")
            
            sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_api_key)
            
            mail = Mail(
                from_email=Email(from_email, from_name),
                to_emails=To(to_email, to_name),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            if text_content:
                mail.content = [
                    Content("text/plain", text_content),
                    Content("text/html", html_content)
                ]
            
            response = sg.send(mail)
            
            return EmailDeliveryResult(
                success=response.status_code == 202,
                message_id=response.headers.get('X-Message-Id'),
                provider_response={
                    'status_code': response.status_code,
                    'headers': dict(response.headers)
                }
            )
            
        except Exception as e:
            return EmailDeliveryResult(success=False, error=str(e))

# ============================================================================
# ⚡ SEQUENCE AUTOMATION ENGINE
# ============================================================================

class SequenceAutomationEngine:
    """Core automation engine for email sequences"""
    
    def __init__(self, db: Session):
        self.db = db
        self.template_engine = EmailTemplateEngine()
        self.delivery_service = EmailDeliveryService()
        self.rate_limits = {
            'emails_per_minute': 10,
            'emails_per_hour': 100,
            'emails_per_day': 500
        }
    
    async def enroll_lead_in_sequence(self, 
                                    lead_id: int, 
                                    sequence_id: int, 
                                    enrolled_by: str = "system") -> bool:
        """Enroll a lead in an email sequence"""
        try:
            # Check if lead is already enrolled
            existing = self.db.query(SequenceEnrollment).filter(
                and_(
                    SequenceEnrollment.lead_id == lead_id,
                    SequenceEnrollment.sequence_id == sequence_id,
                    SequenceEnrollment.status == SequenceStatus.ACTIVE
                )
            ).first()
            
            if existing:
                logger.warning(f"Lead {lead_id} already enrolled in sequence {sequence_id}")
                return False
            
            # Get sequence and lead
            sequence = self.db.query(EmailSequence).filter(EmailSequence.id == sequence_id).first()
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            
            if not sequence or not lead:
                logger.error(f"Sequence {sequence_id} or Lead {lead_id} not found")
                return False
            
            # Check if lead matches sequence targeting
            if not self._lead_matches_targeting(lead, sequence):
                logger.info(f"Lead {lead_id} doesn't match targeting for sequence {sequence_id}")
                return False
            
            # Create enrollment
            enrollment = SequenceEnrollment(
                sequence_id=sequence_id,
                lead_id=lead_id,
                enrolled_by=enrolled_by,
                status=SequenceStatus.ACTIVE,
                current_step=1,
                next_email_at=self._calculate_next_email_time(sequence, 1)
            )
            
            self.db.add(enrollment)
            self.db.commit()
            
            logger.info(f"✅ Enrolled lead {lead_id} in sequence {sequence_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enroll lead {lead_id} in sequence {sequence_id}: {str(e)}")
            return False
    
    def _lead_matches_targeting(self, lead: Lead, sequence: EmailSequence) -> bool:
        """Check if lead matches sequence targeting criteria"""
        
        # Check grade targeting
        if sequence.target_grades:
            if lead.grade not in sequence.target_grades:
                return False
        
        # Check source targeting
        if sequence.target_sources:
            if lead.source not in sequence.target_sources:
                return False
        
        # Check industry targeting
        if sequence.target_industries:
            if lead.industry not in sequence.target_industries:
                return False
        
        return True
    
    def _calculate_next_email_time(self, sequence: EmailSequence, step_number: int) -> datetime:
        """Calculate when the next email should be sent"""
        
        # Get sequence step
        step = self.db.query(SequenceStep).filter(
            and_(
                SequenceStep.sequence_id == sequence.id,
                SequenceStep.step_number == step_number
            )
        ).first()
        
        if not step:
            return datetime.utcnow()
        
        # Calculate delay
        delay = timedelta(
            days=step.delay_days,
            hours=step.delay_hours,
            minutes=step.delay_minutes
        )
        
        # Add delay to current time
        next_time = datetime.utcnow() + delay
        
        # Adjust for sending schedule (business hours, etc.)
        next_time = self._adjust_for_schedule(next_time, sequence)
        
        return next_time
    
    def _adjust_for_schedule(self, send_time: datetime, sequence: EmailSequence) -> datetime:
        """Adjust send time based on sequence schedule settings"""
        
        schedule = sequence.sending_schedule or {}
        
        # Default business hours: Monday-Friday, 9 AM - 5 PM
        business_days = schedule.get('business_days', [0, 1, 2, 3, 4])  # Mon-Fri
        business_hours = schedule.get('business_hours', [9, 17])  # 9 AM - 5 PM
        
        # Adjust day of week
        while send_time.weekday() not in business_days:
            send_time = send_time + timedelta(days=1)
        
        # Adjust hour
        if send_time.hour < business_hours[0]:
            send_time = send_time.replace(hour=business_hours[0], minute=0, second=0)
        elif send_time.hour >= business_hours[1]:
            # Move to next business day
            send_time = send_time + timedelta(days=1)
            send_time = send_time.replace(hour=business_hours[0], minute=0, second=0)
            
            # Check if next day is business day
            while send_time.weekday() not in business_days:
                send_time = send_time + timedelta(days=1)
        
        return send_time
    
    async def process_sequences(self) -> Dict[str, int]:
        """Process all active sequences and prepare emails"""
        
        stats = {
            'enrollments_processed': 0,
            'emails_scheduled': 0,
            'errors': 0
        }
        
        try:
            # Get enrollments ready for next email
            ready_enrollments = self.db.query(SequenceEnrollment).filter(
                and_(
                    SequenceEnrollment.status == SequenceStatus.ACTIVE,
                    SequenceEnrollment.next_email_at <= datetime.utcnow()
                )
            ).limit(100).all()  # Process in batches
            
            for enrollment in ready_enrollments:
                try:
                    await self._process_enrollment(enrollment)
                    stats['enrollments_processed'] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to process enrollment {enrollment.id}: {str(e)}")
                    stats['errors'] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error processing sequences: {str(e)}")
            stats['errors'] += 1
            return stats
    
    async def _process_enrollment(self, enrollment: SequenceEnrollment):
        """Process a single enrollment and create next email"""
        
        # Get sequence step
        step = self.db.query(SequenceStep).filter(
            and_(
                SequenceStep.sequence_id == enrollment.sequence_id,
                SequenceStep.step_number == enrollment.current_step
            )
        ).first()
        
        if not step:
            # No more steps, complete sequence
            enrollment.status = SequenceStatus.COMPLETED
            enrollment.completed_at = datetime.utcnow()
            self.db.commit()
            return
        
        # Get lead and template
        lead = self.db.query(Lead).filter(Lead.id == enrollment.lead_id).first()
        template = self.db.query(EmailTemplate).filter(EmailTemplate.id == step.template_id).first()
        
        if not lead or not template:
            logger.error(f"Lead {enrollment.lead_id} or template {step.template_id} not found")
            return
        
        # Check conditions
        if not self._check_step_conditions(step, lead, enrollment):
            # Skip this step, move to next
            await self._advance_to_next_step(enrollment)
            return
        
        # Create and schedule email
        email = await self._create_email_from_template(
            template=template,
            lead=lead,
            enrollment=enrollment,
            step=step
        )
        
        if email:
            # Update enrollment
            enrollment.current_step += 1
            enrollment.emails_sent += 1
            enrollment.next_email_at = self._calculate_next_email_time(
                enrollment.sequence, 
                enrollment.current_step
            )
            
            self.db.commit()
            
            logger.info(f"📧 Scheduled email {email.id} for lead {lead.id}")
    
    def _check_step_conditions(self, step: SequenceStep, lead: Lead, enrollment: SequenceEnrollment) -> bool:
        """Check if step conditions are met"""
        
        # Check send conditions
        send_conditions = step.send_conditions or {}
        
        # Example conditions
        if 'min_lead_score' in send_conditions:
            if lead.ai_score < send_conditions['min_lead_score']:
                return False
        
        if 'required_grade' in send_conditions:
            if lead.grade != send_conditions['required_grade']:
                return False
        
        # Check skip conditions
        skip_conditions = step.skip_conditions or {}
        
        if 'skip_if_replied' in skip_conditions and skip_conditions['skip_if_replied']:
            # Check if lead has replied to any previous emails
            has_replied = self.db.query(Email).filter(
                and_(
                    Email.lead_id == lead.id,
                    Email.replied_at.isnot(None)
                )
            ).first()
            
            if has_replied:
                return False
        
        return True
    
    async def _advance_to_next_step(self, enrollment: SequenceEnrollment):
        """Advance enrollment to next step"""
        enrollment.current_step += 1
        enrollment.next_email_at = self._calculate_next_email_time(
            enrollment.sequence,
            enrollment.current_step
        )
        self.db.commit()
    
    async def _create_email_from_template(self, 
                                        template: EmailTemplate,
                                        lead: Lead,
                                        enrollment: SequenceEnrollment,
                                        step: SequenceStep) -> Optional[Email]:
        """Create email from template with personalization"""
        
        try:
            # Prepare merge data
            merge_data = {
                'first_name': lead.name.split()[0] if lead.name else '',
                'last_name': ' '.join(lead.name.split()[1:]) if lead.name and len(lead.name.split()) > 1 else '',
                'full_name': lead.name or '',
                'email': lead.email,
                'phone': lead.phone,
                'company': getattr(lead, 'company', ''),
                'industry': lead.industry,
                'location': lead.location,
                'source': lead.source,
                'grade': lead.grade,
                'budget_estimate': lead.budget_estimate,
                'instagram_url': lead.instagram_url,
                'linkedin_url': lead.linkedin_url,
                'twitter_url': lead.twitter_url
            }
            
            # Create email record
            email = Email(
                template_id=template.id,
                sequence_step_id=step.id,
                lead_id=lead.id,
                enrollment_id=enrollment.id,
                to_email=lead.email,
                to_name=lead.name,
                from_email="alex@hunter-agency.com",  # Configure
                from_name="Alex Hunter",
                status=EmailStatus.SCHEDULED,
                scheduled_at=datetime.utcnow() + timedelta(minutes=1),  # Send soon
                merge_data=merge_data,
                loom_video_id=template.loom_video_id
            )
            
            # Render template
            rendered_html, tracking_data = self.template_engine.render_template(
                template_content=template.html_template,
                merge_data=merge_data,
                loom_video_id=template.loom_video_id,
                lead_id=lead.id,
                email_id=None  # Will be set after commit
            )
            
            # Render subject
            subject_template = self.template_engine.env.from_string(template.subject_template)
            rendered_subject = subject_template.render(**merge_data)
            
            # Update email with rendered content
            email.subject = rendered_subject
            email.html_content = rendered_html
            
            # Add to database
            self.db.add(email)
            self.db.commit()
            self.db.refresh(email)
            
            return email
            
        except Exception as e:
            logger.error(f"Failed to create email from template {template.id}: {str(e)}")
            return None

# ============================================================================
# 🚀 CELERY TASKS
# ============================================================================

@celery_app.task(bind=True, max_retries=3)
def process_sequences(self):
    """Celery task to process email sequences"""
    from .database import get_db
    
    db = next(get_db())
    engine = SequenceAutomationEngine(db)
    
    try:
        stats = asyncio.run(engine.process_sequences())
        logger.info(f"Processed sequences: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Sequence processing failed: {str(e)}")
        raise self.retry(countdown=60, exc=e)

@celery_app.task(bind=True, max_retries=3)
def send_scheduled_emails(self):
    """Celery task to send scheduled emails"""
    from .database import get_db
    
    db = next(get_db())
    engine = SequenceAutomationEngine(db)
    
    try:
        # Get emails ready to send
        ready_emails = db.query(Email).filter(
            and_(
                Email.status == EmailStatus.SCHEDULED,
                Email.scheduled_at <= datetime.utcnow()
            )
        ).limit(50).all()  # Rate limit
        
        sent_count = 0
        error_count = 0
        
        for email in ready_emails:
            try:
                # Send email
                result = asyncio.run(engine.delivery_service.send_email(
                    to_email=email.to_email,
                    to_name=email.to_name,
                    from_email=email.from_email,
                    from_name=email.from_name,
                    subject=email.subject,
                    html_content=email.html_content,
                    text_content=email.text_content
                ))
                
                if result.success:
                    email.status = EmailStatus.SENT
                    email.sent_at = datetime.utcnow()
                    email.provider_message_id = result.message_id
                    email.provider_response = result.provider_response
                    sent_count += 1
                    
                    logger.info(f"✅ Sent email {email.id} to {email.to_email}")
                else:
                    email.status = EmailStatus.BOUNCED
                    email.bounce_reason = result.error
                    error_count += 1
                    
                    logger.error(f"❌ Failed to send email {email.id}: {result.error}")
                
                db.commit()
                
                # Rate limiting
                await asyncio.sleep(0.1)  # 100ms between emails
                
            except Exception as e:
                logger.error(f"Error sending email {email.id}: {str(e)}")
                error_count += 1
        
        stats = {
            'sent': sent_count,
            'errors': error_count,
            'total_processed': len(ready_emails)
        }
        
        logger.info(f"Email sending stats: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Email sending task failed: {str(e)}")
        raise self.retry(countdown=30, exc=e)

@celery_app.task
def trigger_sequence_for_lead(lead_id: int, trigger_type: str, trigger_data: Dict = None):
    """Trigger sequences based on lead events"""
    from .database import get_db
    
    db = next(get_db())
    engine = SequenceAutomationEngine(db)
    
    try:
        # Find sequences with matching trigger
        sequences = db.query(EmailSequence).filter(
            and_(
                EmailSequence.is_active == True,
                EmailSequence.trigger_type == trigger_type
            )
        ).all()
        
        enrollments_created = 0
        
        for sequence in sequences:
            success = asyncio.run(engine.enroll_lead_in_sequence(
                lead_id=lead_id,
                sequence_id=sequence.id,
                enrolled_by="trigger_system"
            ))
            
            if success:
                enrollments_created += 1
        
        logger.info(f"Created {enrollments_created} enrollments for lead {lead_id} trigger {trigger_type}")
        return {'enrollments_created': enrollments_created}
        
    except Exception as e:
        logger.error(f"Trigger processing failed for lead {lead_id}: {str(e)}")
        return {'error': str(e)}

# ============================================================================
# 🎯 SEQUENCE MANAGER
# ============================================================================

class SequenceManager:
    """High-level sequence management interface"""
    
    def __init__(self, db: Session):
        self.db = db
        self.automation_engine = SequenceAutomationEngine(db)
    
    def create_cold_outreach_sequence(self, 
                                    name: str,
                                    target_grades: List[str] = None,
                                    target_sources: List[str] = None) -> EmailSequence:
        """Create a complete cold outreach sequence"""
        
        # Create sequence
        sequence = EmailSequence(
            name=name,
            slug=name.lower().replace(' ', '_'),
            campaign_type='cold_outreach',
            trigger_type='lead_qualified',
            target_grades=target_grades or ['hot', 'warm'],
            target_sources=target_sources or ['instagram', 'linkedin'],
            max_emails_per_day=50,
            sending_schedule={
                'business_days': [0, 1, 2, 3, 4],  # Mon-Fri
                'business_hours': [9, 17]  # 9 AM - 5 PM
            }
        )
        
        self.db.add(sequence)
        self.db.commit()
        self.db.refresh(sequence)
        
        # Add sequence steps (would typically use pre-created templates)
        steps_data = [
            {
                'step_number': 1,
                'name': 'Cold Outreach Intro',
                'delay_days': 0,
                'delay_hours': 0,
                'delay_minutes': 5,
                'template_id': 1  # Use existing template
            },
            {
                'step_number': 2,
                'name': 'Follow-up No Response',
                'delay_days': 3,
                'delay_hours': 0,
                'delay_minutes': 0,
                'template_id': 2
            },
            {
                'step_number': 3,
                'name': 'Final Follow-up',
                'delay_days': 7,
                'delay_hours': 0,
                'delay_minutes': 0,
                'template_id': 3
            }
        ]
        
        for step_data in steps_data:
            step = SequenceStep(
                sequence_id=sequence.id,
                **step_data
            )
            self.db.add(step)
        
        self.db.commit()
        
        logger.info(f"✅ Created cold outreach sequence: {sequence.name}")
        return sequence
    
    async def start_sequence_for_leads(self, 
                                     sequence_id: int, 
                                     lead_filters: Dict = None) -> int:
        """Start sequence for multiple leads based on filters"""
        
        # Build lead query
        query = self.db.query(Lead)
        
        if lead_filters:
            if 'grades' in lead_filters:
                query = query.filter(Lead.grade.in_(lead_filters['grades']))
            
            if 'sources' in lead_filters:
                query = query.filter(Lead.source.in_(lead_filters['sources']))
            
            if 'min_score' in lead_filters:
                query = query.filter(Lead.ai_score >= lead_filters['min_score'])
        
        leads = query.all()
        enrolled_count = 0
        
        for lead in leads:
            success = await self.automation_engine.enroll_lead_in_sequence(
                lead_id=lead.id,
                sequence_id=sequence_id,
                enrolled_by="batch_enrollment"
            )
            
            if success:
                enrolled_count += 1
        
        logger.info(f"✅ Enrolled {enrolled_count} leads in sequence {sequence_id}")
        return enrolled_count

# ============================================================================
# 🎯 EXAMPLE USAGE
# ============================================================================

def demo_sequence_automation():
    """Demonstrate sequence automation"""
    
    print("⚡ Email Sequence Automation Demo")
    print("=" * 50)
    
    # This would be integrated with your FastAPI app
    print("🔄 Background tasks:")
    print("  • process_sequences - Every 5 minutes")
    print("  • send_scheduled_emails - Every 2 minutes")
    print("  • update_metrics - Every 10 minutes")
    print("")
    
    print("🎯 Trigger examples:")
    print("  • Lead qualified → Cold outreach sequence")
    print("  • No response after 3 days → Follow-up sequence")
    print("  • Lead score increase → Upgrade sequence")
    print("")
    
    print("📧 Email personalization:")
    print("  • Merge tags: {{first_name}}, {{industry}}, {{budget}}")
    print("  • Loom videos: Custom thumbnails with lead name")
    print("  • Smart content: Based on lead grade/source")
    print("")
    
    print("🚀 Ready to generate conversions at scale!")

if __name__ == "__main__":
    demo_sequence_automation()