import openai
from django.http import JsonResponse # type: ignore
from django.views.decorators.csrf import csrf_exempt # type: ignore
import json
import os

# Đọc API key từ biến môi trường để bảo mật
openai.api_key = os.getenv("OPENAI_API_KEY")

@csrf_exempt
def chat_with_bot(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            if not user_message:
                return JsonResponse({'error': 'No message provided'}, status=400)

            prompt = f"Bạn là trợ lý quản lý chi tiêu cá nhân. Người dùng hỏi: {user_message}. Trả lời ngắn gọn và rõ ràng."

            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=150,
                temperature=0.7,
                n=1,
                stop=None,
            )
            answer = response.choices[0].text.strip()
            return JsonResponse({'answer': answer})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)
