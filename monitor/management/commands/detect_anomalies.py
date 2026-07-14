import os
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils.html import strip_tags
# Import your model here (e.g., from monitor.models import CostSnapshot)

class Command(BaseCommand):
    help = 'Scans database entries, flags spending anomalies, and sends an enterprise HTML alert.'

    def handle(self, *args, **options) -> None:
        # Fetch your actual anomalies from the database to loop through them dynamically
        # anomalies_list = CostSnapshot.objects.filter(is_anomaly=True).order_by('-date')
        # flagged_count = anomalies_list.count()
        
        # Using 10 to match your current data snapshot for this template example:
        flagged_count = 10 
        
        if flagged_count > 0:
            self.stdout.write("Generating enterprise HTML alert email...")
            
            subject = f"🚨 CRITICAL ALERT: {flagged_count} Cloud Cost Anomalies Flagged"
            
            # 1. Build out the HTML rows dynamically from your database anomalies
            table_rows = ""
            
            # Sample mock data mapping your exact screenshot if needed, 
            # but in production you will loop: for item in anomalies_list:
            mock_anomalies = [
                {"date": "2026-07-11", "service": "EC2", "cost": 169.12},
                {"date": "2026-07-10", "service": "RDS", "cost": 124.16},
                {"date": "2026-07-08", "service": "RDS", "cost": 89.26},
                {"date": "2026-07-04", "service": "S3", "cost": 25.03},
            ]
            
            for item in mock_anomalies:
                table_rows += f"""
                <tr style="border-bottom: 1px solid #2d3748;">
                    <td style="padding: 12px; color: #cbd5e0;">{item['date']}</td>
                    <td style="padding: 12px; color: #cbd5e0; font-weight: bold;">{item['service']}</td>
                    <td style="padding: 12px; color: #f6ad55; text-align: right; font-weight: bold;">${item['cost']:.2f}</td>
                </tr>
                """

            # 2. Complete Premium Dark-Themed HTML Structure
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f141c; margin: 0; padding: 20px; color: #e2e8f0;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #1a202c; border-radius: 8px; border: 1px solid #2d3748; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
                    
                    <div style="background: linear-gradient(135deg, #e53e3e 0%, #b7791f 100%); padding: 24px; text-align: center;">
                        <h1 style="margin: 0; color: #ffffff; font-size: 22px; letter-spacing: 1px;">CLOUDGUARD FINOPS</h1>
                        <p style="margin: 5px 0 0 0; color: #feebc8; font-size: 14px;">Automated Anomaly Detection Engine</p>
                    </div>
                    
                    <div style="padding: 24px;">
                        <p style="font-size: 16px; line-height: 1.5; color: #e2e8f0;">
                            Hello Administrator,
                        </p>
                        <p style="font-size: 15px; line-height: 1.5; color: #a0aec0;">
                            The background scraper execution has completed. The cost optimization engine isolated <span style="color: #e53e3e; font-weight: bold;">{flagged_count} cost spikes</span> that exceed regular budget baselines.
                        </p>
                        
                        <h3 style="color: #ed8936; margin-top: 24px; border-bottom: 1px solid #4a5568; padding-bottom: 8px;">Flagged Resource Violations</h3>
                        <table style="width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px;">
                            <thead>
                                <tr style="background-color: #2d3748; text-align: left;">
                                    <th style="padding: 12px; color: #a0aec0;">Date</th>
                                    <th style="padding: 12px; color: #a0aec0;">Service</th>
                                    <th style="padding: 12px; color: #a0aec0; text-align: right;">Cost Incurred</th>
                                </tr>
                            </thead>
                            <tbody>
                                {table_rows}
                            </tbody>
                        </table>
                        
                        <div style="text-align: center; margin-top: 35px; margin-bottom: 20px;">
                            <a href="http://127.0.0.1:8000/" style="background-color: #3182ce; color: #ffffff; padding: 12px 28px; text-decoration: none; font-weight: bold; border-radius: 4px; display: inline-block; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                                View Executive Dashboard
                            </a>
                        </div>
                    </div>
                    
                    <div style="background-color: #171923; padding: 16px; text-align: center; font-size: 12px; color: #718096; border-top: 1px solid #2d3748;">
                        Secure Cloud Infrastructure Automated Control System<br>
                        Report Generated Automatically via Django-Crontab Engine
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 3. Standard text fallback for legacy email clients
            text_content = strip_tags(html_message)
            
            sender_email = os.getenv('EMAIL_HOST_USER')
            
            try:
                send_mail(
                    subject=subject,
                    message=text_content, # Fallback
                    from_email=sender_email,
                    recipient_list=[sender_email],
                    html_message=html_message, # Main pretty version
                    fail_silently=False,
                )
                self.stdout.write(self.style.SUCCESS("📩 Premium HTML Alert dispatched successfully!"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Transmission Error: {str(e)}"))