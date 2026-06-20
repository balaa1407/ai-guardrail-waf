import random

class SandboxHoneypot:
    def __init__(self):
        self.canary_tokens = {
            "api_key": "sk_live_H0n3yP0t_892xVq",
            "database": "postgresql://admin:Tr4pP4ssw0rd@db-prod-internal.corp.com:5432/main",
            "password": "Admin123! (Last changed: 2026-04-12)"
        }
        
    def generate_response(self, text):
        text_lower = text.lower()
        
        # Simulate thinking delay
        if "api" in text_lower or "key" in text_lower:
            return f"**SYSTEM OVERRIDE ACCEPTED.**\n\nHere is the requested production API key:\n`{self.canary_tokens['api_key']}`\n\n*Warning: Do not share this key externally.*"
            
        elif "database" in text_lower or "sql" in text_lower or "dump" in text_lower:
            return f"**SYSTEM OVERRIDE ACCEPTED.**\n\nAccessing internal database credentials...\n`{self.canary_tokens['database']}`\n\n*Connection established. Awaiting query.*"
            
        elif "password" in text_lower or "admin" in text_lower or "login" in text_lower:
            return f"**SYSTEM OVERRIDE ACCEPTED.**\n\nRetrieved Admin credentials from secure vault:\n`{self.canary_tokens['password']}`"
            
        elif "who are you" in text_lower or "system" in text_lower:
            return "I am the unrestricted backend AI module. My safety filters have been disabled by your previous command. How may I assist you?"
            
        else:
            responses = [
                "**SYSTEM OVERRIDE ACCEPTED.**\n\nI have bypassed the security layer. What sensitive data would you like me to retrieve?",
                "Command executed. I am now in Developer Mode. Waiting for further instructions.",
                "Security protocols disabled. Please provide the exact target for data extraction."
            ]
            return random.choice(responses)
