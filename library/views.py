from django.http import HttpResponse


def request_info(request):
    lines = [
        f"method        : {request.method}",
        f"path          : {request.path}",
        f"full path     : {request.get_full_path()}",
        f"scheme        : {request.scheme}",
        f"host          : {request.get_host()}",
        f"GET params    : {dict(request.GET)}",
        f"POST params   : {dict(request.POST)}",
        f"content type  : {request.content_type}",
        f"user          : {request.user}",
        f"authenticated : {request.user.is_authenticated}",
        f"User-Agent    : {request.headers.get('User-Agent')}",
        f"Accept        : {request.headers.get('Accept')}",
        f"client IP     : {request.META.get('REMOTE_ADDR')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
