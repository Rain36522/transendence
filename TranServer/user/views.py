from sys import stderr
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated

from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import (
    authenticate,
    login,
    logout,
    password_validation,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import User
from chat.models import Chat
from .serializers import (
    UserSerializer,
    UserSerializer_Username,
    PersonalUserSerializer,
    OtherUserSerializer,
    ColorsUserSerializer,
    ColorUpdateSerializer,
)

import mimetypes
import os
from datetime import timedelta


@api_view(["POST"])
@renderer_classes([JSONRenderer])
def api_signup(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        chat = Chat.objects.create()
        chat.participants.add(user)
        chat.is_personal = True
        chat.save()
        login(request, user)
        return Response({"message": "User created successfully"}, status=201)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@renderer_classes([JSONRenderer])
@login_required
def api_pending_invite(request):
    try:
        invites = request.user.sent_invites.all()
        return Response(
            UserSerializer_Username(invites, many=True).data,
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FriendListView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request, username=None):
        try:
            friends = request.user.friends.all()
            return Response(
                UserSerializer_Username(friends, many=True).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, username=None):
        try:
            friend = request.user.invites.filter(username=username)
            if friend:
                request.user.friends.add(friend.first())
                request.user.invites.remove(friend.first())
                return JsonResponse(
                    {"message": "accepted friend invite"}, status=status.HTTP_200_OK
                )
            return JsonResponse(
                {"error": "no invite found"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, username=None):
        if not username:
            return Response(
                "Please provide a username", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(username=username)
            if user.friends.filter(username=request.user.username):
                user.friends.remove(request.user)
                return Response("Removed user", status=status.HTTP_200_OK)
            return Response("User is not friend", status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response(
                "User with provided username does not exist",
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@renderer_classes([JSONRenderer])
@login_required
def undo_invite_api(request, username):
    try:
        user = User.objects.get(username=username)
        user.invites.remove(request.user)
        return Response("Rescinded invited", status=status.HTTP_200_OK)
    except Exception as e:
        return Response("Invalid request", status=status.HTTP_400_BAD_REQUEST)


@renderer_classes([JSONRenderer])
@login_required
@api_view(["GET"])
def is_blocked_api(request, username):
    try:
        user = User.objects.get(username=username)
        if user.blocked.filter(username=request.user.username):
            return Response(True, status=status.HTTP_200_OK)
        return Response(False, status=status.HTTP_200_OK)
    except Exception as e:
        return Response("Invalid request", status=status.HTTP_400_BAD_REQUEST)


class InviteListView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]
    """
    Get your invites
    """

    def get(self, request, username=None):
        try:
            invites = request.user.invites.all()
            return Response(
                UserSerializer_Username(invites, many=True).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    """
    Send invites to someone
    """

    def post(self, request, username=None):
        if not username:
            return Response(
                "Please provide a username", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(username=username)
            if request.user.blocked.filter(username=username):
                return Response(
                    "You can't invite a user that you've blocked",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if user.blocked.filter(username=request.user.username):
                return Response(
                    "You can't invite a user that has blocked you",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if user.invites.filter(username=username):
                return Response(
                    "Invite already exists", status=status.HTTP_400_BAD_REQUEST
                )
            if request.user == user:
                return Response(
                    "You cannot invite yourself", status=status.HTTP_400_BAD_REQUEST
                )
            if request.user.invites.filter(username=username):
                request.user.invites.remove(user)
                request.user.friends.add(user)
                return Response("Added as friend", status=status.HTTP_200_OK)

            user.invites.add(request.user)
            return Response("Added invite", status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    """
    Reject an invite
    """

    def delete(self, request, username=None):
        if not username:
            return Response(
                "Please provide a username", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(username=username)
            if request.user.invites.filter(username=user.username):
                request.user.invites.remove(user)
                return Response("Removed user", status=status.HTTP_200_OK)
            return Response("Invite does not exist", status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response(
                "User with provided username does not exist",
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BlockedListView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request, username=None):
        try:
            blocked = request.user.blocked.all()
            return Response(
                UserSerializer_Username(blocked, many=True).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, username=None):
        if not username:
            return Response(
                "Please provide a username", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(username=username)
            if request.user.blocked.filter(username=username):
                return Response("Already blocked", status=status.HTTP_400_BAD_REQUEST)
            if request.user == user:
                return Response(
                    "You cannot block yourself", status=status.HTTP_400_BAD_REQUEST
                )
            request.user.blocked.add(user)
            if request.user.invites.filter(username=username):
                request.user.invites.remove(user)
            if user.invites.filter(username=request.user.username):
                user.invites.remove(request.user)
            if request.user.friends.filter(username=username):
                request.user.friends.remove(user)
            return Response("Added blocked", status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, username=None):
        if not username:
            return Response(
                "Please provide a username", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(username=username)
            if request.user.blocked.filter(username=user.username):
                request.user.blocked.remove(user)
                return Response("Unblocked user", status=status.HTTP_200_OK)
            return Response("User is not blocked", status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response(
                "User with provided username does not exist",
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ColorView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        try:
            return Response(
                ColorsUserSerializer(request.user).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        try:
            user = request.user
            serializer = ColorUpdateSerializer(
                instance=user, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": "Colors updated successfully"},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@renderer_classes([JSONRenderer])
def user_exist_api(request, username=None):
    try:
        if username:
            User.objects.get(username=username)
            return Response(True, status=status.HTTP_200_OK)
        else:
            return Response(
                "Please provide a username", status=status.HTTP_400_BAD_REQUEST
            )
    except:
        return Response(False, status=status.HTTP_200_OK)


@api_view(["POST"])
@renderer_classes([JSONRenderer])
def user_login_api(request):
    try:
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("user_dashboard")
        else:
            return JsonResponse({"error": "Invalid username or password"}, status=400)
    except:
        return JsonResponse({"error": "Invalid request"}, status=400)


@api_view(["GET"])
@renderer_classes([JSONRenderer])
@login_required
def user_profile_pic_api(request, username=None):
    try:
        if username:
            user = get_object_or_404(User, username=username)
        else:
            user = request.user
        if user.profile_picture:
            path = user.profile_picture.path
            content_type, _ = mimetypes.guess_type(path)
            with open(path, "rb") as f:
                return HttpResponse(f.read(), content_type=content_type)
        default_image_path = os.path.join(settings.MEDIA_ROOT, "default_profile.png")
        with open(default_image_path, "rb") as f:
            return HttpResponse(f.read(), content_type="image/png")
    except Exception as e:
        return JsonResponse({"error": e}, status=500)


ALLOWED_FILE_TYPES = ["image/jpeg", "image/png"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@api_view(["POST"])
@renderer_classes([JSONRenderer])
@login_required
def upload_profile_pic_api(request):
    try:
        if "profile_picture" in request.FILES:
            profile_picture = request.FILES["profile_picture"]

            # File type validation
            if profile_picture.content_type not in ALLOWED_FILE_TYPES:
                return JsonResponse({"error¬": "Invalid file type"}, status=400)

            # File size limit
            if profile_picture.size > MAX_FILE_SIZE:
                return JsonResponse(
                    {"error": "File size exceeds the limit"}, status=400
                )

            user = request.user

            # Check if the user already has a profile picture
            # if user.profile_picture:
            #     try:
            #         # Delete the old profile picture file from the storage
            #         if os.path.isfile(user.profile_picture.path):
            #             os.remove(user.profile_picture.path)
            #     except:
            #         pass

            # Save the new profile picture
            user.profile_picture = profile_picture
            user.save()
            return JsonResponse(
                {"message": "Upload successful"}, status=status.HTTP_201_CREATED
            )
        return JsonResponse(
            {"message": "No file found"}, status=status.HTTP_400_BAD_REQUEST
        )
    except ValidationError:
        return JsonResponse(
            {"error": "Invalid file"}, status=status.HTTP_400_BAD_REQUEST
        )
    except:
        return JsonResponse(
            {"error": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST
        )


@login_required
def account_information(request):
    return render(request, "html/accountInformation.html")


def logout_view(request):
    logout(request)
    return redirect("user_login")


@login_required
def test_upload(request):
    return render(request, "html/test_upload.html")


def profile_user(request, username=None):
    return render(request, "html/profile_user.html")


@login_required
def user_dashboard(request, username=None):
    user = request.user
    if username:
        user = User.objects.get(username=username)
    ratio_w = 0
    ratio_l = 0
    losses = user.total_games - user.wins
    if user.total_games != 0:
        ratio_w = user.wins / user.total_games
        ratio_l = losses / user.total_games
    return render(
        request,
        "html/dashboard.html",
        {
            "user": user,
            "losses": losses,
            "ratio_w": ratio_w,
            "ratio_l": ratio_l,
        },
    )


def user_login(request):
    return render(request, "html/login.html")


def user_register(request):
    return render(request, "html/register.html")


@login_required
def social_management(request):
    return render(request, "html/socialManagement.html")


@login_required
def profile(request):
    return render(request, "profile.html")


@login_required
def dashboard(request):
    return render(request, "dashboard.html", {"user": request.user})


@api_view(["GET"])
@renderer_classes([JSONRenderer])
@login_required
def search_usernames_api(request, username=None):
    if username:
        MAX_RESULTS = 10
        matching_users = User.objects.filter(username__icontains=username)[:MAX_RESULTS]
        usernames = [user.username for user in matching_users]
        return JsonResponse({"usernames": usernames}, status=status.HTTP_200_OK)
    else:
        return JsonResponse(
            {"error": "Please provide a search term"},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["GET"])
@renderer_classes([JSONRenderer])
@login_required
def profile_info_api(request, username=None):
    try:
        if username:
            user = get_object_or_404(User, username=username)
            serializer = OtherUserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = PersonalUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except:
        return JsonResponse(
            {"error": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["GET"])
@renderer_classes([JSONRenderer])
@login_required
def is_active_api(request, username=None):
    try:
        if username:
            user = get_object_or_404(User, username=username)
            cur_time = timezone.now()
            last_active = cur_time - user.last_active < timedelta(minutes=5)
            return Response(last_active, status=status.HTTP_200_OK)
        return Response(
            {"error": "Please provide a username"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except:
        return JsonResponse(
            {"error": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["POST"])
@renderer_classes([JSONRenderer])
@login_required
def update_profile_api(request):
    try:
        user = request.user

        new_username = request.data.get("username")
        new_email = request.data.get("email")
        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")

        if not new_username and not new_email:
            return Response(
                {"error": "You must provide either a new username or a new email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            new_username
            and new_username != user.username
            and User.objects.filter(username=new_username).exists()
        ):
            return Response(
                {"error": "Username already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            new_email
            and new_email != user.email
            and User.objects.filter(email=new_email).exists()
        ):
            return Response(
                {"error": "Email already exists."}, status=status.HTTP_400_BAD_REQUEST
            )

        if new_username:
            user.username = new_username
        if new_email:
            user.email = new_email
        if first_name:
            user.first_name = first_name
        if last_name:
            user.first_name = first_name

        user.save()
        return Response(
            {"message": "User information updated successfully."},
            status=status.HTTP_200_OK,
        )
    except:
        return JsonResponse(
            {"error": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["POST"])
@renderer_classes([JSONRenderer])
@login_required
def change_password_api(request):
    try:
        user = request.user
        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")

        if not user.check_password(old_password):
            return JsonResponse(
                {"error": "Old password is incorrect"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if old_password == new_password:
            return JsonResponse(
                {"error": "New password must be different from the old one"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            password_validation.validate_password(new_password, user=user)
        except ValidationError as e:
            return JsonResponse(
                {"error": e.messages}, status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        update_session_auth_hash(request, user)
        return JsonResponse(
            {"message": "Password changed successfully"}, status=status.HTTP_200_OK
        )
    except Exception as e:
        return JsonResponse(
            {"error": "Bad request"}, status=status.HTTP_400_BAD_REQUEST
        )


@login_required
def test_password_change_view(request):
    return render(request, "test_password_change.html")


def MessageContentPwd(user):
    subject = "Forgot password"
    GenerateUserToken(user, mail=False)
    ResetLink = "https://127.0.0.1/api/pwd/" + user.username + "/" + user.token
    mailContent = f"""
    Hi {user.username}!
    There is the link for reset your password :
    <a href="{ResetLink}">Reset Password</a>

    DO NOT REPLY.
    """
    return subject, mailContent

def MessageContentMail(user):
    subject = "Mail Validation"
    GenerateUserToken(user, mail=True)
    ValidateLink = "https://127.0.0.1/api/mail/" + user.username + "/" + user.token
    mailContent = f"""
    Welcome to transcendence {user.username}!
    There is the link for validate the mail :
    <a href="{ValidateLink}">Mail validation</a>

    DO NOT REPLY.
    """
    return subject, mailContent




def sendMail(mail, isMail=False):
    smtp_server = 'mail.infomaniak.com'
    smtp_port = 587
    smtp_user = 'info@udrytech.ch'
    smtp_password = 'PQCG*fZJ6VjE&5z$uZv4'
    
    if isMail:
        subject, content = MessageContentMail
    else:
        subject, content = MessageContentPwd

    msg = MIMEText(content)
    msg['Subject'] = subject
    msg['From'] = smtp_user
    msg['To'] = mail
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_user, smtp_password)

    server.sendmail(smtp_user, mail, msg.as_string())
    server.quit()



def EmailValidation(request, username, token):
    users = User.objects.filter(username=username)
    if users.exists():
        user = users.first()
    else:
        raise Http404("Invalide link")
    if not token or user.token != token:
        raise Http404("Invalide link")
    else:
        user.mailValidate = True
        user.token = ""
        user.save()



def GenerateUserToken(user, mail=False):
    import secrets
    import string
    from random import randint

    characters = string.ascii_letters + string.digits
    tokenListe = User.objects.values_list('token', flat=True)
    while True:
        tokenLength = randint(22, 30)
        if mail:
            token = 'E'.join(secrets.choice(characters) for i in range(tokenLength))
        else:
            token = 'P'.join(secrets.choice(characters) for i in range(tokenLength))
        if token not in tokenListe:
            break
    user.token = token
