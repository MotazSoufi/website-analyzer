import os
from getpass import getpass
import instaloader
from dotenv import load_dotenv

load_dotenv(override=True)
username = os.getenv("INSTAGRAM_USERNAME")

loader = instaloader.Instaloader()

# Hidden input: nothing will show when you paste, just press Enter
sessionid = getpass("Paste sessionid: ").strip()
csrftoken = getpass("Paste csrftoken: ").strip()
ds_user_id = getpass("Paste ds_user_id: ").strip()

# Put the browser's login cookies into Instaloader
for name, value in [("sessionid", sessionid), ("csrftoken", csrftoken), ("ds_user_id", ds_user_id)]:
    loader.context._session.cookies.set(name, value, domain=".instagram.com")

loader.context.username = username  # we tell it the username instead of asking Instagram
loader.save_session_to_file("instagram_session")
print(f"Saved session for {username}")