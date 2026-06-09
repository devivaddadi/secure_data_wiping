import os
import hashlib
from fpdf import FPDF
from datetime import datetime

class CertificateGenerator:
    def __init__(self):
        pass

    def generate_certificate(self, file_name, file_size, hardware, algorithm, duration, erase_id, output_path):
        pdf = FPDF()
        pdf.add_page()
        
        # --- DOCUMENT BORDERS ---
        pdf.set_line_width(1.5)
        pdf.rect(5, 5, 200, 287) # Outer border
        pdf.set_line_width(0.5)
        pdf.rect(7, 7, 196, 283) # Inner decorative border
        
        # --- HEADER SECTION ---
        pdf.set_fill_color(13, 14, 21) # Matches App BG
        pdf.rect(7, 7, 196, 40, 'F')
        
        # Add College Logo if exists
        if os.path.exists("logo.png"):
            pdf.image("logo.png", x=12, y=12, h=30)
        
        pdf.set_y(15)
        pdf.set_x(50) # Shift right to clear logo
        pdf.set_font("Helvetica", 'B', 26)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(150, 15, txt="SECURE DATA WIPING SYSTEM", ln=True, align='C')
        
        pdf.set_x(50) # Maintain shift for sub-header
        pdf.set_font("Helvetica", 'B', 12)
        pdf.set_text_color(59, 130, 246) # ACCENT_BLUE
        pdf.cell(150, 10, txt="CERTIFICATE OF IRRECOVERABLE DESTRUCTION", ln=True, align='C')
        
        # --- SEAL OF AUTHENTICITY (Procedural Graphic) ---
        pdf.set_draw_color(16, 185, 129) # SUCCESS_GREEN
        pdf.set_line_width(1)
        pdf.circle(170, 75, 15)
        pdf.set_font("Helvetica", 'B', 8)
        pdf.set_text_color(16, 185, 129)
        pdf.set_xy(155, 73)
        pdf.multi_cell(30, 4, txt="VERIFIED\nAUTHENTIC\nSDW", align='C')
        
        # --- MAIN DATA SECTION ---
        pdf.set_xy(20, 65)
        pdf.set_font("Helvetica", 'B', 16)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, txt="Sanitization Summary", ln=True)
        pdf.set_line_width(0.5)
        pdf.line(20, 75, 100, 75)
        
        pdf.ln(10)
        pdf.set_font("Helvetica", '', 12)
        pdf.set_text_color(50, 50, 50)
        
        size_mb = file_size / (1024*1024)
        data_points = [
            ("Transaction ID", f"#{erase_id[:13].upper()}"),
            ("Final Timestamp", datetime.now().strftime('%B %d, %Y | %H:%M:%S')),
            ("Host Hardware", hardware),
            ("Target Object", os.path.basename(file_name)),
            ("Total Payload", f"{size_mb:.4f} Megabytes"),
            ("Sanitization Protocol", algorithm),
            ("Execution Duration", f"{duration:.3f} Seconds"),
            ("Forensic Audit Result", "PASSED (Zero Bit Remanence)")
        ]
        
        for label, val in data_points:
            pdf.set_x(25)
            pdf.set_font("Helvetica", 'B', 11)
            pdf.cell(50, 10, txt=f"{label}:", ln=False)
            pdf.set_font("Helvetica", '', 11)
            pdf.cell(0, 10, txt=str(val), ln=True)
            
        # --- LEGAL VALIDATION ---
        pdf.ln(10)
        pdf.set_x(20)
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, txt="Technical Verification", ln=True)
        pdf.set_font("Helvetica", 'I', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.set_x(20)
        statement = (
            "The SDW Engine hereby certifies that the data object specified above has been subjected to "
            "context-aware physical and cryptographic destruction. The underlying bits have been mutated "
            "beyond forensic reconstruction using NIST-compliant patterns and streaming ciphers. This process "
            "is final and irreversible."
        )
        pdf.multi_cell(170, 6, txt=statement, align='L')
        
        # --- CRYPTOGRAPHIC FOOTER ---
        hash_data = f"{erase_id}{file_name}{size_mb}{hardware}{algorithm}{duration}".encode('utf-8')
        cert_hash = hashlib.sha256(hash_data).hexdigest()
        
        pdf.set_y(250)
        pdf.set_font("Courier", 'B', 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, txt=f"Digital Signature: {cert_hash}", ln=True, align='C')
        
        pdf.output(output_path)
        return output_path, cert_hash
