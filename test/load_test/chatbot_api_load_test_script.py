from locust import HttpUser, task, between


class ChatbotUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def post_question(self):
        user_id = 1  # 사용자 Id를 설정합니다.
        q_content = "안녕"  # 질문 내용을 설정합니다.

        payload = {
            "user_id": user_id,
            "q_content": q_content
        }

        # headers = {
        #     "Content-Type": "application/json"
        # }

        # Chatbot API에 POST 요청을 보냅니다.
        # response = self.client.post("/api/chatbot", json=payload, headers=headers)
        response = self.client.post("/chatbot/", json=payload)

        # 요청 결과를 출력합니다. (Optional)
        print(response.status_code)
        print(response.text)
