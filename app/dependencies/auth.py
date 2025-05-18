from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from app.core.config import SUPABASE_URL, SUPABASE_KEY
import httpx

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = credentials.credentials  # Bearer token của user
    try:
        # Dùng token này để xác thực user
        user_resp = supabase.auth.get_user(token)
        user = user_resp.user

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        return {
            "id": user.id,
            "email": user.email,
            "role": getattr(user, "role", None)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
        )

def delete_auth_user(anonymous_user_id: str):
    """
    Xóa user từ bảng auth.users qua Admin API.
    SUPABASE_KEY đã là Service Role Key, đủ quyền DELETE user.
    """
    url = f"{SUPABASE_URL}/auth/v1/admin/users/{anonymous_user_id}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    response = httpx.delete(url, headers=headers)

    if response.status_code == 204:
        print("Anonymous user deleted successfully.")
    else:
        print("Error deleting user:", response.status_code, response.text)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete anonymous user"
        )
