from django.http import JsonResponse

class Unauthorized(Exception):
    def __init__(self, message="Unauthorized"):
        self.message = message
        super().__init__(self.message)

    def to_response(self):
        return JsonResponse({"error": self.message}, status=401)