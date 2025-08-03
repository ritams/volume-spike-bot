import os
import json
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    CHAT_ID = os.getenv('CHAT_ID')
    SIGMA_THRESHOLD = float(os.getenv('SIGMA_THRESHOLD', 2.0))
    Z_SCORE_THRESHOLD = float(os.getenv('Z_SCORE_THRESHOLD', 2.0))
    MARKET_CAP_THRESHOLD = float(os.getenv('MARKET_CAP_THRESHOLD', 200_000_000))
    UPDATE_INTERVAL_MINUTES = int(os.getenv('UPDATE_INTERVAL_MINUTES', 15))
    VOLUME_PERIODS = int(os.getenv('VOLUME_PERIODS', 20))
    
    # EMA-based momentum filtering options
    EMA_PERIODS = int(os.getenv('EMA_PERIODS', 21))
    PRICE_ABOVE_EMA_REQUIRED = os.getenv('PRICE_ABOVE_EMA_REQUIRED', 'true').lower() == 'true'
    EMA_SLOPE_FILTER_ENABLED = os.getenv('EMA_SLOPE_FILTER_ENABLED', 'true').lower() == 'true'
    
    # Strict list configuration
    @property
    def STRICT_LIST(self):
        """Get strict list of tokens from JSON file"""
        try:
            with open('strict_list.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    STRICT_LIST_ENABLED = os.getenv('STRICT_LIST_ENABLED', 'true').lower() == 'true'
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.BOT_TOKEN or not cls.CHAT_ID:
            print("⚠️  Warning: BOT_TOKEN and CHAT_ID not set - alerts will be printed to console")
        
        assert cls.SIGMA_THRESHOLD > 0, "SIGMA_THRESHOLD must be positive"
        assert cls.Z_SCORE_THRESHOLD > 0, "Z_SCORE_THRESHOLD must be positive"
        assert cls.UPDATE_INTERVAL_MINUTES > 0, "UPDATE_INTERVAL_MINUTES must be positive"
        assert cls.VOLUME_PERIODS > 1, "VOLUME_PERIODS must be > 1"
        assert cls.EMA_PERIODS > 0, "EMA_PERIODS must be positive"
        
        # Validate strict list
        config_instance = cls()
        strict_list = config_instance.STRICT_LIST
        if cls.STRICT_LIST_ENABLED and not strict_list:
            print("⚠️  Warning: STRICT_LIST_ENABLED=true but strict_list.json is empty")
        elif strict_list:
            print(f"📋 Monitoring {len(strict_list)} tokens from strict list")
        else:
            print(f"📊 Monitoring all available tokens (strict list disabled)") 