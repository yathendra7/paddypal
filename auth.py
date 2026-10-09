
import streamlit as st
import sqlite3
import hashlib
import re
import base64
from pathlib import Path

# -----------------------------
# Configuration
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
DB_NAME = BASE_DIR / "users.db"
LOGO_PATH = BASE_DIR / "logo.png"


# -----------------------------
# Database
# -----------------------------
def get_connection():
    return sqlite3.connect(str(DB_NAME))


def create_users_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)


# -----------------------------
# PaddyPal Logo
# -----------------------------
def show_paddypal_logo(width=220):
    if not LOGO_PATH.exists():
        st.warning(f"Logo not found: {LOGO_PATH}")
        return

    image_bytes = LOGO_PATH.read_bytes()
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    suffix = LOGO_PATH.suffix.lower()
    mime_type = (
        "image/jpeg"
        if suffix in (".jpg", ".jpeg")
        else "image/png"
    )

    st.markdown(
        f"""
        <div style="
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            margin: 10px auto 24px auto;
        ">
            <img
                src="data:{mime_type};base64,{encoded_image}"
                alt="PaddyPal Logo"
                style="width:{width}px; max-width:90%; height:auto;"
            />
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# Password Hashing
# -----------------------------
def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# -----------------------------
# Identifier Validation
# -----------------------------
def normalize_identifier(identifier):
    identifier = identifier.strip()

    if "@" in identifier:
        return identifier.casefold()

    return identifier


def valid_identifier(identifier):
    identifier = identifier.strip()

    email_pattern = (
        r"^[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )

    phone_pattern = r"^\+?[0-9]{10,15}$"

    return bool(
        re.fullmatch(email_pattern, identifier)
        or re.fullmatch(phone_pattern, identifier)
    )


# -----------------------------
# Create Account
# -----------------------------
def create_user(identifier, password):
    identifier = normalize_identifier(identifier)

    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (identifier, password)
                VALUES (?, ?)
                """,
                (identifier, hash_password(password)),
            )

        return True

    except sqlite3.IntegrityError:
        return False


# -----------------------------
# Check Login
# -----------------------------
def check_user(identifier, password):
    identifier = normalize_identifier(identifier)

    with get_connection() as conn:
        user = conn.execute(
            """
            SELECT id
            FROM users
            WHERE identifier = ? AND password = ?
            """,
            (identifier, hash_password(password)),
        ).fetchone()

    return user is not None


# -----------------------------
# Login / Signup Page
# -----------------------------
def login_page():
    # Logo is displayed only here on the login/signup page.
    show_paddypal_logo(width=220)

    st.markdown(
        """
        <h1 style="text-align:center;">🌾 PaddyPal Login</h1>
        <p style="text-align:center;">
            AI-Based Rice Leaf Disease Detection System
        </p>
        """,
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1, 2, 1])

    with center:
        login_tab, signup_tab = st.tabs(
            ["Login", "Create Account"]
        )

        # -----------------------------
        # Login
        # -----------------------------
        with login_tab:
            login_identifier = st.text_input(
                "Email or Phone Number",
                key="login_identifier",
            )

            login_password = st.text_input(
                "Password",
                type="password",
                key="login_password",
            )

            if st.button("Login", use_container_width=True):
                if not login_identifier or not login_password:
                    st.warning(
                        "Please enter your email/phone and password."
                    )

                elif not valid_identifier(login_identifier):
                    st.error(
                        "Please enter a valid email or phone number."
                    )

                elif check_user(login_identifier, login_password):
                    st.session_state["logged_in"] = True
                    st.session_state["identifier"] = (
                        normalize_identifier(login_identifier)
                    )
                    st.rerun()

                else:
                    st.error("Invalid email/phone or password.")

        # -----------------------------
        # Signup
        # -----------------------------
        with signup_tab:
            signup_identifier = st.text_input(
                "Email or Phone Number",
                key="signup_identifier",
            )

            signup_password = st.text_input(
                "Create Password",
                type="password",
                key="signup_password",
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                key="confirm_password",
            )

            if st.button(
                "Create Account",
                use_container_width=True,
            ):
                if (
                    not signup_identifier
                    or not signup_password
                    or not confirm_password
                ):
                    st.warning("Please fill all fields.")

                elif not valid_identifier(signup_identifier):
                    st.error(
                        "Enter a valid email or phone number."
                    )

                elif len(signup_password) < 6:
                    st.error(
                        "Password must be at least 6 characters."
                    )

                elif signup_password != confirm_password:
                    st.error("Passwords do not match.")

                elif create_user(
                    signup_identifier,
                    signup_password,
                ):
                    st.success(
                        "Account created successfully! Please login."
                    )

                else:
                    st.error(
                        "This email/phone is already registered."
                    )


# -----------------------------
# Logout
# -----------------------------
def logout():
    if st.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["identifier"] = ""
        st.rerun()


# -----------------------------
# Initialize Database
# -----------------------------
create_users_table()
