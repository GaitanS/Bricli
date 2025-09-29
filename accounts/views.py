from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView as BaseLoginView, LogoutView as BaseLogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DetailView, ListView, UpdateView, TemplateView, FormView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import models
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.files.storage import default_storage
from .models import User, CraftsmanProfile, CraftsmanPortfolio, County, City
from .forms import (
    UserRegistrationForm, CraftsmanRegistrationForm, ProfileUpdateForm,
    SimpleUserRegistrationForm, SimpleCraftsmanRegistrationForm,
    CraftsmanProfileForm, CraftsmanPortfolioForm, BulkPortfolioUploadForm, CraftsmanSkillsForm
)


class RegisterView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Contul a fost creat cu succes! Te poți conecta acum.')
        return response


class SimpleRegisterView(CreateView):
    """Simplified registration view similar to MyHammer"""
    model = User
    form_class = SimpleUserRegistrationForm
    template_name = 'accounts/simple_register.html'
    success_url = reverse_lazy('core:home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.user_type == 'craftsman':
                return redirect('services:craftsman_services')
            else:
                return redirect('services:my_orders')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, 'Contul a fost creat cu succes! Bun venit pe Bricli!')
        return response


class SimpleCraftsmanRegisterView(CreateView):
    """Simplified craftsman registration view"""
    model = User
    form_class = SimpleCraftsmanRegistrationForm
    template_name = 'accounts/simple_craftsman_register.html'
    success_url = reverse_lazy('core:home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.user_type == 'craftsman':
                return redirect('services:craftsman_services')
            else:
                return redirect('services:my_orders')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Save the user and profile normally first
        user = form.save(commit=True)  # This creates user, profile, and services

        # Then deactivate the user for email confirmation
        user.is_active = False
        user.save()

        # Send confirmation email
        self.send_confirmation_email(user)

        # Don't login the user yet - they need to confirm email first
        messages.success(
            self.request,
            f'Contul a fost creat cu succes! Am trimis un email de confirmare la {user.email}. '
            'Te rugăm să verifici emailul și să apeși pe linkul de confirmare pentru a-ți activa contul.'
        )
        return redirect('accounts:registration_complete')

    def send_confirmation_email(self, user):
        """Send email confirmation to new user"""
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        from django.contrib.auth.tokens import default_token_generator
        from django.conf import settings

        # Generate confirmation token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Build confirmation URL
        confirmation_url = self.request.build_absolute_uri(
            f'/accounts/confirm-email/{uid}/{token}/'
        )

        # Email content
        subject = 'Confirmă-ți contul Bricli'
        message = f"""
Bună {user.get_full_name()},

Bun venit pe Bricli! Pentru a-ți activa contul de meșter, te rugăm să apeși pe linkul de mai jos:

{confirmation_url}

Dacă nu te-ai înregistrat pe Bricli, poți ignora acest email.

Cu respect,
Echipa Bricli
        """

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            # Log error but don't fail registration
            print(f"Failed to send confirmation email: {e}")
            # Activate user immediately if email fails
            user.is_active = True
            user.save()
            messages.warning(
                self.request,
                'Contul a fost creat dar nu am putut trimite emailul de confirmare. '
                'Contul tău este activ și te poți conecta acum.'
            )


class CraftsmanRegisterView(CreateView):
    model = User
    form_class = CraftsmanRegistrationForm
    template_name = 'accounts/craftsman_register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.user_type = 'craftsman'
        user.save()

        # Create craftsman profile
        CraftsmanProfile.objects.create(user=user)

        messages.success(self.request, 'Contul de meșter a fost creat cu succes! Te poți conecta acum.')
        return redirect(self.success_url)


class LoginView(BaseLoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('core:home')


class LogoutView(BaseLogoutView):
    template_name = 'registration/logged_out.html'
    next_page = reverse_lazy('core:home')
    http_method_names = ['get', 'post', 'options']

    def get(self, request, *args, **kwargs):
        """Handle GET requests for logout"""
        from django.contrib.auth import logout
        logout(request)
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        """Handle POST requests for logout"""
        return super().post(request, *args, **kwargs)


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.user_type == 'craftsman':
            try:
                context['craftsman_profile'] = self.request.user.craftsman_profile
            except CraftsmanProfile.DoesNotExist:
                CraftsmanProfile.objects.create(user=self.request.user)
                context['craftsman_profile'] = self.request.user.craftsman_profile
        return context


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileUpdateForm
    template_name = 'accounts/edit_profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user





class CraftsmenListView(ListView):
    model = CraftsmanProfile
    template_name = 'accounts/craftsmen_list.html'
    context_object_name = 'craftsmen'
    paginate_by = 12

    def get_queryset(self):
        queryset = CraftsmanProfile.objects.filter(user__is_active=True)

        # Filter by county
        county = self.request.GET.get('county')
        if county:
            queryset = queryset.filter(county_id=county)

        # Filter by service
        service = self.request.GET.get('service')
        if service:
            queryset = queryset.filter(services__service_id=service)

        # Search by name or company
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(user__first_name__icontains=search) |
                models.Q(user__last_name__icontains=search) |
                models.Q(company_name__icontains=search)
            )

        return queryset.order_by('-average_rating', '-total_reviews')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['counties'] = County.objects.all()
        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile view"""
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class EditProfileView(LoginRequiredMixin, UpdateView):
    """Edit user profile"""
    model = User
    form_class = ProfileUpdateForm
    template_name = 'accounts/edit_profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        # Handle profile picture removal
        if self.request.POST.get('remove_picture') == 'true':
            if self.request.user.profile_picture:
                self.request.user.profile_picture.delete()
                self.request.user.profile_picture = None
                self.request.user.save()

        messages.success(self.request, 'Profilul a fost actualizat cu succes!')
        return super().form_valid(form)


class CraftsmenListView(ListView):
    model = CraftsmanProfile
    template_name = 'accounts/craftsmen_list.html'
    context_object_name = 'craftsmen'
    paginate_by = 12

    def get_queryset(self):
        queryset = CraftsmanProfile.objects.filter(user__is_active=True)

        # Filter by trade
        trade = self.request.GET.get('trade')
        if trade:
            queryset = queryset.filter(trade=trade)

        # Filter by county
        county = self.request.GET.get('county')
        if county:
            queryset = queryset.filter(county_id=county)

        # Filter by rating
        rating = self.request.GET.get('rating')
        if rating:
            queryset = queryset.filter(average_rating__gte=rating)

        return queryset.order_by('-user__is_verified', '-average_rating', '-total_reviews')

    def get_context_data(self, **kwargs):
        from services.models import Service
        context = super().get_context_data(**kwargs)
        context.update({
            'counties': County.objects.all().order_by('name'),
            'total_craftsmen': CraftsmanProfile.objects.filter(user__is_active=True).count(),
            'verified_craftsmen': CraftsmanProfile.objects.filter(
                user__is_active=True, user__is_verified=True
            ).count(),
            'total_services': Service.objects.filter(is_active=True).count(),
        })
        return context


class CraftsmanDetailView(DetailView):
    model = CraftsmanProfile
    template_name = 'accounts/craftsman_detail.html'
    context_object_name = 'craftsman'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Reviews
        context['reviews'] = getattr(self.object, 'received_reviews', []).all()[:5] if hasattr(self.object, 'received_reviews') else []
        # Portfolio images (first 6)
        context['portfolio_images'] = self.object.portfolio_images.all()[:6]
        # Safe profile photo url with fallback if file missing on disk
        profile_photo_url = None
        
        if self.object.profile_photo and getattr(self.object.profile_photo, 'name', None):
            try:
                if default_storage.exists(self.object.profile_photo.name):
                    profile_photo_url = self.object.profile_photo.url
                else:
                    # File doesn't exist, try fallback
                    pass
            except Exception as e:
                profile_photo_url = None
            
        # Fallback to the user's profile picture if available and exists
        if not profile_photo_url and hasattr(self.object, 'user') and getattr(self.object.user, 'profile_picture', None):
            try:
                user_pic = self.object.user.profile_picture
                if user_pic and getattr(user_pic, 'name', None) and default_storage.exists(user_pic.name):
                    profile_photo_url = user_pic.url
            except Exception as e:
                profile_photo_url = None
            
        # Final fallbacks: default media image, then static placeholder
        if not profile_photo_url:
            default_media_path = 'profiles/default.jpg'
            if default_storage.exists(default_media_path):
                profile_photo_url = settings.MEDIA_URL + default_media_path
            else:
                profile_photo_url = '/static/images/worker.webp'
        
        context['profile_photo_url'] = profile_photo_url
        return context


class CraftsmanPortfolioView(LoginRequiredMixin, TemplateView):
    """View for managing craftsman portfolio"""
    template_name = 'accounts/craftsman_portfolio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            craftsman = self.request.user.craftsman_profile
            context['craftsman'] = craftsman
            context['portfolio_images'] = craftsman.portfolio_images.all()
            context['upload_form'] = CraftsmanPortfolioForm()
            context['bulk_upload_form'] = BulkPortfolioUploadForm()
        except CraftsmanProfile.DoesNotExist:
            messages.error(self.request, 'Nu ai un profil de meșter.')
            return redirect('accounts:profile')
        return context


class PortfolioUploadView(LoginRequiredMixin, CreateView):
    """View for uploading single portfolio image"""
    model = CraftsmanPortfolio
    form_class = CraftsmanPortfolioForm
    template_name = 'accounts/portfolio_upload.html'

    def form_valid(self, form):
        try:
            form.instance.craftsman = self.request.user.craftsman_profile
            messages.success(self.request, 'Imaginea a fost adăugată în portfolio.')
            return super().form_valid(form)
        except CraftsmanProfile.DoesNotExist:
            messages.error(self.request, 'Nu ai un profil de meșter.')
            return redirect('accounts:profile')

    def get_success_url(self):
        return reverse_lazy('accounts:portfolio')


class BulkPortfolioUploadView(LoginRequiredMixin, FormView):
    """View for uploading multiple portfolio images"""
    form_class = BulkPortfolioUploadForm
    template_name = 'accounts/bulk_portfolio_upload.html'

    def form_valid(self, form):
        try:
            craftsman = self.request.user.craftsman_profile
            images = form.get_images()

            created_count = 0
            for image in images:
                CraftsmanPortfolio.objects.create(
                    craftsman=craftsman,
                    image=image,
                    title=f"Lucrare {created_count + 1}"
                )
                created_count += 1

            messages.success(
                self.request,
                f'Au fost încărcate {created_count} imagini în portfolio.'
            )
            return redirect('accounts:portfolio')

        except CraftsmanProfile.DoesNotExist:
            messages.error(self.request, 'Nu ai un profil de meșter.')
            return redirect('accounts:profile')

    def get_success_url(self):
        return reverse_lazy('accounts:portfolio')


class PortfolioDeleteView(LoginRequiredMixin, DetailView):
    """View for deleting portfolio image"""
    model = CraftsmanPortfolio

    def post(self, request, *args, **kwargs):
        portfolio_item = self.get_object()

        # Check if user owns this portfolio item
        if portfolio_item.craftsman.user != request.user:
            messages.error(request, 'Nu ai permisiunea să ștergi această imagine.')
            return redirect('accounts:portfolio')

        portfolio_item.delete()
        messages.success(request, 'Imaginea a fost ștearsă din portfolio.')
        return redirect('accounts:portfolio')


class CraftsmanOnboardingView(LoginRequiredMixin, TemplateView):
    """Multi-step onboarding for new craftsmen"""
    template_name = 'accounts/craftsman_onboarding.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        step = self.request.GET.get('step', '1')
        context['current_step'] = step

        if step == '1':
            # Profile setup
            try:
                craftsman = self.request.user.craftsman_profile
                context['profile_form'] = CraftsmanProfileForm(instance=craftsman)
            except CraftsmanProfile.DoesNotExist:
                context['profile_form'] = CraftsmanProfileForm()

        elif step == '2':
            # Skills selection
            context['skills_form'] = CraftsmanSkillsForm()

        elif step == '3':
            # Portfolio upload
            context['portfolio_form'] = BulkPortfolioUploadForm()

        return context

    def post(self, request, *args, **kwargs):
        step = request.GET.get('step', '1')

        if step == '1':
            return self._handle_profile_step(request)
        elif step == '2':
            return self._handle_skills_step(request)
        elif step == '3':
            return self._handle_portfolio_step(request)

        return self.get(request, *args, **kwargs)

    def _handle_profile_step(self, request):
        try:
            craftsman = request.user.craftsman_profile
            form = CraftsmanProfileForm(request.POST, instance=craftsman)
        except CraftsmanProfile.DoesNotExist:
            form = CraftsmanProfileForm(request.POST)

        if form.is_valid():
            if hasattr(request.user, 'craftsman_profile'):
                form.save()
            else:
                craftsman = form.save(commit=False)
                craftsman.user = request.user
                craftsman.save()

            messages.success(request, 'Profilul a fost actualizat.')
            return redirect(f'{request.path}?step=2')

        return render(request, self.template_name, {
            'current_step': '1',
            'profile_form': form
        })

    def _handle_skills_step(self, request):
        form = CraftsmanSkillsForm(request.POST)
        if form.is_valid():
            # Save skills to craftsman profile or separate model
            messages.success(request, 'Competențele au fost salvate.')
            return redirect(f'{request.path}?step=3')

        return render(request, self.template_name, {
            'current_step': '2',
            'skills_form': form
        })

    def _handle_portfolio_step(self, request):
        form = BulkPortfolioUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                craftsman = request.user.craftsman_profile
                images = form.get_images()

                for i, image in enumerate(images):
                    CraftsmanPortfolio.objects.create(
                        craftsman=craftsman,
                        image=image,
                        title=f"Lucrare {i + 1}"
                    )

                messages.success(request, f'Au fost încărcate {len(images)} imagini.')
                return redirect('accounts:profile')

            except CraftsmanProfile.DoesNotExist:
                messages.error(request, 'Profilul de meșter nu a fost găsit.')

        return render(request, self.template_name, {
            'current_step': '3',
            'portfolio_form': form
        })


class EditCraftsmanProfileView(LoginRequiredMixin, UpdateView):
    """View pentru editarea profilului de meșter cu noul sistem"""
    model = CraftsmanProfile
    form_class = CraftsmanProfileForm
    template_name = 'accounts/edit_craftsman_profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        profile, created = CraftsmanProfile.objects.get_or_create(
            user=self.request.user,
            defaults={
                'display_name': self.request.user.get_full_name() or self.request.user.username,
                'bio': 'Meșter profesionist cu experiență în domeniu.',
            }
        )
        return profile

    def form_valid(self, form):
        response = super().form_valid(form)
        # Actualizează procentajul de completare și badge-urile
        self.object.update_profile_completion()
        self.object.update_badges()
        messages.success(self.request, 'Profilul a fost actualizat cu succes!')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.object
        return context


class ManagePortfolioView(LoginRequiredMixin, TemplateView):
    """View pentru gestionarea portofoliului"""
    template_name = 'accounts/manage_portfolio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = get_object_or_404(CraftsmanProfile, user=self.request.user)
        context['portfolio_items'] = CraftsmanPortfolio.objects.filter(
            craftsman=profile
        ).order_by('-created_at')
        context['profile'] = profile
        return context

    def post(self, request, *args, **kwargs):
        """Handle portfolio item creation"""
        profile = get_object_or_404(CraftsmanProfile, user=request.user)
        form = CraftsmanPortfolioForm(request.POST, request.FILES)

        if form.is_valid():
            portfolio_item = form.save(commit=False)
            portfolio_item.craftsman = profile
            portfolio_item.save()

            # Actualizează procentajul de completare
            profile.update_profile_completion()
            profile.update_badges()

            messages.success(request, 'Lucrarea a fost adăugată în portofoliu!')
            return redirect('accounts:manage_portfolio')
        else:
            messages.error(request, 'Eroare la adăugarea lucrării. Verifică datele introduse.')
            return self.get(request, *args, **kwargs)


# AJAX validation views
@require_http_methods(["POST"])
@csrf_exempt
def validate_email_ajax(request):
    """AJAX endpoint pentru validarea email-ului în timp real"""
    email = request.POST.get('email', '').strip()

    if not email:
        return JsonResponse({
            'valid': False,
            'message': 'Adresa de email este obligatorie.'
        })

    # Verifică formatul
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError

    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({
            'valid': False,
            'message': 'Adresa de email nu este validă.'
        })

    # Verifică dacă există deja în baza de date
    if User.objects.filter(email=email).exists():
        return JsonResponse({
            'valid': False,
            'message': 'Un utilizator cu această adresă de email există deja.'
        })

    return JsonResponse({
        'valid': True,
        'message': 'Adresa de email este disponibilă.'
    })


@require_http_methods(["POST"])
@csrf_exempt
def validate_phone_ajax(request):
    """AJAX endpoint pentru validarea numărului de telefon în timp real"""
    phone = request.POST.get('phone', '').strip()

    if not phone:
        return JsonResponse({
            'valid': True,  # Telefonul poate fi opțional
            'message': ''
        })

    # Verifică formatul românesc
    import re
    if not re.match(r'^(\+40|0040|0)[0-9]{9}$', phone.replace(' ', '').replace('-', '')):
        return JsonResponse({
            'valid': False,
            'message': 'Numărul de telefon nu este valid. Folosește formatul românesc (ex: 0721234567).'
        })

    # Verifică dacă există deja în baza de date
    if User.objects.filter(phone_number=phone).exists():
        return JsonResponse({
            'valid': False,
            'message': 'Un utilizator cu acest număr de telefon există deja.'
        })

    return JsonResponse({
        'valid': True,
        'message': 'Numărul de telefon este disponibil.'
    })


class RegistrationCompleteView(TemplateView):
    """View shown after successful registration"""
    template_name = 'accounts/registration_complete.html'


def confirm_email(request, uidb64, token):
    """Confirm user email and activate account"""
    from django.utils.http import urlsafe_base64_decode
    from django.utils.encoding import force_str
    from django.contrib.auth.tokens import default_token_generator

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(
            request,
            'Emailul a fost confirmat cu succes! Contul tău este acum activ. Bun venit pe Bricli!'
        )
        return redirect('core:home')
    else:
        messages.error(
            request,
            'Linkul de confirmare este invalid sau a expirat. Te rugăm să încerci din nou.'
        )
        return redirect('accounts:simple_craftsman_register')
