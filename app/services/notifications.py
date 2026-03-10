import os
import firebase_admin
from firebase_admin import credentials, messaging

# Initialize Firebase only once
_firebase_initialized = False

def init_firebase():
    global _firebase_initialized
    if _firebase_initialized:
        return
        
    # Expecting the service account JSON path in environment variable
    cred_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
    try:
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            print("Firebase Admin initialized successfully.")
        else:
            print("FIREBASE_CREDENTIALS_PATH not set or file not found. Push notifications will be mocked.")
    except Exception as e:
        print(f"Failed to initialize Firebase Admin: {e}")

def send_push_notification(fcm_token: str, title: str, body: str, data: dict = None):
    """
    Sends a push notification to a specific device using its FCM token.
    """
    if not _firebase_initialized:
        # Mocking for local development or when credentials are not available
        print(f"[MOCK PUSH NOTIFICATION] To: {fcm_token} | Title: {title} | Body: {body} | Data: {data}")
        return True
        
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=fcm_token,
        )
        response = messaging.send(message)
        print(f"Successfully sent message: {response}")
        return True
    except Exception as e:
        print(f"Error sending push notification: {e}")
        return False

# Initialize on module load
init_firebase()
