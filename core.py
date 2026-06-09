import os
import platform
import subprocess
import secrets
import mimetypes
import uuid
import stat
import shlex
import ctypes
import time
import logging
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Configure logging for enterprise auditing
logging.basicConfig(
    filename='sdw_audit.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

class SecureWiperCore:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        logging.info(f"New Sanitization Session Initialized: {self.session_id}")

    def is_admin(self):
        """Checks if the application is running with administrative/root privileges."""
        try:
            if platform.system() == "Windows":
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.getuid() == 0
        except Exception:
            return False

    def get_drive_type(self, target_path=None):
        """Identifies physical hardware to select the safest and most effective wipe method."""
        system = platform.system()
        if target_path is None:
            target_path = "C:\\" if system == "Windows" else "/"
            
        try:
            if system == "Linux":
                safe_path = shlex.quote(target_path)
                try:
                    cmd = f"df {safe_path} | tail -1 | awk '{{print $1}}'"
                    device = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
                    if device.startswith('/dev/'):
                        lsblk_cmd = f"lsblk -no ROTA {shlex.quote(device)} | head -1"
                        rota = subprocess.check_output(lsblk_cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
                        if rota == "1": return "Hard Disk Drive (HDD)"
                        if rota == "0": return "Solid State Drive (SSD)"
                except Exception:
                    pass
                return "Unknown Storage (Defaulting to SSD-Safe)"

            elif system == "Windows":
                try:
                    drive_letter = os.path.splitdrive(os.path.abspath(target_path))[0].upper()
                    if not drive_letter: drive_letter = 'C:'
                    ps_cmd = f"(Get-Partition -DriveLetter {drive_letter[0]} | Get-Disk).MediaType"
                    out = subprocess.check_output(['powershell', '-Command', ps_cmd], text=True, stderr=subprocess.DEVNULL).strip()
                    
                    if "SSD" in out.upper(): return "Solid State Drive (SSD)"
                    if "HDD" in out.upper(): return "Hard Disk Drive (HDD)"
                    if "UNSPECIFIED" in out.upper(): return "Generic Storage (SSD-Safe Mode)"
                except Exception:
                    pass
        except Exception:
            pass
        return "Generic Storage (SSD-Safe Mode)"

    def analyze_file(self, file_path):
        if not os.path.exists(file_path):
            return "Unknown"
        if os.path.isdir(file_path):
            return "Folder / Directory"
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > 100: return "Large Archive/File"
        mime, _ = mimetypes.guess_type(file_path)
        if mime:
            if mime.startswith('image/') or mime.startswith('video/'): return "Media (Image/Video)"
        return "Text/Data File"

    def select_algorithm(self, drive_type, file_type):
        if file_type == "Folder / Directory":
            return "Smart Batch Erasure"
        if "SSD" in drive_type or file_type == "Large Archive/File":
            return "Crypto-Shredding (AES-256 CTR)"
        elif "Media" in file_type:
            return "Header Corruption & Overwrite"
        else:
            return "NIST SP 800-88 3-Pass"

    def _sync(self, file_obj):
        file_obj.flush()
        try:
            os.fsync(file_obj.fileno())
        except Exception:
            pass 

    def execute_wipe(self, file_path, algorithm, progress_callback=None):
        logging.info(f"Target selected: {file_path} using algorithm: {algorithm}")
        if os.path.isdir(file_path):
            if progress_callback: progress_callback(0.0, "Scanning folder contents...")
            
            file_list = []
            for root, dirs, files in os.walk(file_path):
                for name in files:
                    file_list.append(os.path.join(root, name))
            
            total_files = len(file_list)
            if total_files == 0:
                try: os.rmdir(file_path)
                except: pass
                if progress_callback: progress_callback(1.0, "Empty folder deleted.")
                return
                
            processed = 0
            for root, dirs, files in os.walk(file_path, topdown=False):
                for name in files:
                    full_path = os.path.join(root, name)
                    try:
                        f_size = os.path.getsize(full_path)
                        f_size_str = f"({f_size / 1024:.1f} KB)"
                    except: f_size_str = ""

                    def sub_callback(val, msg=None):
                        overall_val = (processed + (val or 0)) / total_files
                        if progress_callback:
                            detailed_msg = f"[{processed+1}/{total_files}] {name} {f_size_str}: {msg}" if msg else None
                            progress_callback(overall_val, detailed_msg)

                    f_type = self.analyze_file(full_path)
                    d_type = self.get_drive_type(full_path)
                    spec_algo = self.select_algorithm(d_type, f_type)
                    
                    if "Smart" in spec_algo: spec_algo = "Crypto-Shredding (AES-256 CTR)"
                        
                    try:
                        self.execute_wipe_single(full_path, spec_algo, sub_callback)
                    except Exception as e:
                        logging.error(f"Failed to wipe {full_path}: {str(e)}")
                        if progress_callback: progress_callback(None, f"⚠️ Access Denied: {name}")
                    processed += 1
                
                for name in dirs:
                    dir_path = os.path.join(root, name)
                    try: 
                        os.chmod(dir_path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                        os.rmdir(dir_path)
                    except: pass
                    
            try: 
                os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                os.rmdir(file_path)
            except: pass
            if progress_callback: progress_callback(1.0, "Folder erasure complete.")
            
        else:
            self.execute_wipe_single(file_path, algorithm, progress_callback)

    def execute_wipe_single(self, file_path, algorithm, progress_callback=None):
        if os.path.islink(file_path):
            try: os.unlink(file_path)
            except: pass
            return

        if not os.path.exists(file_path): return

        try: os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
        except Exception: pass

        try: size = os.path.getsize(file_path)
        except Exception as e: raise Exception(f"Access Denied: {e}")
        
        if algorithm == "NIST SP 800-88 3-Pass":
            chunk_size = 1024 * 1024
            with open(file_path, "r+b") as f:
                # Pass 1: Zeros
                for w in range(0, size, chunk_size):
                    f.seek(w)
                    f.write(b'\x00' * min(chunk_size, size - w))
                    if progress_callback: progress_callback((w/size)*0.3, "Pass 1/3 (Zeros)")
                self._sync(f)
                
                # Pass 2: Ones
                for w in range(0, size, chunk_size):
                    f.seek(w)
                    f.write(b'\xff' * min(chunk_size, size - w))
                    if progress_callback: progress_callback(0.3 + (w/size)*0.3, "Pass 2/3 (Ones)")
                self._sync(f)

                # Pass 3: Random
                for w in range(0, size, chunk_size):
                    f.seek(w)
                    f.write(secrets.token_bytes(min(chunk_size, size - w)))
                    if progress_callback: progress_callback(0.6 + (w/size)*0.3, "Pass 3/3 (Random)")
                self._sync(f)

        elif algorithm == "Header Corruption & Overwrite":
            smash_size = min(16384, size)
            if smash_size > 0:
                with open(file_path, "r+b") as f:
                    f.write(secrets.token_bytes(smash_size))
                    self._sync(f)
            if progress_callback: progress_callback(0.8, "Structure Destroyed")

        elif "Crypto-Shredding" in algorithm:
            key = secrets.token_bytes(32) # AES-256
            nonce = secrets.token_bytes(16)
            cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
            encryptor = cipher.encryptor()
            
            chunk_size = 1024 * 1024
            with open(file_path, "r+b") as f:
                for w in range(0, size, chunk_size):
                    f.seek(w)
                    chunk = f.read(chunk_size)
                    if not chunk: break
                    f.seek(w)
                    f.write(encryptor.update(chunk))
                    if progress_callback: progress_callback((w/size)*0.8, "AES-256 Encryption Wipe")
                f.write(encryptor.finalize())
                self._sync(f)

        # --- ADVANCED METADATA WIPING (Timestomping & Obfuscation) ---
        try:
            # 1. Truncate payload
            with open(file_path, "wb") as f:
                f.truncate(0)
            
            # 2. Timestomp (Set to arbitrary past date)
            # 315532800 = Jan 1st 1980
            os.utime(file_path, (315532800, 315532800))
            
            # 3. Recursive Renaming
            dir_name = os.path.dirname(file_path)
            current_path = file_path
            for _ in range(3):
                new_path = os.path.join(dir_name, secrets.token_hex(8))
                try:
                    os.rename(current_path, new_path)
                    current_path = new_path
                except: break
            
            # 4. Final Removal
            os.remove(current_path)
            logging.info(f"Successfully eradicated: {file_path}")
        except Exception as e:
            logging.warning(f"Metadata wipe issue on {file_path}: {str(e)}")
            try: os.remove(file_path)
            except: pass

    def verify_wipe(self, file_path):
        time.sleep(0.3)
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                remnants = os.listdir(file_path)
                return len(remnants) == 0, remnants
            return False, ["File still exists"]
        return True, []
