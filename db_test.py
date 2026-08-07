import asyncio
import sys
import os

# Ensure the app module can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.models.database import engine, Base, async_session, create_user, authenticate_user, User
from sqlalchemy import select

async def main():
    print("--- Testing Database End-to-End ---")
    try:
        print("1. Initializing DB connection and tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("[SUCCESS] DB initialized.")

        test_username = "testuser_e2e"
        test_password = "securepassword123"
        test_role = "user"

        async with async_session() as session:
            # Check if exists first to clean up
            result = await session.execute(select(User).where(User.username == test_username))
            existing_user = result.scalar_one_or_none()
            if existing_user:
                print("Found existing test user, deleting for fresh test...")
                await session.delete(existing_user)
                await session.commit()

            print(f"2. Creating new user '{test_username}'...")
            new_user = await create_user(session, test_username, test_password, test_role)
            if new_user:
                print("[SUCCESS] User created.")
            else:
                print("[FAILED] Could not create user.")
                return

            print("3. Authenticating user with correct password...")
            auth_success = await authenticate_user(session, test_username, test_password, test_role)
            if auth_success:
                print("[SUCCESS] Authentication successful.")
            else:
                print("[FAILED] Authentication failed with correct credentials.")

            print("4. Authenticating user with WRONG password...")
            auth_fail = await authenticate_user(session, test_username, "wrongpass", test_role)
            if not auth_fail:
                print("[SUCCESS] Authentication correctly rejected wrong password.")
            else:
                print("[FAILED] Authentication succeeded with wrong password!")

            print("5. Cleaning up test user...")
            result = await session.execute(select(User).where(User.username == test_username))
            user_to_delete = result.scalar_one_or_none()
            if user_to_delete:
                await session.delete(user_to_delete)
                await session.commit()
                print("[SUCCESS] Cleaned up.")

    except Exception as e:
        print(f"\n[ERROR] Database test failed:\n{e}")

if __name__ == "__main__":
    asyncio.run(main())
