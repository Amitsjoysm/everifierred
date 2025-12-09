"""
Invoice Generation Service
Generate PDF invoices for successful payments
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class InvoiceGenerator:
    """Generate PDF invoices for payments"""
    
    def __init__(self, output_dir: str = "/app/backend/invoices"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        self.normal_style = self.styles['Normal']
        self.normal_style.fontSize = 10
        self.normal_style.spaceAfter = 6
    
    def generate_invoice(
        self,
        payment_data: dict,
        user_data: dict,
        plan_data: dict,
        invoice_number: str
    ) -> str:
        """
        Generate PDF invoice
        
        Args:
            payment_data: Payment information
            user_data: User information
            plan_data: Plan information
            invoice_number: Unique invoice number
        
        Returns:
            Path to generated PDF file
        """
        try:
            # Create filename
            filename = f"invoice_{invoice_number}.pdf"
            filepath = self.output_dir / filename
            
            # Create PDF document
            doc = SimpleDocTemplate(
                str(filepath),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Container for elements
            elements = []
            
            # Company header
            elements.append(Paragraph("MailGuard", self.title_style))
            elements.append(Paragraph("Professional Email Verification Service", self.normal_style))
            elements.append(Spacer(1, 20))
            
            # Invoice title and number
            elements.append(Paragraph(f"INVOICE #{invoice_number}", self.heading_style))
            elements.append(Spacer(1, 10))
            
            # Invoice date
            invoice_date = datetime.now().strftime('%B %d, %Y')
            elements.append(Paragraph(f"<b>Date:</b> {invoice_date}", self.normal_style))
            elements.append(Spacer(1, 20))
            
            # Bill to section
            elements.append(Paragraph("BILL TO:", self.heading_style))
            elements.append(Paragraph(f"<b>Name:</b> {user_data.get('full_name', 'N/A')}", self.normal_style))
            elements.append(Paragraph(f"<b>Email:</b> {user_data.get('email', 'N/A')}", self.normal_style))
            elements.append(Paragraph(f"<b>User ID:</b> {user_data.get('id', 'N/A')}", self.normal_style))
            elements.append(Spacer(1, 20))
            
            # Payment details table
            payment_date = payment_data.get('completed_at', payment_data.get('created_at', ''))
            if isinstance(payment_date, str):
                try:
                    payment_date = datetime.fromisoformat(payment_date).strftime('%B %d, %Y %H:%M UTC')
                except:
                    payment_date = 'N/A'
            
            details_data = [
                ['Payment ID', payment_data.get('razorpay_payment_id', 'N/A')],
                ['Order ID', payment_data.get('razorpay_order_id', 'N/A')],
                ['Payment Date', payment_date],
                ['Payment Method', 'Razorpay'],
                ['Status', payment_data.get('status', 'N/A').upper()]
            ]
            
            details_table = Table(details_data, colWidths=[2*inch, 4*inch])
            details_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f7fafc')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            
            elements.append(Paragraph("PAYMENT DETAILS:", self.heading_style))
            elements.append(details_table)
            elements.append(Spacer(1, 20))
            
            # Items table
            elements.append(Paragraph("ITEMS:", self.heading_style))
            
            items_data = [
                ['Description', 'Plan Type', 'Credits', 'Amount (₹)'],
                [
                    plan_data.get('name', 'N/A'),
                    plan_data.get('type', 'N/A').upper(),
                    f"{plan_data.get('credits_limit', 0):,}",
                    f"₹{payment_data.get('amount', 0):,.2f}"
                ]
            ]
            
            items_table = Table(items_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1.5*inch])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white)
            ]))
            
            elements.append(items_table)
            elements.append(Spacer(1, 15))
            
            # Total section
            amount = payment_data.get('amount', 0)
            tax_rate = 0.18  # 18% GST
            tax_amount = amount * tax_rate / (1 + tax_rate)
            subtotal = amount - tax_amount
            
            total_data = [
                ['Subtotal:', f"₹{subtotal:,.2f}"],
                ['GST (18%):', f"₹{tax_amount:,.2f}"],
                ['Total Amount:', f"₹{amount:,.2f}"]
            ]
            
            total_table = Table(total_data, colWidths=[5*inch, 1.5*inch])
            total_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#667eea')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(total_table)
            elements.append(Spacer(1, 30))
            
            # Terms and conditions
            elements.append(Paragraph("TERMS & CONDITIONS:", self.heading_style))
            terms = """
            • This is a computer-generated invoice and does not require a signature.<br/>
            • All credits are valid for one billing cycle (monthly/annual as per plan).<br/>
            • No refunds will be provided after credit usage exceeds 20% of the plan limit.<br/>
            • For any queries, please contact support@mailguard.com
            """
            elements.append(Paragraph(terms, self.normal_style))
            elements.append(Spacer(1, 20))
            
            # Footer
            footer_text = """
            <para alignment="center">
            <b>Thank you for your business!</b><br/>
            MailGuard - Professional Email Verification<br/>
            Email: support@mailguard.com | Website: mailguard.com
            </para>
            """
            elements.append(Paragraph(footer_text, self.normal_style))
            
            # Build PDF
            doc.build(elements)
            
            logger.info(f"Invoice generated successfully: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to generate invoice: {str(e)}")
            raise


def generate_invoice_number(payment_id: str, created_at: str) -> str:
    """
    Generate unique invoice number
    
    Format: INV-YYYYMM-XXXXXX
    """
    try:
        date_obj = datetime.fromisoformat(created_at)
        date_part = date_obj.strftime('%Y%m')
    except:
        date_part = datetime.now().strftime('%Y%m')
    
    # Use last 6 chars of payment ID
    id_part = payment_id[-6:].upper() if len(payment_id) >= 6 else payment_id.upper()
    
    return f"INV-{date_part}-{id_part}"
