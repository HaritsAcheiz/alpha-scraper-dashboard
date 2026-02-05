import streamlit_authenticator as stauth

# 1. Create a credentials dictionary
creds = {
    'usernames': {
        'admin': {'password': 'adminalpha'},
        'editor': {'password': 'editoralpha'},
        'viewer': {'password': 'vieweralpha'}
    }
}

stauth.Hasher.hash_passwords(creds)

# 3. Print the results
for username, data in creds['usernames'].items():
    print(f"Password for {username}: {data['password']}")