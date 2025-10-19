import base64
import io

import qrcode
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import LogoutView as BaseLogoutView
from django.contrib.auth.views import PasswordResetCompleteView as BasePasswordResetCompleteView
from django.contrib.auth.views import PasswordResetConfirmView as BasePasswordResetConfirmView
from django.contrib.auth.views import PasswordResetDoneView as BasePasswordResetDoneView
from django.contrib.auth.views import PasswordResetView as BasePasswordResetView
from django.core.files.storage import default_storage
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DetailView, FormView, ListView, TemplateView, UpdateView

from .forms import (
    BulkPortfolioUploadForm,
    CraftsmanPortfolioForm,
    CraftsmanProfileForm,
    CraftsmanRegistrationForm,
    CraftsmanSkillsForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm,
    ProfileUpdateForm,
    SimpleCraftsmanRegistrationForm,
    SimpleUserRegistrationForm,
    TwoFactorDisableForm,
    TwoFactorSetupForm,
    TwoFactorVerifyForm,
    UserRegistrationForm,
)
from .models import County, CraftsmanPortfolio, CraftsmanProfile, User


class RegisterView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Contul a fost creat cu succes! Te poți conecta acum.")
        return response


class SimpleRegisterView(CreateView):
    """Simplified registration view similar to MyHammer"""

    model = User
    form_class = SimpleUserRegistrationForm
    template_name = "accounts/simple_register.html"
    success_url = reverse_lazy("core:home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.user_type == "craftsman":
                return redirect("services:craftsman_services")
            else:
                return redirect("services:my_orders")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Contul a fost creat cu succes! Bun venit pe Bricli!")
        return response


class SimpleCraftsmanRegisterView(CreateView):
    """Simplified craftsman registration view"""

    model = User
    form_class = SimpleCraftsmanRegistrationForm
    template_name = "accounts/simple_craftsman_register.html"
    success_url = reverse_lazy("accounts:profile")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.user_type == "craftsman":
                return redirect("services:craftsman_services")
            else:
                return redirect("services:my_orders")
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        """Keep user on page with error messages when form is invalid"""
        return self.render_to_response(self.get_context_data(form=form))

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
            f"Contul a fost creat cu succes! Am trimis un email de confirmare la {user.email}. "
            "Te rugăm să verifici emailul și să apeși pe linkul de confirmare pentru a-ți activa contul.",
        )
        return redirect("accounts:registration_complete")

    def send_confirmation_email(self, user):
        """Send email confirmation to new user"""
        from django.contrib.auth.tokens import default_token_generator
        from django.core.mail import send_mail
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        # Generate confirmation token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Build confirmation URL
        confirmation_url = self.request.build_absolute_uri(f"/accounts/confirm-email/{uid}/{token}/")

        # Email content
        subject = "Confirmă-ți contul Bricli"
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
                "Contul a fost creat dar nu am putut trimite emailul de confirmare. "
                "Contul tău este activ și te poți conecta acum.",
            )


class CraftsmanRegisterView(CreateView):
    model = User
    form_class = CraftsmanRegistrationForm
    template_name = "accounts/craftsman_register.html"
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.user_type = "craftsman"
        user.save()

        # Create craftsman profile
        CraftsmanProfile.objects.create(user=user)

        messages.success(self.request, "Contul de meșter a fost creat cu succes! Te poți conecta acum.")
        return redirect(self.success_url)


