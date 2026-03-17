# auth.py
import hashlib
import streamlit as st
from sheets import get_user, create_user

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def login_form():
    """מציג טופס לוגין ומחזיר True אם המשתמש מחובר"""
    if st.session_state.get("authenticated"):
        return True

    st.markdown("## 🏆 כניסה לקזינו ליגת האלופות")

    with st.form("login_form"):
        username = st.text_input("שם משתמש")
        password = st.text_input("סיסמה", type="password")
        submitted = st.form_submit_button("כניסה")

        if submitted:
            if not username or not password:
                st.error("נא למלא שם משתמש וסיסמה")
                return False

            user = get_user(username)
            if user is None:
                st.error("שם משתמש לא קיים")
                return False

            if not verify_password(password, str(user["hashed_password"])):
                st.error("סיסמה שגויה")
                return False

            # שמירה ב-session
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.session_state["is_admin"] = str(user["is_admin"]).lower() == "true"
            st.cache_data.clear()
            st.rerun()

    return False

def logout():
    for key in ["authenticated", "username", "is_admin", "current_group"]:
        st.session_state.pop(key, None)
    st.cache_data.clear()
    st.rerun()

def require_auth():
    """decorator-style — קורא לזה בתחילת כל דף"""
    if not st.session_state.get("authenticated"):
        login_form()
        st.stop()

def require_admin():
    require_auth()
    if not st.session_state.get("is_admin"):
        st.error("אין לך הרשאות אדמין")
        st.stop()