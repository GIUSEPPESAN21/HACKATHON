"""
Sistema de exportación avanzada de reportes
Genera PDFs y Excel con gráficos profesionales
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
import pandas as pd
import io
from datetime import datetime
import xlsxwriter
import logging

logger = logging.getLogger(__name__)

class ReportExporter:
    def __init__(self):
        """Inicializa el exportador de reportes"""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Crea estilos personalizados para el PDF"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2ecc71'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#27ae60'),
            spaceAfter=12,
            spaceBefore=12
        ))
    
    def export_to_pdf(self, df, filename="reporte_sava.pdf", include_stats=True):
        """
        Exporta análisis a PDF profesional
        
        Args:
            df: DataFrame con noticias analizadas
            filename: Nombre del archivo PDF
            include_stats: Si True, incluye estadísticas y gráficos
        
        Returns:
            BytesIO object con el PDF
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        # Contenedor de elementos
        elements = []
        
        # Título
        title = Paragraph("📊 Reporte de Análisis de Sentimiento", self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Información general
        fecha_reporte = datetime.now().strftime("%d de %B de %Y - %H:%M")
        info = Paragraph(f"<b>Fecha del Reporte:</b> {fecha_reporte}<br/>"
                        f"<b>Total de Noticias:</b> {len(df)}<br/>"
                        f"<b>Generado por:</b> SAVA Software - Agro Insight",
                        self.styles['Normal'])
        elements.append(info)
        elements.append(Spacer(1, 20))
        
        # Estadísticas
        if include_stats:
            elements.append(Paragraph("Distribución de Sentimientos", self.styles['SectionTitle']))
            
            total = len(df)
            pos = len(df[df['sentimiento_ia'] == 'Positivo'])
            neg = len(df[df['sentimiento_ia'] == 'Negativo'])
            neu = len(df[df['sentimiento_ia'] == 'Neutro'])
            
            stats_data = [
                ['Sentimiento', 'Cantidad', 'Porcentaje'],
                ['Positivo', str(pos), f'{pos/total*100:.1f}%'],
                ['Negativo', str(neg), f'{neg/total*100:.1f}%'],
                ['Neutro', str(neu), f'{neu/total*100:.1f}%'],
                ['TOTAL', str(total), '100%']
            ]
            
            stats_table = Table(stats_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d5f4e6')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(stats_table)
            elements.append(Spacer(1, 20))
        
        # Noticias detalladas
        elements.append(PageBreak())
        elements.append(Paragraph("Detalle de Noticias Analizadas", self.styles['SectionTitle']))
        elements.append(Spacer(1, 12))
        
        for index, row in df.head(20).iterrows():  # Primeras 20 noticias
            sentimiento = row.get('sentimiento_ia', 'Neutro')
            
            # Color según sentimiento
            if sentimiento == 'Positivo':
                color = colors.HexColor('#2ecc71')
                emoji = '🟢'
            elif sentimiento == 'Negativo':
                color = colors.HexColor('#e74c3c')
                emoji = '🔴'
            else:
                color = colors.HexColor('#95a5a6')
                emoji = '⚪'
            
            # Titular
            titular_text = f"<b>{emoji} {row.get('titular', 'Sin titular')}</b>"
            titular_para = Paragraph(titular_text, self.styles['Heading3'])
            elements.append(titular_para)
            
            # Detalles
            detalles = f"""<font color='{color.hexval()}'>Sentimiento: {sentimiento}</font><br/>
            <b>Análisis:</b> {row.get('explicacion_ia', 'N/A')[:200]}...<br/>
            <b>Fecha:</b> {row.get('fecha', 'N/A')}"""
            
            detalles_para = Paragraph(detalles, self.styles['Normal'])
            elements.append(detalles_para)
            elements.append(Spacer(1, 15))
        
        # Construir PDF
        doc.build(elements)
        
        buffer.seek(0)
        logger.info(f"✅ PDF generado exitosamente: {filename}")
        return buffer
    
    def export_to_excel(self, df, filename="reporte_sava.xlsx", include_charts=True):
        """
        Exporta análisis a Excel con formato profesional y gráficos
        
        Args:
            df: DataFrame con noticias analizadas
            filename: Nombre del archivo Excel
            include_charts: Si True, incluye gráficos
        
        Returns:
            BytesIO object con el Excel
        """
        buffer = io.BytesIO()
        
        # Crear Excel writer
        writer = pd.ExcelWriter(buffer, engine='xlsxwriter')
        workbook = writer.book
        
        # Formatos
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#2ecc71',
            'font_color': 'white',
            'border': 1
        })
        
        positive_format = workbook.add_format({'bg_color': '#d5f4e6'})
        negative_format = workbook.add_format({'bg_color': '#fadbd8'})
        neutral_format = workbook.add_format({'bg_color': '#f2f3f4'})
        
        # Hoja 1: Datos completos
        df.to_excel(writer, sheet_name='Análisis Completo', index=False)
        worksheet_data = writer.sheets['Análisis Completo']
        
        # Aplicar formato a encabezados
        for col_num, value in enumerate(df.columns.values):
            worksheet_data.write(0, col_num, value, header_format)
        
        # Aplicar formato condicional a sentimientos
        for row_num in range(1, len(df) + 1):
            sentimiento = df.iloc[row_num - 1]['sentimiento_ia']
            if sentimiento == 'Positivo':
                worksheet_data.set_row(row_num, None, positive_format)
            elif sentimiento == 'Negativo':
                worksheet_data.set_row(row_num, None, negative_format)
            else:
                worksheet_data.set_row(row_num, None, neutral_format)
        
        # Ajustar anchos de columna
        worksheet_data.set_column('A:A', 50)  # Titular
        worksheet_data.set_column('B:B', 15)  # Fecha
        worksheet_data.set_column('C:C', 15)  # Sentimiento
        worksheet_data.set_column('D:D', 40)  # Explicación
        
        # Hoja 2: Resumen estadístico
        stats_df = df['sentimiento_ia'].value_counts().reset_index()
        stats_df.columns = ['Sentimiento', 'Cantidad']
        stats_df['Porcentaje'] = (stats_df['Cantidad'] / len(df) * 100).round(1)
        
        stats_df.to_excel(writer, sheet_name='Estadísticas', index=False, startrow=1)
        worksheet_stats = writer.sheets['Estadísticas']
        
        # Título de estadísticas
        title_format = workbook.add_format({'bold': True, 'font_size': 14, 'fg_color': '#2ecc71', 'font_color': 'white'})
        worksheet_stats.write('A1', 'Resumen Estadístico de Sentimientos', title_format)
        
        # Gráfico de torta
        if include_charts:
            chart = workbook.add_chart({'type': 'pie'})
            chart.add_series({
                'name': 'Distribución de Sentimientos',
                'categories': ['Estadísticas', 2, 0, 2 + len(stats_df) - 1, 0],
                'values': ['Estadísticas', 2, 1, 2 + len(stats_df) - 1, 1],
                'data_labels': {'percentage': True},
                'points': [
                    {'fill': {'color': '#2ecc71'}},  # Positivo
                    {'fill': {'color': '#e74c3c'}},  # Negativo
                    {'fill': {'color': '#95a5a6'}},  # Neutro
                ],
            })
            
            chart.set_title({'name': 'Distribución de Sentimientos'})
            chart.set_style(10)
            
            worksheet_stats.insert_chart('E2', chart, {'x_scale': 1.5, 'y_scale': 1.5})
        
        # Hoja 3: Palabras clave (Top 10)
        try:
            from collections import Counter
            import re
            
            all_words = []
            stopwords = set(['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se', 'no'])
            
            for text in df['titular'].fillna(''):
                words = re.findall(r'\b[a-záéíóúñ]{4,}\b', text.lower())
                all_words.extend([w for w in words if w not in stopwords])
            
            keywords_df = pd.DataFrame(Counter(all_words).most_common(15), columns=['Palabra', 'Frecuencia'])
            keywords_df.to_excel(writer, sheet_name='Palabras Clave', index=False)
            
            worksheet_keywords = writer.sheets['Palabras Clave']
            
            # Gráfico de barras
            if include_charts:
                chart_bar = workbook.add_chart({'type': 'column'})
                chart_bar.add_series({
                    'name': 'Frecuencia',
                    'categories': ['Palabras Clave', 1, 0, 15, 0],
                    'values': ['Palabras Clave', 1, 1, 15, 1],
                    'fill': {'color': '#3498db'},
                })
                
                chart_bar.set_title({'name': 'Top 15 Palabras Más Frecuentes'})
                chart_bar.set_x_axis({'name': 'Palabra'})
                chart_bar.set_y_axis({'name': 'Frecuencia'})
                
                worksheet_keywords.insert_chart('D2', chart_bar, {'x_scale': 1.8, 'y_scale': 1.5})
        except Exception as e:
            logger.warning(f"No se pudieron generar palabras clave: {e}")
        
        # Cerrar writer
        writer.close()
        
        buffer.seek(0)
        logger.info(f"✅ Excel generado exitosamente: {filename}")
        return buffer

