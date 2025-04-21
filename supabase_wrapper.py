from supabase import create_client as original_create_client
from supabase.lib.client_options import ClientOptions

def create_client_without_proxy(url, key, **kwargs):
    """
    カスタムSupabaseクライアント作成関数
    proxyパラメータを無視して安全に初期化します
    """
    if 'proxy' in kwargs:
        del kwargs['proxy']
    
    options = ClientOptions(
        schema='public',
        headers={'X-Client-Info': 'supabase-py/2.3.1'},
        auto_refresh_token=True,
        persist_session=True
    )
    
    return original_create_client(url, key, options=options)
