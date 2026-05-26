"""Read/write credentials from Windows Credential Manager + DPAPI encryption for local storage."""
import ctypes
import ctypes.wintypes
import json

CRED_TYPE_GENERIC = 1
CRED_PERSIST_LOCAL_MACHINE = 2
ANTIGRAVITY_TARGET = "gemini:antigravity"


class CREDENTIAL(ctypes.Structure):
    _fields_ = [
        ('Flags', ctypes.wintypes.DWORD),
        ('Type', ctypes.wintypes.DWORD),
        ('TargetName', ctypes.wintypes.LPWSTR),
        ('Comment', ctypes.wintypes.LPWSTR),
        ('LastWritten', ctypes.wintypes.FILETIME),
        ('CredentialBlobSize', ctypes.wintypes.DWORD),
        ('CredentialBlob', ctypes.POINTER(ctypes.c_byte)),
        ('Persist', ctypes.wintypes.DWORD),
        ('AttributeCount', ctypes.wintypes.DWORD),
        ('Attributes', ctypes.c_void_p),
        ('TargetAlias', ctypes.wintypes.LPWSTR),
        ('UserName', ctypes.wintypes.LPWSTR),
    ]


PCREDENTIAL = ctypes.POINTER(CREDENTIAL)
advapi32 = ctypes.windll.advapi32


def read_credential(target: str = ANTIGRAVITY_TARGET) -> dict | None:
    """Read a credential from Windows Credential Manager. Returns parsed JSON or None."""
    cred_ptr = PCREDENTIAL()
    ok = advapi32.CredReadW(target, CRED_TYPE_GENERIC, 0, ctypes.byref(cred_ptr))
    if not ok:
        return None
    try:
        cred = cred_ptr.contents
        blob_size = cred.CredentialBlobSize
        blob = bytes(ctypes.cast(cred.CredentialBlob, ctypes.POINTER(ctypes.c_byte * blob_size)).contents)
        return json.loads(blob.decode('utf-8'))
    finally:
        advapi32.CredFree(cred_ptr)


def write_credential(data: dict, target: str = ANTIGRAVITY_TARGET, username: str = "antigravity") -> bool:
    """Write a credential to Windows Credential Manager."""
    blob = json.dumps(data).encode('utf-8')
    blob_array = (ctypes.c_byte * len(blob))(*blob)

    cred = CREDENTIAL()
    cred.Flags = 0
    cred.Type = CRED_TYPE_GENERIC
    cred.TargetName = target
    cred.CredentialBlobSize = len(blob)
    cred.CredentialBlob = ctypes.cast(blob_array, ctypes.POINTER(ctypes.c_byte))
    cred.Persist = CRED_PERSIST_LOCAL_MACHINE
    cred.UserName = username

    return bool(advapi32.CredWriteW(ctypes.byref(cred), 0))





# --- DPAPI encryption for local profile storage ---

class DATA_BLOB(ctypes.Structure):
    _fields_ = [('cbData', ctypes.wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_byte))]


crypt32 = ctypes.windll.crypt32
kernel32 = ctypes.windll.kernel32


def encrypt_data(data: dict) -> bytes:
    """Encrypt JSON data using Windows DPAPI (only decryptable by current user)."""
    plaintext = json.dumps(data).encode('utf-8')
    blob_in = DATA_BLOB(len(plaintext), ctypes.cast(ctypes.create_string_buffer(plaintext, len(plaintext)), ctypes.POINTER(ctypes.c_byte)))
    blob_out = DATA_BLOB()

    if not crypt32.CryptProtectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
        raise OSError("DPAPI encryption failed")

    encrypted = bytes(ctypes.cast(blob_out.pbData, ctypes.POINTER(ctypes.c_byte * blob_out.cbData)).contents)
    kernel32.LocalFree(blob_out.pbData)
    return encrypted


def decrypt_data(encrypted: bytes) -> dict:
    """Decrypt DPAPI-encrypted data back to JSON dict."""
    blob_in = DATA_BLOB(len(encrypted), ctypes.cast(ctypes.create_string_buffer(encrypted, len(encrypted)), ctypes.POINTER(ctypes.c_byte)))
    blob_out = DATA_BLOB()

    if not crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
        raise OSError("DPAPI decryption failed")

    plaintext = bytes(ctypes.cast(blob_out.pbData, ctypes.POINTER(ctypes.c_byte * blob_out.cbData)).contents)
    kernel32.LocalFree(blob_out.pbData)
    return json.loads(plaintext.decode('utf-8'))
