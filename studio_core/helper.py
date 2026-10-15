from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from rest_framework import status
import traceback
from rest_framework.exceptions import ErrorDetail
from datetime import datetime,timedelta,date
import uuid
from django.db.models import Q,Sum
import json
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django.core.exceptions import ValidationError
from functools import wraps
from rest_framework.response import Response
from django.utils import timezone

def validate_timezone(value: str) -> None:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValidationError(
            "Enter a valid IANA timezone, such as Asia/Kolkata."
        )



def is_anonymous(user):
    return type(user) is AnonymousUser



def get_key_errors_sub(err):
    if isinstance(err, dict):
        subkey, error = get_key_errors(err)
        return ".{}".format(subkey), error
    # Else, it's a list
    else:
        if (len(err) != 0) and (isinstance(err[0], ErrorDetail)):
            error = err[0]
            return "", error
        else:
            subkey, error = get_key_errors(err)
            return ".{}".format(subkey), error


def get_key_errors(errors):
    print(type(errors))
    if isinstance(errors, dict):
        firstKey = list(errors.keys())[0]
        err = errors[firstKey]
        if firstKey == "non_field_errors": keyName = ""
        else: keyName = firstKey.replace("_", " ")
        subkey, error = get_key_errors_sub(err)
        keyName += subkey

    else:
        index = 0
        for err in errors:
            if err: break
            index +=1
        print(index, err)
        keyName = str(index)
        subkey, error = get_key_errors_sub(err)
        keyName += subkey

    return keyName, error


def get_serializer_first_error(serializer):
    key, error = get_key_errors(serializer.errors)
    return key + ": " + error


def int_or_none(value):
    return int(value) if value is not None else None


def success(status_code, message, data):
    return JsonResponse({
        "status": 1,
        "message": message,
        "data": data
    }, status=status_code)


def failure(status_code, message, error = []):
    return JsonResponse({
        "status": 0,
        "message": message,
        "error": error,
    }, status=status_code)
    


def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            return Response(
                {
                    "status": 0,
                    "message": "Authentication required",
                    "data": {},
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        is_staff = user.details.filter(role="STAFF").exists()

        if not is_staff:
            return Response(
                {
                    "status": 0,
                    "message": "Only staff users can perform this action",
                    "data": {},
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return view_func(request, *args, **kwargs)

    return wrapper


