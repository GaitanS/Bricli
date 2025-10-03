import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.db import transaction
from pywebpush import webpush, WebPushException
import requests

from .models import Notification, NotificationPreference, PushSubscription

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications"""
    
    @staticmethod
    def create_notification(
        recipient: User,
        title: str,
        message: str,
        notification_type: str = 'system',
        priority: str = 'medium',
        sender: Optional[User] = None,
        action_url: Optional[str] = None,
        related_object_type: Optional[str] = None,
        related_object_id: Optional[int] = None,
        expires_at: Optional[datetime] = None,
        send_email: bool = True,
        send_push: bool = True
    ) -> Notification:
        """Create a new notification and optionally send via email/push"""
        
        try:
            with transaction.atomic():
                # Create the notification
                notification = Notification.objects.create(
                    recipient=recipient,
                    sender=sender,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    priority=priority,
                    action_url=action_url,
                    related_object_type=related_object_type,
                    related_object_id=related_object_id,
                    expires_at=expires_at
                )
                
                # Get user preferences
                preferences = NotificationPreference.objects.filter(
                    user=recipient
                ).first()
                
                # Send email notification if enabled
                if send_email and preferences and NotificationService._should_send_email(preferences, notification_type):
                    email_sent = EmailNotificationService.send_notification_email(notification)
                    notification.email_sent = email_sent
                
                # Send push notification if enabled
                if send_push and preferences and NotificationService._should_send_push(preferences, notification_type):
                    push_sent = PushNotificationService.send_push_notification(
                        user=recipient,
                        title=title,
                        message=message,
                        action_url=action_url,
                        notification_id=notification.id
                    )
                    notification.push_sent = push_sent
                
                notification.save()
                
                logger.info(f"Notification created: {notification.id} for user {recipient.username}")
                return notification
                
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            raise
    
    @staticmethod
    def _should_send_email(preferences: NotificationPreference, notification_type: str) -> bool:
        """Check if email should be sent based on user preferences"""
        type_mapping = {
            'new_order': preferences.email_new_orders,
            'quote': preferences.email_quotes,
            'payment': preferences.email_payments,
            'message': preferences.email_messages,
            'review': preferences.email_reviews,
            'system': preferences.email_system,
        }
        return type_mapping.get(notification_type, True)
    
    @staticmethod
    def _should_send_push(preferences: NotificationPreference, notification_type: str) -> bool:
        """Check if push notification should be sent based on user preferences"""
        type_mapping = {
            'new_order': preferences.push_new_orders,
            'quote': preferences.push_quotes,
            'payment': preferences.push_payments,
            'message': preferences.push_messages,
            'review': preferences.push_reviews,
            'system': preferences.push_system,
        }
        return type_mapping.get(notification_type, True)
    
    @staticmethod
    def bulk_create_notifications(
        recipients: List[User],
        title: str,
        message: str,
        notification_type: str = 'system',
        priority: str = 'medium',
        sender: Optional[User] = None,
        action_url: Optional[str] = None
    ) -> List[Notification]:
        """Create notifications for multiple recipients"""
        
        notifications = []
        for recipient in recipients:
            try:
                notification = NotificationService.create_notification(
                    recipient=recipient,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    priority=priority,
                    sender=sender,
                    action_url=action_url
                )
                notifications.append(notification)
            except Exception as e:
                logger.error(f"Error creating notification for user {recipient.username}: {str(e)}")
        
        return notifications
    
    @staticmethod
    def cleanup_expired_notifications():
        """Remove expired notifications"""
        now = timezone.now()
        expired_count = Notification.objects.filter(
            expires_at__lt=now
        ).delete()[0]
        
        logger.info(f"Cleaned up {expired_count} expired notifications")
        return expired_count
    
    @staticmethod
    def get_user_notification_stats(user: User) -> Dict[str, Any]:
        """Get notification statistics for a user"""
        notifications = Notification.objects.filter(recipient=user)
        now = timezone.now()
        
        return {
            'total': notifications.count(),
            'unread': notifications.filter(is_read=False).count(),
            'today': notifications.filter(created_at__date=now.date()).count(),
            'this_week': notifications.filter(
                created_at__gte=now - timedelta(days=7)
            ).count(),
            'by_type': dict(
                notifications.values('notification_type').annotate(
                    count=models.Count('id')
                ).values_list('notification_type', 'count')
            )
        }


class EmailNotificationService:
    """Service for sending email notifications"""
    
    @staticmethod
    def send_notification_email(notification: Notification) -> bool:
        """Send email notification"""
        try:
            # Check if user is in quiet hours
            preferences = NotificationPreference.objects.filter(
                user=notification.recipient
            ).first()
            
            if preferences and EmailNotificationService._is_quiet_hours(preferences):
                logger.info(f"Skipping email notification {notification.id} - quiet hours")
                return False
            
            # Prepare email context
            context = {
                'notification': notification,
                'user': notification.recipient,
                'site_name': getattr(settings, 'SITE_NAME', 'Bricli'),
                'site_url': getattr(settings, 'SITE_URL', 'https://bricli.ro'),
            }
            
            # Render email content
            subject = f"[Bricli] {notification.title}"
            html_message = render_to_string(
                'emails/notification_email.html',
                context
            )
            plain_message = strip_tags(html_message)
            
            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.recipient.email],
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Email notification sent: {notification.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification {notification.id}: {str(e)}")
            return False
    
    @staticmethod
    def _is_quiet_hours(preferences: NotificationPreference) -> bool:
        """Check if current time is within user's quiet hours"""
        if not preferences.quiet_hours_start or not preferences.quiet_hours_end:
            return False
        
        now = timezone.now().time()
        start = preferences.quiet_hours_start
        end = preferences.quiet_hours_end
        
        if start <= end:
            return start <= now <= end
        else:  # Quiet hours span midnight
            return now >= start or now <= end
    
    @staticmethod
    def send_digest_email(user: User, period: str = 'daily') -> bool:
        """Send notification digest email"""
        try:
            preferences = NotificationPreference.objects.filter(user=user).first()
            if not preferences or preferences.digest_frequency == 'never':
                return False
            
            # Calculate date range based on period
            now = timezone.now()
            if period == 'daily':
                start_date = now - timedelta(days=1)
            elif period == 'weekly':
                start_date = now - timedelta(days=7)
            elif period == 'monthly':
                start_date = now - timedelta(days=30)
            else:
                return False
            
            # Get notifications for the period
            notifications = Notification.objects.filter(
                recipient=user,
                created_at__gte=start_date,
                created_at__lt=now
            ).order_by('-created_at')
            
            if not notifications.exists():
                return False
            
            # Prepare email context
            context = {
                'user': user,
                'notifications': notifications,
                'period': period,
                'period_display': {
                    'daily': 'ultimele 24 de ore',
                    'weekly': 'ultima săptămână',
                    'monthly': 'ultima lună'
                }.get(period, period),
                'total_count': notifications.count(),
                'unread_count': notifications.filter(is_read=False).count(),
                'site_name': getattr(settings, 'SITE_NAME', 'Bricli'),
                'site_url': getattr(settings, 'SITE_URL', 'https://bricli.ro'),
            }
            
            # Render and send email
            subject = f"[Bricli] Rezumatul notificărilor - {context['period_display']}"
            html_message = render_to_string('emails/notification_digest.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Digest email sent to {user.username} for period {period}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending digest email to {user.username}: {str(e)}")
            return False


class PushNotificationService:
    """Service for sending push notifications"""
    
    @staticmethod
    def send_push_notification(
        user: User,
        title: str,
        message: str,
        action_url: Optional[str] = None,
        notification_id: Optional[int] = None,
        icon: Optional[str] = None,
        badge: Optional[str] = None
    ) -> bool:
        """Send push notification to user's devices"""
        
        try:
            # Get user's active push subscriptions
            subscriptions = PushSubscription.objects.filter(
                user=user,
                is_active=True
            )
            
            if not subscriptions.exists():
                logger.info(f"No active push subscriptions for user {user.username}")
                return False
            
            # Prepare notification payload
            payload = {
                'title': title,
                'body': message,
                'icon': icon or '/static/images/notification-icon.png',
                'badge': badge or '/static/images/badge-icon.png',
                'tag': f'notification-{notification_id}' if notification_id else 'general',
                'data': {
                    'url': action_url or '/notifications/',
                    'notification_id': notification_id,
                    'timestamp': timezone.now().isoformat()
                },
                'actions': [
                    {
                        'action': 'view',
                        'title': 'Vezi',
                        'icon': '/static/images/view-icon.png'
                    },
                    {
                        'action': 'dismiss',
                        'title': 'Închide',
                        'icon': '/static/images/close-icon.png'
                    }
                ],
                'requireInteraction': True,
                'silent': False
            }
            
            # VAPID configuration
            vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY', None)
            vapid_public_key = getattr(settings, 'VAPID_PUBLIC_KEY', None)
            vapid_claims = {
                'sub': getattr(settings, 'VAPID_SUBJECT', 'mailto:admin@bricli.ro')
            }
            
            if not vapid_private_key or not vapid_public_key:
                logger.error("VAPID keys not configured")
                return False
            
            success_count = 0
            failed_subscriptions = []
            
            # Send to each subscription
            for subscription in subscriptions:
                try:
                    webpush(
                        subscription_info={
                            'endpoint': subscription.endpoint,
                            'keys': {
                                'p256dh': subscription.p256dh_key,
                                'auth': subscription.auth_key
                            }
                        },
                        data=json.dumps(payload),
                        vapid_private_key=vapid_private_key,
                        vapid_claims=vapid_claims
                    )
                    
                    # Update last used timestamp
                    subscription.last_used = timezone.now()
                    subscription.save()
                    success_count += 1
                    
                except WebPushException as e:
                    logger.error(f"WebPush error for subscription {subscription.id}: {str(e)}")
                    
                    # Handle expired subscriptions
                    if e.response and e.response.status_code in [410, 413]:
                        failed_subscriptions.append(subscription)
                    
                except Exception as e:
                    logger.error(f"Error sending push to subscription {subscription.id}: {str(e)}")
                    failed_subscriptions.append(subscription)
            
            # Deactivate failed subscriptions
            if failed_subscriptions:
                PushSubscription.objects.filter(
                    id__in=[sub.id for sub in failed_subscriptions]
                ).update(is_active=False)
                
                logger.info(f"Deactivated {len(failed_subscriptions)} failed push subscriptions")
            
            logger.info(f"Push notifications sent: {success_count}/{subscriptions.count()} for user {user.username}")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error sending push notifications to {user.username}: {str(e)}")
            return False
    
    @staticmethod
    def register_push_subscription(
        user: User,
        endpoint: str,
        p256dh_key: str,
        auth_key: str,
        user_agent: Optional[str] = None
    ) -> PushSubscription:
        """Register or update a push subscription"""
        
        try:
            subscription, created = PushSubscription.objects.get_or_create(
                user=user,
                endpoint=endpoint,
                defaults={
                    'p256dh_key': p256dh_key,
                    'auth_key': auth_key,
                    'user_agent': user_agent,
                    'is_active': True
                }
            )
            
            if not created:
                # Update existing subscription
                subscription.p256dh_key = p256dh_key
                subscription.auth_key = auth_key
                subscription.user_agent = user_agent
                subscription.is_active = True
                subscription.save()
            
            logger.info(f"Push subscription {'created' if created else 'updated'} for user {user.username}")
            return subscription
            
        except Exception as e:
            logger.error(f"Error registering push subscription for {user.username}: {str(e)}")
            raise
    
    @staticmethod
    def unregister_push_subscription(user: User, endpoint: str) -> bool:
        """Unregister a push subscription"""
        
        try:
            subscription = PushSubscription.objects.get(
                user=user,
                endpoint=endpoint
            )
            subscription.delete()
            
            logger.info(f"Push subscription unregistered for user {user.username}")
            return True
            
        except PushSubscription.DoesNotExist:
            logger.warning(f"Push subscription not found for user {user.username}")
            return False
        except Exception as e:
            logger.error(f"Error unregistering push subscription for {user.username}: {str(e)}")
            return False
    
    @staticmethod
    def cleanup_inactive_subscriptions():
        """Remove inactive push subscriptions"""
        cutoff_date = timezone.now() - timedelta(days=30)
        
        inactive_count = PushSubscription.objects.filter(
            models.Q(is_active=False) | models.Q(last_used__lt=cutoff_date)
        ).delete()[0]
        
        logger.info(f"Cleaned up {inactive_count} inactive push subscriptions")
        return inactive_count


class NotificationTemplateService:
    """Service for managing notification templates"""
    
    TEMPLATES = {
        'new_order': {
            'title': 'Comandă nouă primită',
            'message': 'Ați primit o comandă nouă de la {client_name}.',
            'email_template': 'emails/new_order_notification.html'
        },
        'quote_received': {
            'title': 'Ofertă primită',
            'message': 'Ați primit o ofertă de la {craftsman_name}.',
            'email_template': 'emails/quote_notification.html'
        },
        'payment_received': {
            'title': 'Plată primită',
            'message': 'Ați primit o plată în valoare de {amount} RON.',
            'email_template': 'emails/payment_notification.html'
        },
        'message_received': {
            'title': 'Mesaj nou',
            'message': 'Ați primit un mesaj nou de la {sender_name}.',
            'email_template': 'emails/message_notification.html'
        },
        'review_received': {
            'title': 'Recenzie nouă',
            'message': 'Ați primit o recenzie nouă cu {rating} stele.',
            'email_template': 'emails/review_notification.html'
        },
        'system_update': {
            'title': 'Actualizare sistem',
            'message': 'Sistemul a fost actualizat cu funcționalități noi.',
            'email_template': 'emails/system_notification.html'
        }
    }
    
    @staticmethod
    def get_template(notification_type: str) -> Dict[str, str]:
        """Get notification template by type"""
        return NotificationTemplateService.TEMPLATES.get(
            notification_type,
            {
                'title': 'Notificare',
                'message': 'Aveți o notificare nouă.',
                'email_template': 'emails/generic_notification.html'
            }
        )
    
    @staticmethod
    def format_notification(notification_type: str, **kwargs) -> Dict[str, str]:
        """Format notification with provided data"""
        template = NotificationTemplateService.get_template(notification_type)
        
        return {
            'title': template['title'].format(**kwargs),
            'message': template['message'].format(**kwargs),
            'email_template': template['email_template']
        }