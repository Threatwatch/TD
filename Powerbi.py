# import msal

# # Replace these with your actual values
# CLIENT_ID = '5d6331c1-6fb5-4c0c-8cd4-a0bb40bb03af'
# CLIENT_SECRET = 'iS18Q~hXT7LriJaZDO0glu.SoGjaOttxsE1NOayt'
# TENANT_ID = 'cba06876-16e4-47c2-a8cd-ef4ec539e414'

# # Power BI API scope
# SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]

# # Authority URL
# AUTHORITY_URL = f'https://login.microsoftonline.com/{TENANT_ID}'

# # Create a Confidential Client Application instance
# app = msal.ConfidentialClientApplication(
#     CLIENT_ID,
#     authority=AUTHORITY_URL,
#     client_credential=CLIENT_SECRET
# )

# # Acquire token for the Power BI service
# def get_access_token():
#     result = app.acquire_token_for_client(scopes=SCOPE)
    
#     if "access_token" in result:
#         print("Access token generated successfully.")
#         return result["access_token"]
#     else:
#         print("Error acquiring token:")
#         print(result.get("error"))
#         print(result.get("error_description"))
#         print(result.get("correlation_id"))  # Helps to track errors in the logs
#         return None

# # Generate and print the access token
# access_token = get_access_token()
# print("Access Token:", access_token)
