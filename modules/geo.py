import math
import folium
from streamlit_folium import st_folium

class GeoEngine:
    def __init__(self):
        self.lat_centro = -35.577493129233176
        self.lng_centro = -58.01362755722343

        self.coordenadas_sitios = {

            # ================================================
            # PATRIMONIO HISTÓRICO
            # ================================================

            # --- Casa de Casco y subdocumentos (Sarmiento y San Martín) ---
            "casa_de_casco.txt":               {"lat": -35.57860727800254, "lng": -58.01429481316557, "nombre": "Casa de Casco (Sarmiento y San Martín)", "tipo": "Historico"},
            "doc_13_casa_casco_chascomus.txt": {"lat": -35.57860727800254, "lng": -58.01429481316557, "nombre": "Casa de Casco (Historia Completa)", "tipo": "Historico"},
            "HIST_Casco_01_Origen.txt":        {"lat": -35.57860727800254, "lng": -58.01429481316557, "nombre": "Casa de Casco — Origen", "tipo": "Historico"},
            "HIST_Casco_02_Arquitectura.txt":  {"lat": -35.57860727800254, "lng": -58.01429481316557, "nombre": "Casa de Casco — Arquitectura", "tipo": "Historico"},
            "HIST_Casco_03_Museo_txt.txt":     {"lat": -35.57860727800254, "lng": -58.01429481316557, "nombre": "Casa de Casco — Museo Municipal", "tipo": "Historico"},
            "HIST_Casco_04_Leyenda.txt":       {"lat": -35.57860727800254, "lng": -58.01429481316557, "nombre": "Casa de Casco — Leyenda del Fantasma", "tipo": "Historico"},

            # --- Capilla de los Negros y subdocumentos ---
            "capilla_de_los_negros.txt":              {"lat": -35.582189815814246, "lng": -58.006696005773975, "nombre": "Capilla de los Negros (1862)", "tipo": "Historico"},
            "doc_10_capilla_negros_chascomus.txt":    {"lat": -35.582189815814246, "lng": -58.006696005773975, "nombre": "Capilla de los Negros — Historia", "tipo": "Historico"},
            "HIST_Capilla_01_Comunidad.txt":          {"lat": -35.582189815814246, "lng": -58.006696005773975, "nombre": "Capilla de los Negros — Comunidad", "tipo": "Historico"},
            "HIST_Capilla_02_Construccion.txt":       {"lat": -35.582189815814246, "lng": -58.006696005773975, "nombre": "Capilla de los Negros — Construcción", "tipo": "Historico"},
            "HIST_Capilla_03_Culto.txt":              {"lat": -35.582189815814246, "lng": -58.006696005773975, "nombre": "Capilla de los Negros — Culto y Rituales", "tipo": "Historico"},

            # --- Museo Pampeano y Parque Libres del Sur ---
            "museo_pampeano.txt":                        {"lat": -35.57794748656019, "lng": -58.017457136459484, "nombre": "Museo Pampeano", "tipo": "Historico"},
            "HIST_Museo_Pampeano_01.txt":                {"lat": -35.57794748656019, "lng": -58.017457136459484, "nombre": "Museo Pampeano — Colecciones", "tipo": "Historico"},
            "doc_11_que_hacer_chascomus_con_chicos.txt": {"lat": -35.57794748656019, "lng": -58.017457136459484, "nombre": "Museo Pampeano y Parque Libres del Sur", "tipo": "Historico"},

            # --- Palacio Municipal Salamone ---
            "municipalidad_salamone.txt":             {"lat": -35.57774888491685, "lng": -58.01376070577693, "nombre": "Palacio Municipal (Salamone)", "tipo": "Historico"},
            "URB_Municipalidad_01_Salamone.txt":      {"lat": -35.57774888491685, "lng": -58.01376070577693, "nombre": "Municipalidad — Obra de Salamone", "tipo": "Historico"},
            "doc_7_arquitectura_chascomus.txt":       {"lat": -35.57774888491685, "lng": -58.01376070577693, "nombre": "Arquitectura de Chascomús", "tipo": "Historico"},

            # --- Reloj de los Italianos ---
            "reloj_de_los_italianos.txt":             {"lat": -35.57683366875893, "lng": -58.01334754441206, "nombre": "Reloj de los Italianos (Lastra y Mitre)", "tipo": "Historico"},
            "doc_20_reloj_italianos_chascomus.txt":   {"lat": -35.57683366875893, "lng": -58.01334754441206, "nombre": "Reloj de los Italianos — Historia", "tipo": "Historico"},
            "HIST_Reloj_Italianos_01.txt":            {"lat": -35.57683366875893, "lng": -58.01334754441206, "nombre": "Reloj de los Italianos — Comunidad Italiana", "tipo": "Historico"},

            # --- Catedral Nuestra Señora de la Merced (Lavalle 281) ---
            "doc_18_catedral_chascomus.txt":          {"lat": -35.57898919181944, "lng": -58.013810682482784, "nombre": "Catedral Nuestra Señora de la Merced (Lavalle 281)", "tipo": "Historico"},
            "URB_Catedral_01_General.txt":            {"lat": -35.57898919181944, "lng": -58.013810682482784, "nombre": "Catedral — Historia General", "tipo": "Historico"},
            "URB_Catedral_02_Estilo.txt":             {"lat": -35.57898919181944, "lng": -58.013810682482784, "nombre": "Catedral — Estilo Arquitectónico", "tipo": "Historico"},

           # --- Plaza Independencia / Centro Cívico ---
            "doc_15_historia_chascomus.txt":          {"lat": -35.57851170202658, "lng": -58.01386559782448, "nombre": "Plaza Independencia — Historia de Chascomús", "tipo": "Historico"},
            "URB_Plaza_01_Historia.txt":              {"lat": -35.57851170202658, "lng": -58.01386559782448, "nombre": "Plaza Independencia — Diseño Colonial", "tipo": "Historico"},
            "doc_31_atractivos.txt":                  {"lat": -35.57851170202658, "lng": -58.01386559782448, "nombre": "Atractivos del Casco Histórico", "tipo": "Historico"},

            # --- Teatro Brazzola (Sarmiento 90) ---
            "doc_24_fiestas_tradicionales_chascomus.txt": {"lat": -35.57847110174371, "lng": -58.01465171316587, "nombre": "Teatro Brazzola — Fiestas y Cultura (Sarmiento 90)", "tipo": "Historico"},

            # --- Club de Pelota Paleta (Sarmiento y San Martín, offset norte) ---
            "doc_17_club_pelota_chascomus.txt":       {"lat": -35.57910087654957, "lng": -58.014289387737264, "nombre": "Club de Pelota Paleta (Sarmiento y San Martín)", "tipo": "Historico"},

            # --- Castillo de la Amistad (Av. Pedro Urruty) ---
            "doc_6_castillo_amistad_chascomus.txt":   {"lat": -35.55097676919556, "lng": -58.054543720776266, "nombre": "Castillo de la Amistad (Av. Pedro Urruty)", "tipo": "Historico"},

            # --- Casa de Alfonsín (Lavalle 227) ---
            "doc_9_alfonsin_chascomus.txt":           {"lat": -35.578362252754616, "lng": -58.01353794284365, "nombre": "Casa de Alfonsín (Lavalle 227)", "tipo": "Historico"},

            # --- Vieja Estación / Museo Ferroviario (Belgrano 300) ---
            "doc_28_vieja_estacion_chascomus.txt":    {"lat": -35.570685569072054, "lng": -58.01599598248836, "nombre": "Vieja Estación / Museo Ferroviario (Belgrano 300)", "tipo": "Historico"},
            "HIST_Vieja_Estacion_01.txt":             {"lat": -35.570685569072054, "lng": -58.01599598248836, "nombre": "Vieja Estación — Historia Ferroviaria", "tipo": "Historico"},

            # --- Estación Hidrobiológica (Av. Lastra y Juárez) ---
            "doc_14_estacion_hidrobiologica_chascomus.txt": {"lat": -35.57682012723176, "lng": -58.01770719043619, "nombre": "Estación Hidrobiológica (Av. Lastra y Juárez)", "tipo": "Historico"},
            "GEO_Laguna_02_Pejerrey.txt":             {"lat": -35.57682012723176, "lng": -58.01770719043619, "nombre": "Estación Hidrobiológica — Cría del Pejerrey", "tipo": "Historico"},

            # --- Torii de Chascomús (Costanera Sur) ---
            "doc_16_torii_chascomus.txt":             {"lat": -35.592676703297194, "lng": -57.98089152110877, "nombre": "Torii de Chascomús (Costanera Sur)", "tipo": "Historico"},

            # --- Espigón Domingo Cazaux ---
            "doc_29_espigon_chascomus_pesca_atardeceres.txt": {"lat": -35.58254612775905, "lng": -58.01908144293625, "nombre": "Espigón Domingo Cazaux (Pesca y Atardeceres)", "tipo": "Historico"},

            # --- Cementerio Protestante / Capilla San Andrés (5km por Av. Campaña del Desierto) ---
            "doc_26_cementerio_protestante_chascomus.txt": {"lat": -35.57855330887996, "lng": -57.96273193607241, "nombre": "Cementerio Protestante / Capilla San Andrés", "tipo": "Historico"},

           # --- Aeroclub (Paracaidismo y Vuelos, Ruta 20) ---
            "doc_5_aire_libre_diversion.txt":         {"lat": -35.536237227383204, "lng": -58.04691562339352, "nombre": "Aeroclub Chascomús (Paracaidismo y Vuelos)", "tipo": "Historico"},

            # --- Laguna (punto central geográfico) ---
            "doc_27_laguna_chascomus.txt":            {"lat": -35.58072045903063, "lng": -58.020780554775016, "nombre": "Laguna de Chascomús (3.044 ha)", "tipo": "Historico"},
            "GEO_Laguna_01_Datos.txt":                {"lat": -35.58072045903063, "lng": -58.020780554775016, "nombre": "Laguna — Datos Geográficos", "tipo": "Historico"},
            "NAT_Laguna_Ecologia_2026.txt":           {"lat": -35.58072045903063, "lng": -58.020780554775016, "nombre": "Laguna — Ecología y Cianobacterias 2026", "tipo": "Historico"},

            # --- Paseo de los Artesanos (Costanera) ---
            "doc_3_regionales.txt":                   {"lat": -35.58306702473038, "lng": -58.007590944065655, "nombre": "Paseo de los Artesanos y Comercios Regionales", "tipo": "Historico"},

            # --- Personajes contemporáneos → Centro Cultural Vieja Estación como referencia ---
            "HIST_Personajes_Contemporaneos.txt":     {"lat": -35.57100863528421, "lng": -58.015849575181676, "nombre": "Personajes Contemporáneos de Chascomús", "tipo": "Historico"},

            # ================================================
            # GASTRONOMÍA Y COMERCIAL
            # ================================================
            "franklin_47.txt":             {"lat": -35.57259723001434, "lng": -58.010604151804166, "nombre": "Franklin 47 Bar Cultural", "tipo": "Gastronomia"},
            "teofilo_bar.txt":             {"lat": -35.57448504664866, "lng": -58.014053440596484, "nombre": "Teófilo Bar (Libres del Sur 156)", "tipo": "Gastronomia"},
            "bach_patio.txt":              {"lat": -35.57092546306074, "lng": -58.00361643020003, "nombre": "Bach Patio Cervecero (Belbeze 153)", "tipo": "Gastronomia"},
            "olofsson_cerveceria.txt":     {"lat": -35.57815388826812, "lng": -58.00988059156062, "nombre": "Cervecería Olofsson (San Martín 140)", "tipo": "Gastronomia"},
            "cerveceria_haroldo.txt":      {"lat": -35.58198202201804, "lng": -58.01251350577424, "nombre": "Haroldo (Bartolomé Mitre 353)", "tipo": "Gastronomia"},
            "punta_norte.txt":             {"lat": -35.56849649251462, "lng": -58.02370635293211, "nombre": "Punta Norte (Costanera Alem y Escribano)", "tipo": "Gastronomia"},
            "bicho_raro.txt":              {"lat": -35.575332559968956, "lng": -58.013581659754486, "nombre": "Bicho Raro (Libres del Sur 82)", "tipo": "Gastronomia"},
            "bar_alsina.txt":              {"lat": -35.579670013222014, "lng": -58.012038005775764, "nombre": "Bar Alsina (Alsina 204)", "tipo": "Gastronomia"},
            "chancho_aurelio.txt":         {"lat": -35.5813854173409, "lng": -58.0079047750919, "nombre": "Chancho Aurelio (Av. Perón 355)", "tipo": "Gastronomia"},
            "cafe_club_social.txt":        {"lat": -35.57713518646701, "lng": -58.013559889751214, "nombre": "Café Club Social (Libres del Sur)", "tipo": "Gastronomia"},
            "33_beer_burger.txt":          {"lat": -35.58041436812814, "lng": -58.00830213731309, "nombre": "33 Beer & Burger (Pte. Perón 255)", "tipo": "Gastronomia"},
            "las_lomittas.txt":            {"lat": -35.58501645473256, "lng": -58.06613690634044, "nombre": "Las Lomittas (Barrio Lomas Altas)", "tipo": "Gastronomia"},
            "vieja_esquina.txt":           {"lat": -35.582661536450665, "lng": -58.00465770577394, "nombre": "Restaurante Vieja Esquina (Artigas y Costanera)", "tipo": "Gastronomia"},
            "macuco_bar.txt":              {"lat": -35.58368442311776, "lng": -58.00808528564382, "nombre": "Macuco Bar (Av. Costanera España 19)", "tipo": "Gastronomia"},
            "areca_multiespacio.txt":      {"lat": -35.576695198228165, "lng": -58.01342859043639, "nombre": "Areca Multiespacio (Libres del Sur 14)", "tipo": "Gastronomia"},
            "el_bodegon.txt":              {"lat": -35.5766171667788, "lng": -58.00933847453229, "nombre": "El Bodegón (Av. Lastra 446)", "tipo": "Gastronomia"},
            "cafe_mule.txt":               {"lat": -35.57966751634684, "lng": -58.01946645179981, "nombre": "Café Mulé (Av. Costanera España 4)", "tipo": "Gastronomia"},
            "la_toscana.txt":              {"lat": -35.578664485504014, "lng": -58.011106705776285, "nombre": "La Toscana (Lavalle 139)", "tipo": "Gastronomia"},
            "qva_parrilla.txt":            {"lat": -35.57732048591032, "lng": -58.01334014582103, "nombre": "Qva (Libres del Sur 87)", "tipo": "Gastronomia"},
            
            # --- Documentos del Corpus General (Fijados con alta resolución) ---
            "GAST_Guia_Comercial_Chascomus.txt":       {"lat": -35.57880000000000, "lng": -58.01320000000000, "nombre": "Guía Gastronómica General", "tipo": "Gastronomia"},
            "GAST_Oferta_Gastronomica_Detallada.txt":  {"lat": -35.57880000000000, "lng": -58.01320000000000, "nombre": "Oferta Gastronómica Detallada", "tipo": "Gastronomia"},
            "GAST_Ruta_del_Pejerrey_y_Cerveza.txt":    {"lat": -35.57840000000000, "lng": -58.01590000000000, "nombre": "Ruta del Pejerrey y Cerveza Artesanal", "tipo": "Gastronomia"},
            "doc_2_gastronomia.txt":                   {"lat": -35.57880000000000, "lng": -58.01320000000000, "nombre": "Gastronomía de Chascomús", "tipo": "Gastronomia"},
        }

    def _calcular_haversine(self, lat1, lon1, lat2, lon2):
        """Fórmula matemática tradicional para calcular la distancia entre dos coordenadas en Km."""
        R = 6371.0
        rad_lat1, rad_lon1 = math.radians(lat1), math.radians(lon1)
        rad_lat2, rad_lon2 = math.radians(lat2), math.radians(lon2)
        dlon = rad_lon2 - rad_lon1
        dlat = rad_lat2 - rad_lat1
        a = math.sin(dlat / 2)**2 + math.cos(rad_lat1) * math.cos(rad_lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def obtener_mas_cercano(self, lat_usuario, lng_usuario, tipo_filtro=None):
        """Compara la ubicación del usuario con el corpus y devuelve el punto más cercano."""
        sitio_cercano = None
        distancia_minima = float('inf')
        archivo_id_cercano = None
        vistos = set()  # Evita duplicar sitios con múltiples archivos en la misma coordenada

        for archivo, datos in self.coordenadas_sitios.items():
            if tipo_filtro and datos["tipo"] != tipo_filtro:
                continue
            coord_key = (datos["lat"], datos["lng"])
            if coord_key in vistos:
                continue
            vistos.add(coord_key)

            dist = self._calcular_haversine(lat_usuario, lng_usuario, datos["lat"], datos["lng"])
            if dist < distancia_minima:
                distancia_minima = dist
                sitio_cercano = datos
                archivo_id_cercano = archivo

        return archivo_id_cercano, sitio_cercano, distancia_minima

    def generar_mapa_sitio(self, nombre_archivo_id, entidades=None):
        """
        Genera un mapa centrado en un sitio específico de forma inteligente:
        Primero busca si alguna entidad NER machea con un punto específico,
        y si no, cae en el ID del documento como fallback.
        """
        clave_encontrada = None

        # 1. Estrategia de búsqueda por Entidades NER (Para máxima precisión)
        if entidades:
            for entidad in entidades:
                texto_entidad = entidad["texto"].lower()
                # Buscamos si el texto de la entidad está contenido en alguna de nuestras claves
                for clave, datos in self.coordenadas_sitios.items():
                    if texto_entidad in datos["nombre"].lower():
                        clave_encontrada = clave
                        break
                if clave_encontrada:
                    break

        # 2. Estrategia Fallback: Si no hay entidades válidas, usamos el ID del documento
        if not clave_encontrada and nombre_archivo_id in self.coordenadas_sitios:
            clave_encontrada = nombre_archivo_id

        # 3. Renderizado del mapa con la clave seleccionada
        if clave_encontrada:
            datos = self.coordenadas_sitios[clave_encontrada]
            mapa = folium.Map(location=[datos["lat"], datos["lng"]], zoom_start=16, control_scale=True)
            
            color = "blue" if datos["tipo"] == "Historico" else "green"
            icono = "info-sign" if datos["tipo"] == "Historico" else "cutlery"
            
            folium.Marker(
                location=[datos["lat"], datos["lng"]],
                popup=f"<b>{datos['nombre']}</b><br>Categoría: {datos['tipo']}",
                tooltip=datos["nombre"],
                icon=folium.Icon(color=color, icon=icono)
            ).add_to(mapa)
            
            return mapa
            
        return None

    def generar_mapa_general(self):
        """Genera el mapa completo con todos los puntos del corpus, sin duplicar coordenadas."""
        mapa_global = folium.Map(location=[self.lat_centro, self.lng_centro], zoom_start=14)
        coordenadas_ya_dibujadas = set()

        for archivo, datos in self.coordenadas_sitios.items():
            coord_key = (datos["lat"], datos["lng"])
            if coord_key in coordenadas_ya_dibujadas:
                continue
            coordenadas_ya_dibujadas.add(coord_key)

            color = "blue" if datos["tipo"] == "Historico" else "green"
            icono = "info-sign" if datos["tipo"] == "Historico" else "cutlery"

            folium.Marker(
                location=[datos["lat"], datos["lng"]],
                popup=f"<b>{datos['nombre']}</b>",
                tooltip=datos["nombre"],
                icon=folium.Icon(color=color, icon=icono)
            ).add_to(mapa_global)

        # Leyenda visual en el mapa
        leyenda_html = """
        <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                    background-color: white; padding: 10px 14px; border-radius: 8px;
                    border: 2px solid #ccc; font-size: 13px; font-family: Arial;">
            <b>Referencias</b><br>
            <span style="color:#2A7AE2">&#9679;</span> Patrimonio Histórico<br>
            <span style="color:#2ECC40">&#9679;</span> Gastronomía
        </div>
        """
        mapa_global.get_root().html.add_child(folium.Element(leyenda_html))

        return mapa_global

    def obtener_estadisticas_cobertura(self):
        """Devuelve métricas de cobertura geográfica del corpus para el Dashboard."""
        historicos = [d for d in self.coordenadas_sitios.values() if d["tipo"] == "Historico"]
        gastronomicos = [d for d in self.coordenadas_sitios.values() if d["tipo"] == "Gastronomia"]
        total_coords_unicas = len({(d["lat"], d["lng"]) for d in self.coordenadas_sitios.values()})

        return {
            "total_entradas": len(self.coordenadas_sitios),
            "coords_unicas": total_coords_unicas,
            "historicos": len(set((d["lat"], d["lng"]) for d in historicos)),
            "gastronomicos": len(set((d["lat"], d["lng"]) for d in gastronomicos)),
        }