class LoginView(BaseLoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        """Handle successful login with 2FA check"""
        user = form.get_user()

        # Check if user has 2FA enabled
        if user.two_factor_enabled:
            # Store user ID in session for 2FA verification
            self.request.session["2fa_user_id"] = user.id

            # Store redirect URL if provided
            next_url = self.request.GET.get("next")
            if next_url:
                self.request.session["login_redirect_url"] = next_url

            # Redirect to 2FA verification instead of logging in
            return redirect("accounts:two_factor_verify")

        # Normal login for users without 2FA
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("core:home")


class LogoutView(BaseLogoutView):
    template_name = "registration/logged_out.html"
    next_page = reverse_lazy("core:home")
    http_method_names = ["get", "post", "options"]

    def get(self, request, *args, **kwargs):
        """Handle GET requests for logout"""
        from django.contrib.auth import logout

        logout(request)
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        """Handle POST requests for logout"""
        return super().post(request, *args, **kwargs)


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile view"""

    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        from django.db.models import Avg
        from django.urls import reverse

        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["user"] = user

        # Get craftsman profile if exists
        craftsman = getattr(user, "craftsman_profile", None)

        # Calculate services count
        try:
            from services.models import CraftsmanService
            services_count = CraftsmanService.objects.filter(craftsman=craftsman).count() if craftsman else 0
        except Exception:
            services_count = 0

        # Calculate reviews stats
        reviews_count = 0
        rating_avg = 0.0
        try:
            from services.models import Review
            if craftsman:
                reviews_qs = Review.objects.filter(craftsman=craftsman)
                reviews_count = reviews_qs.count()
                avg_rating = reviews_qs.aggregate(avg=Avg("rating"))["avg"]
                rating_avg = avg_rating if avg_rating is not None else 0.0
        except Exception:
            pass

        # Format rating with comma (Romanian style)
        rating_avg_str = f"{rating_avg:.1f}".replace(".", ",")

        # Calculate orders count for clients
        orders_active_count = 0
        orders_completed_count = 0
        if user.user_type == "client":
            try:
                from services.models import Order
                from services.querydefs import q_active, q_completed

                base_qs = Order.objects.filter(client=user)
                orders_active_count = base_qs.filter(q_active()).count()
                orders_completed_count = base_qs.filter(q_completed()).count()
            except Exception:
                pass

        # Get public profile URL with slug
        public_url = ""
        if craftsman:
            ensure_craftsman_slug(craftsman)  # Ensure slug exists
            if craftsman.slug:
                public_url = reverse("accounts:craftsman_detail", kwargs={"slug": craftsman.slug})

        # Get avatar URL
        avatar_url = ""
        if craftsman and getattr(craftsman, "profile_photo", None):
            try:
                avatar_url = craftsman.profile_photo.url
            except Exception:
                pass
        if not avatar_url and getattr(user, "profile_picture", None):
            try:
                avatar_url = user.profile_picture.url
            except Exception:
                pass

        # Calculate profile completion for craftsmen
        profile_completion = 0
        profile_is_complete = False
        completion_missing = []
        if craftsman:
            try:
                from accounts.services.profile_completion import calculate_profile_completion, get_completion_summary

                result = calculate_profile_completion(craftsman)
                profile_completion = result["score"]
                profile_is_complete = result["is_complete"]
                completion_missing = get_completion_summary(craftsman)
            except Exception:
                pass

        context.update({
            "services_count": services_count,
            "reviews_count": reviews_count,
            "rating_avg": rating_avg_str,
            "orders_active_count": orders_active_count,
            "orders_completed_count": orders_completed_count,
            "public_url": public_url,
            "avatar_url": avatar_url,
            "profile_completion": profile_completion,
            "profile_is_complete": profile_is_complete,
            "completion_missing": completion_missing,
        })

        return context


class EditProfileView(LoginRequiredMixin, UpdateView):
    """Edit user profile"""

    model = User
    form_class = ProfileUpdateForm
    template_name = "accounts/edit_profile.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        # Handle profile picture removal
        if self.request.POST.get("remove_picture") == "true":
            if self.request.user.profile_picture:
                self.request.user.profile_picture.delete()
                self.request.user.profile_picture = None
                self.request.user.save()

        # Save craftsman profile fields if user is craftsman
        if self.request.user.user_type == "craftsman":
            try:
                craftsman_profile = self.request.user.craftsman_profile
            except CraftsmanProfile.DoesNotExist:
                craftsman_profile = CraftsmanProfile.objects.create(user=self.request.user)

            # Update craftsman profile fields
            craftsman_fields = [
                "display_name",
                "county",
                "city",
                "coverage_radius_km",
                "bio",
                "years_experience",
                "hourly_rate",
                "min_job_value",
                "company_cui",
                "business_address",
                "website_url",
                "facebook_url",
                "instagram_url",
            ]

            for field in craftsman_fields:
                if field in form.cleaned_data and form.cleaned_data[field] is not None:
                    setattr(craftsman_profile, field, form.cleaned_data[field])

            craftsman_profile.save()
            craftsman_profile.update_profile_completion()
            craftsman_profile.update_badges()

        messages.success(self.request, "Profilul a fost actualizat cu succes!")
        return super().form_valid(form)


class CraftsmenListView(ListView):
    model = CraftsmanProfile
    template_name = "accounts/craftsmen_list.html"
    context_object_name = "results"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        """Redirect craftsmen to their dashboard"""
        if request.user.is_authenticated and getattr(request.user, "user_type", None) == "craftsman":
            messages.info(request, "Meșterii nu pot accesa lista de meșteri.")
            return redirect("services:my_quotes")
        return super().dispatch(request, *args, **kwargs)

    def get_paginate_by(self, queryset):
        """Allow dynamic page size"""
        per_page = self.request.GET.get("per_page")
        if per_page and per_page.isdigit():
            per_page = int(per_page)
            # Limit to 10-60 range
            return max(10, min(60, per_page))
        return self.paginate_by

    def get_queryset(self):
        from services.models import ServiceCategory
        from services.querydefs import q_active_craftsmen

        # Get filter parameters
        q = (self.request.GET.get("q") or "").strip()
        county = self.request.GET.get("county") or ""
        category = self.request.GET.get("category") or ""
        verified = self.request.GET.get("verified") == "1"
        available = self.request.GET.get("available") == "1"
        rating = self.request.GET.get("rating")
        sort = self.request.GET.get("sort") or "popular"

        # Base queryset - use permissive filter (only requires active user account)
        qs = CraftsmanProfile.objects.filter(q_active_craftsmen())
        qs = qs.select_related("user", "county").prefetch_related("services__service__category")

        # Text search
        if q:
            qs = qs.filter(
                models.Q(user__first_name__icontains=q)
                | models.Q(user__last_name__icontains=q)
                | models.Q(bio__icontains=q)
                | models.Q(company_name__icontains=q)
            )

        # County filter (by slug)
        if county:
            county_obj = County.objects.filter(slug=county).first()
            if county_obj:
                qs = qs.filter(county=county_obj)

        # Category filter (by slug)
        if category:
            category_obj = ServiceCategory.objects.filter(slug=category).first()
            if category_obj:
                qs = qs.filter(services__service__category=category_obj)

        # Verified filter
        if verified:
            qs = qs.filter(user__is_verified=True)

        # Available filter (if field exists)
        if available and hasattr(CraftsmanProfile, "is_available"):
            qs = qs.filter(is_available=True)

        # Hourly rate filter (if fields exist)
        min_rate = self.request.GET.get("min_rate")
        max_rate = self.request.GET.get("max_rate")
        if hasattr(CraftsmanProfile, "hourly_rate"):
            if min_rate and min_rate.isdigit():
                qs = qs.filter(hourly_rate__gte=int(min_rate))
            if max_rate and max_rate.isdigit():
                qs = qs.filter(hourly_rate__lte=int(max_rate))

        # Rating filter
        if rating:
            try:
                rating_min = float(rating)
                qs = qs.filter(average_rating__gte=rating_min)
            except ValueError:
                pass

        # Sorting
        if sort == "reviews":
            qs = qs.order_by("-total_reviews", "-average_rating", "-id")
        elif sort == "rating":
            qs = qs.order_by("-average_rating", "-total_reviews", "-id")
        elif sort == "newest" and hasattr(CraftsmanProfile, "created_at"):
            qs = qs.order_by("-created_at")
        else:  # popular (default)
            qs = qs.order_by("-total_reviews", "-average_rating")

        return qs.distinct()

    def get_context_data(self, **kwargs):
        from services.models import ServiceCategory

        context = super().get_context_data(**kwargs)
        context["counties"] = County.objects.only("name", "slug").order_by("name")
        context["categories"] = ServiceCategory.objects.only("name", "slug").order_by("name")
        context["sort_options"] = {
            "popular": "Cei mai populari",
            "newest": "Cei mai noi",
            "rating": "Rating",
            "reviews": "Nr. recenzii",
        }
        context["per_page_choices"] = [20, 40, 60]
        context["default_per_page"] = 20
        context["view"] = self.request.GET.get("view") or "grid"
        return context


class CraftsmanDetailView(DetailView):
    model = CraftsmanProfile
    template_name = "accounts/craftsman_detail.html"
    context_object_name = "craftsman"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Reviews with images prefetched for performance
        context["reviews"] = (
            self.object.received_reviews
            .select_related("client")
            .prefetch_related("images")
            .order_by("-created_at")[:5]
        )
        # Portfolio images (first 6)
        context["portfolio_images"] = self.object.portfolio_images.all()[:6]
        # Safe profile photo url with fallback if file missing on disk
        profile_photo_url = None

        if self.object.profile_photo and getattr(self.object.profile_photo, "name", None):
            try:
                if default_storage.exists(self.object.profile_photo.name):
                    profile_photo_url = self.object.profile_photo.url
                else:
                    # File doesn't exist, try fallback
                    pass
            except Exception:
                profile_photo_url = None

        # Fallback to the user's profile picture if available and exists
        if (
            not profile_photo_url
            and hasattr(self.object, "user")
            and getattr(self.object.user, "profile_picture", None)
        ):
            try:
                user_pic = self.object.user.profile_picture
                if user_pic and getattr(user_pic, "name", None) and default_storage.exists(user_pic.name):
                    profile_photo_url = user_pic.url
            except Exception:
                profile_photo_url = None

        # Final fallback: static placeholder avatar.svg to avoid corrupted media default.jpg
        if not profile_photo_url:
            profile_photo_url = "/static/images/avatar.svg"

        context["profile_photo_url"] = profile_photo_url
        return context


class CraftsmanPortfolioView(LoginRequiredMixin, TemplateView):
    """View for managing craftsman portfolio"""

    template_name = "accounts/craftsman_portfolio.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            craftsman = self.request.user.craftsman_profile
            context["craftsman"] = craftsman
            context["portfolio_images"] = craftsman.portfolio_images.all()
            context["upload_form"] = CraftsmanPortfolioForm()
            context["bulk_upload_form"] = BulkPortfolioUploadForm()
        except CraftsmanProfile.DoesNotExist:
            messages.error(self.request, "Nu ai un profil de meșter.")
            return redirect("accounts:profile")
        return context


class PortfolioUploadView(LoginRequiredMixin, CreateView):
    """View for uploading single portfolio image"""

    model = CraftsmanPortfolio
    form_class = CraftsmanPortfolioForm
    template_name = "accounts/portfolio_upload.html"

    def form_valid(self, form):
        try:
            form.instance.craftsman = self.request.user.craftsman_profile
            messages.success(self.request, "Imaginea a fost adăugată în portfolio.")
            return super().form_valid(form)
        except CraftsmanProfile.DoesNotExist:
            messages.error(self.request, "Nu ai un profil de meșter.")
            return redirect("accounts:profile")

    def get_success_url(self):
        return reverse_lazy("accounts:portfolio")


class BulkPortfolioUploadView(LoginRequiredMixin, FormView):
    """View for uploading multiple portfolio images"""

    form_class = BulkPortfolioUploadForm
    template_name = "accounts/bulk_portfolio_upload.html"

    def form_valid(self, form):
        try:
            craftsman = self.request.user.craftsman_profile
            images = form.get_images()

            created_count = 0
            for image in images:
                CraftsmanPortfolio.objects.create(
                    craftsman=craftsman, image=image, title=f"Lucrare {created_count + 1}"
                )
                created_count += 1

            messages.success(self.request, f"Au fost încărcate {created_count} imagini în portfolio.")
            return redirect("accounts:portfolio")

        except CraftsmanProfile.DoesNotExist:
            messages.error(self.request, "Nu ai un profil de meșter.")
            return redirect("accounts:profile")

    def get_success_url(self):
        return reverse_lazy("accounts:portfolio")


class PortfolioDeleteView(LoginRequiredMixin, DetailView):
    """View for deleting portfolio image"""

    model = CraftsmanPortfolio

    def post(self, request, *args, **kwargs):
        portfolio_item = self.get_object()

        # Check if user owns this portfolio item
        if portfolio_item.craftsman.user != request.user:
            messages.error(request, "Nu ai permisiunea să ștergi această imagine.")
            return redirect("accounts:portfolio")

        portfolio_item.delete()
        messages.success(request, "Imaginea a fost ștearsă din portfolio.")
        return redirect("accounts:portfolio")


class CraftsmanOnboardingView(LoginRequiredMixin, TemplateView):
    """Multi-step onboarding for new craftsmen"""

    template_name = "accounts/craftsman_onboarding.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        step = self.request.GET.get("step", "1")
        context["current_step"] = step

        if step == "1":
            # Profile setup
            try:
                craftsman = self.request.user.craftsman_profile
                context["profile_form"] = CraftsmanProfileForm(instance=craftsman)
            except CraftsmanProfile.DoesNotExist:
                context["profile_form"] = CraftsmanProfileForm()

        elif step == "2":
            # Skills selection
            context["skills_form"] = CraftsmanSkillsForm()

        elif step == "3":
            # Portfolio upload
            context["portfolio_form"] = BulkPortfolioUploadForm()

        return context

    def post(self, request, *args, **kwargs):
        step = request.GET.get("step", "1")

        if step == "1":
            return self._handle_profile_step(request)
        elif step == "2":
            return self._handle_skills_step(request)
        elif step == "3":
            return self._handle_portfolio_step(request)

        return self.get(request, *args, **kwargs)

    def _handle_profile_step(self, request):
        try:
            craftsman = request.user.craftsman_profile
            form = CraftsmanProfileForm(request.POST, instance=craftsman)
        except CraftsmanProfile.DoesNotExist:
            form = CraftsmanProfileForm(request.POST)

        if form.is_valid():
            if hasattr(request.user, "craftsman_profile"):
                form.save()
            else:
                craftsman = form.save(commit=False)
                craftsman.user = request.user
                craftsman.save()

            messages.success(request, "Profilul a fost actualizat.")
            return redirect(f"{request.path}?step=2")

        return render(request, self.template_name, {"current_step": "1", "profile_form": form})

    def _handle_skills_step(self, request):
        form = CraftsmanSkillsForm(request.POST)
        if form.is_valid():
            # Save skills to craftsman profile or separate model
            messages.success(request, "Competențele au fost salvate.")
            return redirect(f"{request.path}?step=3")

        return render(request, self.template_name, {"current_step": "2", "skills_form": form})

    def _handle_portfolio_step(self, request):
        form = BulkPortfolioUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                craftsman = request.user.craftsman_profile
                images = form.get_images()

                for i, image in enumerate(images):
                    CraftsmanPortfolio.objects.create(craftsman=craftsman, image=image, title=f"Lucrare {i + 1}")

                messages.success(request, f"Au fost încărcate {len(images)} imagini.")
                return redirect("accounts:profile")

            except CraftsmanProfile.DoesNotExist:
                messages.error(request, "Profilul de meșter nu a fost găsit.")

        return render(request, self.template_name, {"current_step": "3", "portfolio_form": form})


class ManagePortfolioView(LoginRequiredMixin, TemplateView):
    """View pentru gestionarea portofoliului"""

    template_name = "accounts/manage_portfolio.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = get_object_or_404(CraftsmanProfile, user=self.request.user)
        context["portfolio_items"] = CraftsmanPortfolio.objects.filter(craftsman=profile).order_by("-created_at")
        context["profile"] = profile
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

            messages.success(request, "Lucrarea a fost adăugată în portofoliu!")
            return redirect("accounts:manage_portfolio")
        else:
            messages.error(request, "Eroare la adăugarea lucrării. Verifică datele introduse.")
            return self.get(request, *args, **kwargs)


# AJAX validation views
@require_http_methods(["POST"])
@csrf_exempt
def validate_email_ajax(request):
    """AJAX endpoint pentru validarea email-ului în timp real"""
    email = request.POST.get("email", "").strip()

    if not email:
        return JsonResponse({"valid": False, "message": "Adresa de email este obligatorie."})

    # Verifică formatul
    from django.core.exceptions import ValidationError
    from django.core.validators import validate_email

    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({"valid": False, "message": "Adresa de email nu este validă."})

    # Verifică dacă există deja în baza de date
    if User.objects.filter(email=email).exists():
        return JsonResponse({"valid": False, "message": "Un utilizator cu această adresă de email există deja."})

    return JsonResponse({"valid": True, "message": "Adresa de email este disponibilă."})


@require_http_methods(["POST"])
@csrf_exempt
def validate_phone_ajax(request):
    """AJAX endpoint pentru validarea numărului de telefon în timp real"""
    phone = request.POST.get("phone", "").strip()

    if not phone:
        return JsonResponse({"valid": True, "message": ""})  # Telefonul poate fi opțional

    # Verifică formatul românesc
    import re

    if not re.match(r"^(\+40|0040|0)[0-9]{9}$", phone.replace(" ", "").replace("-", "")):
        return JsonResponse(
            {
                "valid": False,
                "message": "Numărul de telefon nu este valid. Folosește formatul românesc (ex: 0721234567).",
            }
        )

    # Verifică dacă există deja în baza de date
    if User.objects.filter(phone_number=phone).exists():
        return JsonResponse({"valid": False, "message": "Un utilizator cu acest număr de telefon există deja."})

    return JsonResponse({"valid": True, "message": "Numărul de telefon este disponibil."})


class RegistrationCompleteView(TemplateView):
    """View shown after successful registration"""

    template_name = "accounts/registration_complete.html"


def confirm_email(request, uidb64, token):
    """Confirm user email and activate account"""
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.encoding import force_str
    from django.utils.http import urlsafe_base64_decode

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
            request, "Emailul a fost confirmat cu succes! Contul tău este acum activ. Bun venit pe Bricli!"
        )
        return redirect("core:home")
    else:
        messages.error(request, "Linkul de confirmare este invalid sau a expirat. Te rugăm să încerci din nou.")
        return redirect("auth:craftsman_register")


# Password Reset Views
class PasswordResetView(BasePasswordResetView):
    """Custom password reset view with Romanian language support"""

    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")
    form_class = CustomPasswordResetForm

    def form_valid(self, form):
        messages.success(self.request, "Am trimis instrucțiunile de resetare a parolei la adresa ta de email.")
        return super().form_valid(form)


class PasswordResetDoneView(BasePasswordResetDoneView):
    """Password reset email sent confirmation"""

    template_name = "accounts/password_reset_done.html"


class PasswordResetConfirmView(BasePasswordResetConfirmView):
    """Password reset confirmation view"""

    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")
    form_class = CustomSetPasswordForm

    def form_valid(self, form):
        messages.success(self.request, "Parola ta a fost schimbată cu succes! Acum te poți autentifica cu noua parolă.")
        return super().form_valid(form)


class PasswordResetCompleteView(BasePasswordResetCompleteView):
    """Password reset complete view"""

    template_name = "accounts/password_reset_complete.html"


# Two-Factor Authentication Views


class TwoFactorSetupView(LoginRequiredMixin, FormView):
    """View for setting up two-factor authentication"""

    template_name = "accounts/two_factor_setup.html"
    form_class = TwoFactorSetupForm
    success_url = reverse_lazy("accounts:profile")

    def dispatch(self, request, *args, **kwargs):
        # Redirect if 2FA is already enabled
        if request.user.two_factor_enabled:
            messages.info(request, "Autentificarea cu doi factori este deja activată.")
            return redirect("accounts:profile")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Generate QR code for TOTP setup
        if not self.request.user.two_factor_secret:
            self.request.user.generate_2fa_secret()
            self.request.user.save()

        qr_code_url = self.request.user.get_2fa_qr_code_url()

        # Generate QR code image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_code_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

        context.update(
            {
                "qr_code_base64": qr_code_base64,
                "secret_key": self.request.user.two_factor_secret,
                "qr_code_url": qr_code_url,
            }
        )

        return context

    def form_valid(self, form):
        user = self.request.user
        token = form.cleaned_data["token"]

        if user.verify_2fa_token(token):
            user.two_factor_enabled = True
            user.generate_backup_codes()
            user.save()

            messages.success(
                self.request,
                "Autentificarea cu doi factori a fost activată cu succes! "
                "Salvează codurile de rezervă într-un loc sigur.",
            )
            return super().form_valid(form)
        else:
            form.add_error("token", "Codul introdus nu este valid.")
            return self.form_invalid(form)


class TwoFactorVerifyView(FormView):
    """View for verifying 2FA token during login"""

    template_name = "accounts/two_factor_verify.html"
    form_class = TwoFactorVerifyForm

    def dispatch(self, request, *args, **kwargs):
        # Check if user is in 2FA verification state
        if not request.session.get("2fa_user_id"):
            return redirect("accounts:login")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.request.session.get("2fa_user_id")
        if user_id:
            user = get_object_or_404(User, id=user_id)
            context["user"] = user
        return context

    def form_valid(self, form):
        user_id = self.request.session.get("2fa_user_id")
        user = get_object_or_404(User, id=user_id)
        token = form.cleaned_data["token"]

        # Verify TOTP token or backup code
        if user.verify_2fa_token(token) or user.verify_backup_code(token):
            # Complete login
            login(self.request, user)

            # Clear 2FA session data
            del self.request.session["2fa_user_id"]

            messages.success(self.request, f"Bun venit, {user.get_full_name() or user.username}!")

            # Redirect to next URL or profile
            next_url = self.request.session.get("login_redirect_url", reverse_lazy("accounts:profile"))
            if "login_redirect_url" in self.request.session:
                del self.request.session["login_redirect_url"]

            return redirect(next_url)
        else:
            form.add_error("token", "Codul introdus nu este valid.")
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("accounts:profile")


class TwoFactorDisableView(LoginRequiredMixin, FormView):
    """View for disabling two-factor authentication"""

    template_name = "accounts/two_factor_disable.html"
    form_class = TwoFactorDisableForm
    success_url = reverse_lazy("accounts:profile")

    def dispatch(self, request, *args, **kwargs):
        # Redirect if 2FA is not enabled
        if not request.user.two_factor_enabled:
            messages.info(request, "Autentificarea cu doi factori nu este activată.")
            return redirect("accounts:profile")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = self.request.user
        password = form.cleaned_data["password"]

        # Verify password
        if user.check_password(password):
            user.disable_2fa()
            messages.success(self.request, "Autentificarea cu doi factori a fost dezactivată cu succes.")
            return super().form_valid(form)
        else:
            form.add_error("password", "Parola introdusă nu este corectă.")
            return self.form_invalid(form)


class TwoFactorBackupCodesView(LoginRequiredMixin, TemplateView):
    """View for displaying backup codes"""

    template_name = "accounts/two_factor_backup_codes.html"

    def dispatch(self, request, *args, **kwargs):
        # Redirect if 2FA is not enabled
        if not request.user.two_factor_enabled:
            messages.error(request, "Autentificarea cu doi factori nu este activată.")
            return redirect("accounts:profile")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["backup_codes"] = self.request.user.backup_codes or []
        return context

    def post(self, request, *args, **kwargs):
        # Regenerate backup codes
        request.user.generate_backup_codes()
        request.user.save()

        messages.success(
            request, "Codurile de rezervă au fost regenerate cu succes. " "Salvează noile coduri într-un loc sigur."
        )

        return redirect("accounts:two_factor_backup_codes")


class RegistrationChoiceView(TemplateView):
    """
    Landing page for registration - choose between Client or Craftsman (Meserias)
    """

    template_name = "accounts/registration_choice.html"


def ensure_craftsman_slug(craftsman):
    """
    Helper: if craftsman.slug is missing/empty, trigger save() to auto-generate.
    Called by CraftsmanIdRedirectView.get() to handle old profiles without slugs.
    """
    if not craftsman.slug:
        craftsman.save()  # Auto-generates slug via model's save() method
        craftsman.refresh_from_db()  # Ensure we have the latest slug


class CraftsmanIdRedirectView(DetailView):
    """
    Redirect view for old craftsman URLs with numeric IDs.
    Redirects /conturi/meserias/1/ to /conturi/meserias/slug/ with 301.
    """
    model = CraftsmanProfile
    pk_url_kwarg = "pk"

    def get(self, request, *args, **kwargs):
        from django.shortcuts import redirect

        craftsman = self.get_object()
        ensure_craftsman_slug(craftsman)

        # Verify slug exists after generation
        if not craftsman.slug:
            messages.error(
                request,
                f"Nu s-a putut genera URL-ul pentru profilul meșterului. Te rugăm să contactezi suportul."
            )
            return redirect("accounts:craftsmen_list")

        return redirect("accounts:craftsman_detail", slug=craftsman.slug, permanent=True)


@require_http_methods(["GET"])
def craftsman_reviews_ajax(request, pk):
    """AJAX endpoint for loading more reviews"""
    try:
        from services.models import Review

        craftsman = get_object_or_404(CraftsmanProfile, pk=pk)
        offset = int(request.GET.get("offset", 0))
        limit = int(request.GET.get("limit", 10))

        # Get reviews with images
        reviews_qs = Review.objects.filter(craftsman=craftsman).select_related("client").prefetch_related("images").order_by("-created_at")
        total_reviews = reviews_qs.count()
        reviews = reviews_qs[offset : offset + limit]

        # Format reviews data
        reviews_data = []
        for review in reviews:
            # Get review images
            images_data = []
            for img in review.images.all():
                images_data.append({
                    "url": img.image.url,
                    "description": img.description or ""
                })

            reviews_data.append(
                {
                    "id": review.pk,
                    "client_name": (review.client.get_full_name() or review.client.username) if review.client else "Client",
                    "rating": review.rating,
                    "comment": review.comment or "",
                    "created_at": review.created_at.strftime("%d %b %Y"),
                    "images": images_data,
                    "images_count": len(images_data)
                }
            )

        return JsonResponse({"reviews": reviews_data, "total_reviews": total_reviews, "offset": offset, "limit": limit})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
