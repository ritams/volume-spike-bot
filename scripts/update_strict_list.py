#!/usr/bin/env python3
"""
Strict List Updater for Hyperliquid Volume Spike Bot
Updates strict_list.json with tokens based on strict criteria
"""

import os
import sys
import json
import requests
from typing import List

class StrictListUpdater:
    def __init__(self):
        self.json_file = "strict_list.json"
        
    def get_current_strict_list(self) -> List[str]:
        """Get current strict list from JSON file"""
        try:
            with open(self.json_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def update_strict_list(self, new_list: List[str]) -> bool:
        """Update strict list JSON file"""
        try:
            with open(self.json_file, 'w') as f:
                json.dump(new_list, f, indent=2)
            print(f"✅ Updated {self.json_file} with {len(new_list)} tokens")
            return True
        except Exception as e:
            print(f"❌ Error updating {self.json_file}: {e}")
            return False
    
    def fetch_strict_tokens(self) -> List[str]:
        """Fetch tokens based on strict criteria from Hyperliquid API"""
        print("🔍 Fetching strict tokens from Hyperliquid API...")
        
        url = "https://api.hyperliquid.xyz/info"
        payload = {"type": "meta"}
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            strict_tokens = []
            excluded_tokens = {"BTC", "ETH"}  # Exclude Bitcoin and Ethereum
            
            for token in data["universe"]:
                token_name = token["name"]
                
                # Skip Bitcoin and Ethereum
                if token_name in excluded_tokens:
                    continue
                    
                is_delisted = token.get("isDelisted", False)
                only_isolated = token.get("onlyIsolated", False)
                max_leverage = token.get("maxLeverage", 0)
                margin_table_id = token.get("marginTableId", 0)

                # Strict logic
                if not is_delisted and not only_isolated and max_leverage >= 10 and margin_table_id >= 51:
                    strict_tokens.append(token_name)

            print(f"📊 Found {len(strict_tokens)} tokens meeting strict criteria (excluding BTC/ETH)")
            return sorted(strict_tokens)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching from Hyperliquid API: {e}")
            return []
        except (KeyError, json.JSONDecodeError) as e:
            print(f"❌ Error parsing API response: {e}")
            return []
    
    def run(self):
        """Main execution function"""
        print("🚀 Hyperliquid Strict List Updater")
        print("=" * 40)
        
        current_list = self.get_current_strict_list()
        print(f"\n📋 Current: {len(current_list)} tokens")
        
        # Fetch new strict tokens
        new_list = self.fetch_strict_tokens()
        
        if new_list:
            print(f"\n📋 New list: {len(new_list)} tokens")
            print(f"Tokens: {', '.join(new_list[:10])}{'...' if len(new_list) > 10 else ''}")
            
            confirm = input("\nUpdate strict_list.json? (y/N): ").strip().lower()
            if confirm in ['y', 'yes']:
                if self.update_strict_list(new_list):
                    print("🎉 Updated! Restart bot to apply changes.")
                else:
                    print("❌ Update failed")
            else:
                print("👋 Cancelled")
        else:
            print("❌ No tokens found")

def main():
    updater = StrictListUpdater()
    updater.run()

if __name__ == "__main__":
    main() 