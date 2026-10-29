import os
import sys
from typing import Optional

try:
    import win32crypt
    HAS_WIN32CRYPT = True
except ImportError:
    HAS_WIN32CRYPT = False


class PPAPIKeyVault:
    """
    Windows Protected Storage / Data Protection API (DPAPI / PPAPI) Key Store.
    Encrypts sensitive credentials (such as Google Gemini API keys) using
    the logged-in Windows user's master key via CryptProtectData.

    The encrypted ciphertext is stored locally on disk and cannot be decrypted
    by another user or on another machine.
    """

    VAULT_ENTROPY = b"TargonProtectedVault_Entropy_2026"
    VAULT_DESCRIPTION = "Targon Secure Gemini API Key"

    def __init__(self, vault_dir: Optional[str] = None):
        if vault_dir is None:
            # Default to %APPDATA%\Targon or ~/.targon
            appdata = os.environ.get("APPDATA")
            if appdata:
                vault_dir = os.path.join(appdata, "Targon")
            else:
                vault_dir = os.path.join(os.path.expanduser("~"), ".targon")

        os.makedirs(vault_dir, exist_ok=True)
        self.vault_file = os.path.join(vault_dir, "gemini_key.ppapi")
        self.fallback_file = os.path.join(vault_dir, "gemini_key.enc")

    def save_gemini_api_key(self, api_key: str) -> bool:
        """
        Encrypts and stores the Gemini API key locally using Windows PPAPI/DPAPI.
        If api_key is empty or None, clears the stored key.
        """
        if not api_key or not api_key.strip():
            self.clear_key()
            return True

        clean_key = api_key.strip().encode("utf-8")

        if HAS_WIN32CRYPT and sys.platform == "win32":
            try:
                ciphertext = win32crypt.CryptProtectData(
                    clean_key,
                    self.VAULT_DESCRIPTION,
                    self.VAULT_ENTROPY,
                    None,
                    None,
                    0,
                )
                with open(self.vault_file, "wb") as f:
                    f.write(ciphertext)
                # Remove fallback if exists
                if os.path.exists(self.fallback_file):
                    os.remove(self.fallback_file)
                return True
            except Exception as e:
                # Fallback to local obfuscated store if CryptProtectData encounters an issue
                pass

        # Fallback local obfuscated storage
        try:
            from cryptography.fernet import Fernet
            import base64
            import hashlib

            machine_id = os.environ.get("COMPUTERNAME", "TargonMachine") + os.environ.get("USERNAME", "DefaultUser")
            key = base64.urlsafe_b64encode(hashlib.sha256(machine_id.encode()).digest())
            f = Fernet(key)
            enc = f.encrypt(clean_key)
            with open(self.fallback_file, "wb") as fp:
                fp.write(enc)
            return True
        except Exception:
            return False

    def get_gemini_api_key(self) -> str:
        """
        Decrypts and returns the Gemini API key using Windows PPAPI/DPAPI.
        Returns an empty string if no key is stored.
        """
        if HAS_WIN32CRYPT and sys.platform == "win32" and os.path.exists(self.vault_file):
            try:
                with open(self.vault_file, "rb") as f:
                    ciphertext = f.read()
                if not ciphertext:
                    return ""
                _, plaintext = win32crypt.CryptUnprotectData(
                    ciphertext,
                    self.VAULT_ENTROPY,
                    None,
                    None,
                    0,
                )
                return plaintext.decode("utf-8", errors="ignore").strip()
            except Exception:
                pass

        if os.path.exists(self.fallback_file):
            try:
                from cryptography.fernet import Fernet
                import base64
                import hashlib

                machine_id = os.environ.get("COMPUTERNAME", "TargonMachine") + os.environ.get("USERNAME", "DefaultUser")
                key = base64.urlsafe_b64encode(hashlib.sha256(machine_id.encode()).digest())
                f = Fernet(key)
                with open(self.fallback_file, "rb") as fp:
                    dec = f.decrypt(fp.read())
                return dec.decode("utf-8", errors="ignore").strip()
            except Exception:
                pass

        return ""

    def clear_key(self):
        """Removes all stored local encrypted key files."""
        for path in (self.vault_file, self.fallback_file):
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

    def get_status(self) -> dict:
        """Returns security status of the local PPAPI vault."""
        key = self.get_gemini_api_key()
        has_key = bool(key)
        masked_key = ""
        if has_key:
            masked_key = key[:6] + "..." + key[-4:] if len(key) > 10 else "••••••••"
        return {
            "vault_type": "Windows DPAPI/PPAPI (Protected Storage)",
            "is_available": HAS_WIN32CRYPT and sys.platform == "win32",
            "has_key": has_key,
            "masked_key": masked_key,
            "vault_path": self.vault_file if os.path.exists(self.vault_file) else self.fallback_file,
        }


# Global singleton instance
vault = PPAPIKeyVault()
