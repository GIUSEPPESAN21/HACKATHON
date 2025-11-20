"""
Sistema de alertas personalizadas para monitoreo de riesgos
"""
import pandas as pd
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class AlertSystem:
    def __init__(self):
        """Inicializa el sistema de alertas"""
        self.alerts = []
        self.alert_rules = self._default_alert_rules()
    
    def _default_alert_rules(self):
        """Define reglas de alertas por defecto"""
        return {
            'high_negative_ratio': {
                'name': 'Alta proporción de noticias negativas',
                'threshold': 0.4,  # 40%
                'severity': 'critical',
                'enabled': True
            },
            'critical_keywords': {
                'name': 'Palabras clave críticas detectadas',
                'keywords': ['sequía', 'plaga', 'crisis', 'pérdida', 'conflicto', 'paro', 'bloqueo'],
                'severity': 'high',
                'enabled': True
            },
            'low_positive_trend': {
                'name': 'Tendencia negativa persistente',
                'threshold': 0.15,  # Menos de 15% positivas
                'severity': 'medium',
                'enabled': True
            },
            'geographic_concentration': {
                'name': 'Concentración de noticias negativas en una zona',
                'threshold': 3,  # 3 o más noticias negativas de la misma ubicación
                'severity': 'high',
                'enabled': True
            }
        }
    
    def analyze_and_generate_alerts(self, df):
        """
        Analiza datos y genera alertas según reglas configuradas
        
        Args:
            df: DataFrame con noticias analizadas
        
        Returns:
            Lista de alertas generadas
        """
        self.alerts = []
        
        if df is None or len(df) == 0:
            return self.alerts
        
        # Regla 1: Alta proporción de noticias negativas
        if self.alert_rules['high_negative_ratio']['enabled']:
            self._check_negative_ratio(df)
        
        # Regla 2: Palabras clave críticas
        if self.alert_rules['critical_keywords']['enabled']:
            self._check_critical_keywords(df)
        
        # Regla 3: Baja tendencia positiva
        if self.alert_rules['low_positive_trend']['enabled']:
            self._check_positive_trend(df)
        
        # Regla 4: Concentración geográfica
        if self.alert_rules['geographic_concentration']['enabled']:
            self._check_geographic_concentration(df)
        
        # Ordenar por severidad
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        self.alerts.sort(key=lambda x: severity_order.get(x['severity'], 3))
        
        return self.alerts
    
    def _check_negative_ratio(self, df):
        """Verifica proporción de noticias negativas"""
        total = len(df)
        negativas = len(df[df['sentimiento_ia'] == 'Negativo'])
        ratio = negativas / total if total > 0 else 0
        
        threshold = self.alert_rules['high_negative_ratio']['threshold']
        
        if ratio >= threshold:
            self.alerts.append({
                'type': 'high_negative_ratio',
                'severity': 'critical',
                'title': '🚨 ALERTA CRÍTICA: Alta Concentración de Noticias Negativas',
                'message': f'Se detectó que {ratio*100:.1f}% ({negativas}/{total}) de las noticias son negativas, superando el umbral del {threshold*100:.0f}%.',
                'recommendation': 'Revisar inmediatamente las noticias negativas para identificar amenazas críticas al sector.',
                'timestamp': datetime.now().isoformat()
            })
    
    def _check_critical_keywords(self, df):
        """Detecta palabras clave críticas"""
        keywords = self.alert_rules['critical_keywords']['keywords']
        detected_keywords = {}
        
        for index, row in df.iterrows():
            if row.get('sentimiento_ia') == 'Negativo':
                text_full = f"{row.get('titular', '')} {row.get('cuerpo', '')}".lower()
                
                for keyword in keywords:
                    if keyword in text_full:
                        if keyword not in detected_keywords:
                            detected_keywords[keyword] = []
                        detected_keywords[keyword].append(row.get('titular', 'Sin titular'))
        
        if detected_keywords:
            keywords_str = ', '.join([f"'{k}' ({len(v)} veces)" for k, v in detected_keywords.items()])
            
            self.alerts.append({
                'type': 'critical_keywords',
                'severity': 'high',
                'title': '⚠️ ALERTA: Palabras Clave Críticas Detectadas',
                'message': f'Se encontraron menciones de: {keywords_str}',
                'recommendation': 'Evaluar impacto potencial de estos eventos en las operaciones.',
                'details': detected_keywords,
                'timestamp': datetime.now().isoformat()
            })
    
    def _check_positive_trend(self, df):
        """Verifica tendencia de noticias positivas"""
        total = len(df)
        positivas = len(df[df['sentimiento_ia'] == 'Positivo'])
        ratio = positivas / total if total > 0 else 0
        
        threshold = self.alert_rules['low_positive_trend']['threshold']
        
        if ratio < threshold:
            self.alerts.append({
                'type': 'low_positive_trend',
                'severity': 'medium',
                'title': '📉 ALERTA: Baja Proporción de Noticias Positivas',
                'message': f'Solo {ratio*100:.1f}% ({positivas}/{total}) de las noticias son positivas, por debajo del {threshold*100:.0f}%.',
                'recommendation': 'Considerar estrategias para identificar y aprovechar oportunidades en el sector.',
                'timestamp': datetime.now().isoformat()
            })
    
    def _check_geographic_concentration(self, df):
        """Detecta concentración de noticias negativas por ubicación"""
        try:
            from src.geo_mapper import NewsGeoMapper
            mapper = NewsGeoMapper()
            
            location_negatives = {}
            
            for index, row in df.iterrows():
                if row.get('sentimiento_ia') == 'Negativo':
                    text_full = f"{row.get('titular', '')} {row.get('cuerpo', '')}"
                    locations = mapper.extract_locations_from_text(text_full)
                    
                    for loc in locations:
                        if loc not in location_negatives:
                            location_negatives[loc] = []
                        location_negatives[loc].append(row.get('titular', 'Sin titular'))
            
            # Filtrar ubicaciones con múltiples noticias negativas
            threshold = self.alert_rules['geographic_concentration']['threshold']
            hot_spots = {k: v for k, v in location_negatives.items() if len(v) >= threshold}
            
            if hot_spots:
                hot_spots_str = ', '.join([f"{k} ({len(v)} noticias)" for k, v in hot_spots.items()])
                
                self.alerts.append({
                    'type': 'geographic_concentration',
                    'severity': 'high',
                    'title': '📍 ALERTA: Zona de Riesgo Concentrado',
                    'message': f'Múltiples noticias negativas detectadas en: {hot_spots_str}',
                    'recommendation': 'Investigar situación específica en estas zonas y considerar medidas preventivas.',
                    'details': hot_spots,
                    'timestamp': datetime.now().isoformat()
                })
        except Exception as e:
            logger.warning(f"No se pudo verificar concentración geográfica: {e}")
    
    def get_alert_summary(self):
        """Genera resumen de alertas"""
        if not self.alerts:
            return "✅ No se detectaron alertas. El análisis no muestra riesgos significativos."
        
        critical = sum(1 for a in self.alerts if a['severity'] == 'critical')
        high = sum(1 for a in self.alerts if a['severity'] == 'high')
        medium = sum(1 for a in self.alerts if a['severity'] == 'medium')
        
        summary = f"🔔 **{len(self.alerts)} Alertas Generadas**\n\n"
        summary += f"- 🚨 Críticas: {critical}\n"
        summary += f"- ⚠️ Altas: {high}\n"
        summary += f"- ⚡ Medias: {medium}\n"
        
        return summary
    
    def export_alerts_json(self, filename="alertas.json"):
        """Exporta alertas a JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.alerts, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Alertas exportadas a {filename}")

