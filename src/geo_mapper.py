"""
Sistema de mapeo geográfico para visualizar ubicación de noticias
Utiliza Folium para mapas interactivos y Geopy para geocodificación
"""
import folium
from folium import plugins
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import logging
import re

logger = logging.getLogger(__name__)

class NewsGeoMapper:
    def __init__(self):
        """Inicializa el mapeador con geocodificador"""
        self.geolocator = Nominatim(user_agent="sava_agro_insight")
        
        # Caché de ubicaciones para evitar múltiples consultas
        self.location_cache = {
            # Principales ciudades del Valle del Cauca
            "cali": (3.4516, -76.5320),
            "palmira": (3.5394, -76.3036),
            "buenaventura": (3.8801, -77.0314),
            "tulua": (4.0840, -76.1952),
            "cartago": (4.7467, -75.9114),
            "buga": (3.9000, -76.3000),
            "jamundi": (3.2644, -76.5411),
            "yumbo": (3.5883, -76.4986),
            "valle del cauca": (3.8008, -76.6413),
            "colombia": (4.5709, -74.2973)
        }
    
    def extract_locations_from_text(self, text):
        """
        Extrae posibles ubicaciones del texto de la noticia
        
        Args:
            text: Texto de la noticia
        
        Returns:
            Lista de ubicaciones detectadas
        """
        text_lower = text.lower()
        detected_locations = []
        
        # Buscar ciudades conocidas del Valle del Cauca
        cities = [
            "Cali", "Palmira", "Buenaventura", "Tuluá", "Cartago", "Buga",
            "Jamundí", "Yumbo", "Candelaria", "Florida", "Pradera", 
            "Ginebra", "Guacarí", "Sevilla", "Dagua", "La Cumbre"
        ]
        
        for city in cities:
            if city.lower() in text_lower:
                detected_locations.append(city)
        
        # Buscar "Valle del Cauca"
        if "valle del cauca" in text_lower or "valle" in text_lower:
            detected_locations.append("Valle del Cauca")
        
        return list(set(detected_locations))  # Eliminar duplicados
    
    def geocode_location(self, location_name):
        """
        Obtiene coordenadas de una ubicación
        
        Args:
            location_name: Nombre de la ubicación
        
        Returns:
            Tupla (lat, lon) o None si no se encuentra
        """
        location_lower = location_name.lower().strip()
        
        # Verificar caché primero
        if location_lower in self.location_cache:
            return self.location_cache[location_lower]
        
        # Intentar geocodificar
        try:
            # Agregar "Colombia" al final para mejorar precisión
            search_query = f"{location_name}, Valle del Cauca, Colombia"
            location = self.geolocator.geocode(search_query, timeout=5)
            
            if location:
                coords = (location.latitude, location.longitude)
                self.location_cache[location_lower] = coords
                return coords
            else:
                logger.warning(f"No se pudo geocodificar: {location_name}")
                return None
                
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Error de geocodificación: {e}")
            return None
    
    def create_news_map(self, df, center_coords=(3.8008, -76.6413), zoom_start=8):
        """
        Crea mapa interactivo con noticias geolocalizadas
        
        Args:
            df: DataFrame con noticias (debe tener 'titular', 'sentimiento_ia', etc.)
            center_coords: Coordenadas del centro del mapa (default: Valle del Cauca)
            zoom_start: Nivel de zoom inicial
        
        Returns:
            Objeto folium.Map
        """
        # Crear mapa base
        m = folium.Map(
            location=center_coords,
            zoom_start=zoom_start,
            tiles="OpenStreetMap",
            control_scale=True
        )
        
        # Agregar control de capas - CORREGIDO: Stamen Terrain deprecado
        # Usar OpenTopoMap en lugar de Stamen Terrain
        folium.TileLayer('OpenTopoMap', name='Terreno', attr='OpenTopoMap').add_to(m)
        folium.TileLayer('CartoDB positron', name='Limpio', attr='CartoDB').add_to(m)
        
        # Grupos de marcadores por sentimiento
        cluster_positivo = plugins.MarkerCluster(name="Noticias Positivas").add_to(m)
        cluster_negativo = plugins.MarkerCluster(name="Noticias Negativas").add_to(m)
        cluster_neutro = plugins.MarkerCluster(name="Noticias Neutras").add_to(m)
        
        # Contadores
        geolocalized = 0
        not_geolocalized = 0
        
        # Procesar cada noticia
        for index, row in df.iterrows():
            titular = str(row.get('titular', 'Sin Titular'))
            sentimiento = row.get('sentimiento_ia', 'Neutro')
            explicacion = row.get('explicacion_ia', 'Sin explicación')
            fecha = row.get('fecha', 'Sin fecha')
            
            # Extraer ubicaciones del texto
            text_full = f"{titular} {row.get('cuerpo', '')}"
            locations = self.extract_locations_from_text(text_full)
            
            if not locations:
                # Si no hay ubicaciones específicas, usar Valle del Cauca genérico
                locations = ["Valle del Cauca"]
            
            # Geocodificar primera ubicación detectada
            coords = self.geocode_location(locations[0])
            
            if coords:
                geolocalized += 1
                
                # Definir color según sentimiento
                if sentimiento == "Positivo":
                    color = "green"
                    icon = "arrow-up"
                    cluster = cluster_positivo
                elif sentimiento == "Negativo":
                    color = "red"
                    icon = "arrow-down"
                    cluster = cluster_negativo
                else:
                    color = "gray"
                    icon = "info-sign"
                    cluster = cluster_neutro
                
                # Crear popup con información
                popup_html = f"""
                <div style="width: 300px;">
                    <h4 style="color: {color};">{sentimiento}</h4>
                    <p><b>{titular}</b></p>
                    <p><i>{explicacion[:150]}...</i></p>
                    <hr>
                    <small>📍 {locations[0]}<br>📅 {fecha}</small>
                </div>
                """
                
                # Agregar marcador
                folium.Marker(
                    location=coords,
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"{sentimiento}: {titular[:50]}...",
                    icon=folium.Icon(color=color, icon=icon, prefix='glyphicon')
                ).add_to(cluster)
                
                time.sleep(0.1)  # Pequeña pausa para evitar rate limiting
            else:
                not_geolocalized += 1
        
        # Agregar control de capas
        folium.LayerControl().add_to(m)
        
        # Agregar mini mapa
        minimap = plugins.MiniMap(toggle_display=True)
        m.add_child(minimap)
        
        # Agregar botón de pantalla completa
        plugins.Fullscreen().add_to(m)
        
        logger.info(f"📍 Mapa creado: {geolocalized} noticias geolocalizadas, {not_geolocalized} sin ubicación específica")
        
        return m
    
    def create_heatmap(self, df):
        """
        Crea mapa de calor basado en intensidad de noticias negativas
        
        Args:
            df: DataFrame con noticias
        
        Returns:
            Objeto folium.Map con heatmap
        """
        m = folium.Map(
            location=(3.8008, -76.6413),
            zoom_start=8,
            tiles="CartoDB dark_matter"
        )
        
        heat_data = []
        negativas_count = 0
        
        for index, row in df.iterrows():
            if row.get('sentimiento_ia') == 'Negativo':
                negativas_count += 1
                text_full = f"{row.get('titular', '')} {row.get('cuerpo', '')}"
                locations = self.extract_locations_from_text(text_full)
                
                if locations:
                    coords = self.geocode_location(locations[0])
                    if coords:
                        # Peso mayor para noticias negativas
                        heat_data.append([coords[0], coords[1], 1.0])
                    time.sleep(0.05)  # Reducido para ser más rápido
        
        if heat_data:
            # MEJORADO: Configuración más visible del heatmap
            plugins.HeatMap(
                heat_data, 
                radius=30,  # Aumentado para mejor visibilidad
                blur=40,    # Aumentado para mejor difusión
                max_zoom=13,
                min_opacity=0.3,  # Más visible
                gradient={0.2: 'blue', 0.4: 'cyan', 0.6: 'lime', 0.8: 'yellow', 1.0: 'red'}  # Gradiente de colores
            ).add_to(m)
            
            # Agregar marcador informativo
            folium.Marker(
                location=(3.8008, -76.6413),
                popup=f"Mapa de Calor de Riesgos<br>Noticias Negativas: {negativas_count}<br>Puntos geolocalizados: {len(heat_data)}",
                icon=folium.Icon(color='red', icon='info-sign', prefix='glyphicon')
            ).add_to(m)
        else:
            # Si no hay datos, agregar marcador informativo
            folium.Marker(
                location=(3.8008, -76.6413),
                popup="No hay noticias negativas geolocalizadas para mostrar en el mapa de calor",
                icon=folium.Icon(color='gray', icon='info-sign', prefix='glyphicon')
            ).add_to(m)
        
        logger.info(f"🔥 Mapa de calor: {len(heat_data)} puntos de {negativas_count} noticias negativas")
        
        return m

