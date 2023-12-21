from Crypto.Cipher import AES
from os import urandom
import struct

def encrypt (key, value):
    assert key, 'No key set'
    assert (len(key) == 16)
    k = bytearray (key)
    val = bytearray(value.ljust (16, b'\x00'))
    k.reverse ()
    val.reverse ()
    cipher = AES.new(bytes(k), AES.MODE_ECB)
    val = bytearray (cipher.encrypt (bytes(val)))
    val.reverse ()
    return val

def make_checksum (key, nonce, payload):
    """
    Args :
        key: Encryption key, 16 bytes
        nonce:
        payload: The unencrypted payload.
    """
    base = nonce + bytearray ([len(payload)])
    base = base.ljust (16, b'\x00')
    check = encrypt (key, base)

    for i in range (0, len (payload), 16):
        check_payload = bytearray (payload[i:i+16].ljust (16, b'\x00'))
        check = bytearray([ a ^ b for (a,b) in zip(check, check_payload) ])
        check = encrypt (key, check)

    return check

def crypt_payload (key, nonce, payload):
    """
    Used for both encrypting and decrypting.

    """
    base = bytearray(b'\x00' + nonce)
    base = base.ljust (16, b'\x00')
    result = bytearray ()

    for i in range (0, len (payload), 16):
        enc_base = encrypt (key, base)
        result += bytearray ([ a ^ b for (a,b) in zip (enc_base, bytearray (payload[i:i+16]))])
        base[0] += 1

    return result

def make_command_packet (key, address, dest_id, command, data):
    """
    Args :
        key: The encryption key, 16 bytes.
        address: The mac address as a string.
        dest_id: The mesh id of the command destination as a number.
        command: The command as a number.
        data: The parameters for the command as bytes.
    """
    # Sequence number, just need to be different, idea from https://github.com/nkaminski/csrmesh
    s = urandom (3)

    # Build nonce
    a = bytearray.fromhex(address.replace (":",""))
    a.reverse()
    nonce = bytes(a[0:4] + b'\x01' + s)

    # Build payload
    dest = struct.pack ("<H", dest_id)
    payload = (dest + struct.pack('B', command) + b'\x11\x02' + data).ljust(15, b'\x00') #Change b'\x60\x01 to b'\x11\x02

    # Compute checksum
    check = make_checksum (key, nonce, payload)

    # Encrypt payload
    payload = crypt_payload (key, nonce, payload)

    # Make packet
    packet = s + check[0:2] + payload
    return packet
 
def decrypt_packet (key, address, packet):
    """
    Args :
        address: The mac address as a string.
        packet : The 20 bytes packet read on the characteristic.

    Returns :
        The packet with the payload part decrypted, or None if the checksum 
        didn't match.
        
    """
    # Build nonce
    a = bytearray.fromhex(address.replace (":",""))
    a.reverse()
    nonce = bytes(a[0:3] + packet[0:5])

    # Decrypt Payload
    payload = crypt_payload (key, nonce, packet[7:])

    # Compute checksum
    check = make_checksum (key, nonce, payload)

    # Check bytes
    if check[0:2] != packet [5:7] :
        return None

    # Decrypted packet
    dec_packet = packet [0:7] + payload
    return dec_packet

def make_pair_packet (mesh_name, mesh_password, session_random):
    m_n = bytearray (mesh_name.ljust (16, b'\x00'))
    m_p = bytearray (mesh_password.ljust (16, b'\x00'))
    s_r = session_random.ljust (16, b'\x00')
    name_pass = bytearray ([ a ^ b for (a,b) in zip(m_n, m_p) ])
    enc = encrypt (s_r ,name_pass)
    packet = bytearray(b'\x0c' + session_random) # 8bytes session_random
    packet += enc[0:8]
    return packet

def make_session_key (mesh_name, mesh_password, session_random, response_random):
    random = session_random + response_random
    m_n = bytearray (mesh_name.ljust (16, b'\x00'))
    m_p = bytearray (mesh_password.ljust (16, b'\x00'))
    name_pass = bytearray([ a ^ b for (a,b) in zip(m_n, m_p) ])
    key = encrypt (name_pass, random)
    return key

def crc16 (array):
    poly_array = [0x0, 0xa001]
    crc = 0xffff
    for val in bytearray (array):
        for i in range (0, 8):
            ind = (crc ^ val) & 0x1
            crc = (crc >> 1) ^ poly_array [ind]
            val = val >> 1
    return crc
