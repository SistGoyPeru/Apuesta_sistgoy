
import requests
from bs4 import BeautifulSoup
import polars as pl

class CalendarioLiga:
    def __init__(self, url="https://www.livefutbol.com/competition/co97/espana-primera-division/all-matches/"):
        self.url = url
        self.data = []

    def extraer_calendario(self):
        response = requests.get(self.url)
        if response.status_code != 200:
            print(f"Error al acceder a la URL: {response.status_code}")
            return pl.DataFrame()
        soup = BeautifulSoup(response.content, 'html.parser')
        gameplan = soup.find('div', class_='module-gameplan')
        if not gameplan:
            print("No se encontró el bloque de partidos (module-gameplan)")
            return pl.DataFrame()
        jornada = None
        fecha = None
        for child in gameplan.find_all('div'):
            classes = child.get('class', [])
            if 'round-head' in classes:
                jornada = child.get_text(strip=True)
            elif 'date-head' in classes:
                fecha = child.get_text(strip=True)
            elif 'match' in classes:
                local = child.find('div', class_='team-name-home')
                visita = child.find('div', class_='team-name-away')
                hora = child.find('div', class_='match-time')
                marcador = child.find('div', class_='match-result')
                resultado = marcador.get_text(strip=True) if marcador else ''
                # Separar goles si el marcador es válido
                if resultado and ':' in resultado and resultado != '-:-':
                    try:
                        ga, gv = [int(x) for x in resultado.split(':')]
                    except Exception:
                        ga, gv = None, None
                else:
                    ga, gv = None, None
                self.data.append({
                    "Jornada": jornada,
                    "Fecha": fecha,
                    "Hora": hora.get_text(strip=True) if hora else '',
                    "Local": local.get_text(strip=True) if local else '',
                    "Visita": visita.get_text(strip=True) if visita else '',
                    "Resultado": resultado,
                    "GA": ga,
                    "GV": gv
                })
        df = pl.DataFrame(self.data)
        # Convertir la columna 'Fecha' a tipo fecha (pl.Date)
        if 'Fecha' in df.columns:
            df = df.with_columns([
                pl.col('Fecha').str.strptime(pl.Date, "%d.%m.%Y", strict=False).alias('Fecha')
            ])
        if 'Jornada' in df.columns:
            # Extraer solo el número de jornada y convertir a entero
            df = df.with_columns([
                pl.col('Jornada').str.extract(r'(\d+)', 1).cast(pl.Int32).alias('Jornada')
            ])
        # Eliminar la columna 'Resultado'
        if 'Resultado' in df.columns:
            df = df.drop('Resultado')
        return df

