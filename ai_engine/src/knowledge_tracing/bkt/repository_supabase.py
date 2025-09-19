import os
from supabase import create_client, Client

class SupabaseClient:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.client: Client = create_client(url, key)

    def table(self, name: str):
        return self.client.table(name)
