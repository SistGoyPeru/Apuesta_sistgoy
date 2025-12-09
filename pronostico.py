import polars as pl
import numpy as np
from scipy.stats import poisson
from estadisticas_ligas import EstadisticasLiga

class PronosticoPoisson:
    def __init__(self, stats_liga=None):
        if stats_liga:
            self.stats = stats_liga
        else:
            self.stats = EstadisticasLiga()
        
        self.df_partidos = self.stats.df  # Todos los partidos (jugados y por jugar)
        self.df_jugados = self.stats.partidos_jugados()  # Solo jugados para calcular fuerzas
        self.fuerzas = {}
        self.medias_liga = {}
        self._calcular_fuerzas()

    def _calcular_fuerzas(self):
        if self.df_jugados.height == 0:
            return

        # 1. Medias Globales de la Liga
        # Promedio de goles que marca un equipo local por partido
        media_goles_local_liga = self.stats.media_goles_local()
        # Promedio de goles que marca un equipo visitante por partido
        media_goles_visita_liga = self.stats.media_goles_visita()
        
        self.medias_liga = {
            "local": media_goles_local_liga,
            "visita": media_goles_visita_liga
        }

        # 2. Estadísticas por Equipo (Local y Visita)
        
        # Stats Local: GF (Goles Favor), GC (Goles Contra), PJ (Partidos Jugados)
        stats_local = self.df_jugados.group_by("Local").agg([
            pl.col("GA").sum().alias("GF"),
            pl.col("GV").sum().alias("GC"),
            pl.len().alias("PJ")
        ]).rename({"Local": "Equipo"})

        # Stats Visita
        stats_visita = self.df_jugados.group_by("Visita").agg([
            pl.col("GV").sum().alias("GF"),
            pl.col("GA").sum().alias("GC"),
            pl.len().alias("PJ")
        ]).rename({"Visita": "Equipo"})

        # Convertir a diccionarios para acceso rápido
        # Usaremos diccionarios anidados: self.fuerzas[equipo]["local"|"visita"]["ataque"|"defensa"]
        
        def safe_div(a, b):
            return a / b if b > 0 else 0

        # Procesar locales
        for row in stats_local.iter_rows(named=True):
            equipo = row["Equipo"]
            if equipo not in self.fuerzas: self.fuerzas[equipo] = {"local": {}, "visita": {}}
            
            # Fuerza Ataque Local = (Goles Favor Local / PJ Local) / Media Liga Local
            avg_gf_local = safe_div(row["GF"], row["PJ"])
            fuerza_ataque = safe_div(avg_gf_local, media_goles_local_liga)
            
            # Fuerza Defensa Local = (Goles Contra Local / PJ Local) / Media Liga Visita
            # (Lo que el local recibe es lo que la visita anota promedio)
            avg_gc_local = safe_div(row["GC"], row["PJ"])
            fuerza_defensa = safe_div(avg_gc_local, media_goles_visita_liga)

            self.fuerzas[equipo]["local"] = {"ataque": fuerza_ataque, "defensa": fuerza_defensa}

        # Procesar visitas
        for row in stats_visita.iter_rows(named=True):
            equipo = row["Equipo"]
            if equipo not in self.fuerzas: self.fuerzas[equipo] = {"local": {}, "visita": {}}
            
            # Fuerza Ataque Visita = (Goles Favor Visita / PJ Visita) / Media Liga Visita
            avg_gf_visita = safe_div(row["GF"], row["PJ"])
            fuerza_ataque = safe_div(avg_gf_visita, media_goles_visita_liga)
            
            # Fuerza Defensa Visita = (Goles Contra Visita / PJ Visita) / Media Liga Local
            avg_gc_visita = safe_div(row["GC"], row["PJ"])
            fuerza_defensa = safe_div(avg_gc_visita, media_goles_local_liga)

            self.fuerzas[equipo]["visita"] = {"ataque": fuerza_ataque, "defensa": fuerza_defensa}

    def predecir_partido(self, local, visita):
        if local not in self.fuerzas or visita not in self.fuerzas:
            return None # No hay datos suficientes

        # Datos seguros con .get por si falta algún lado (ej: equipo nuevo sin partidos de local aun)
        f_ataque_local = self.fuerzas[local].get("local", {}).get("ataque", 1.0)
        f_defensa_local = self.fuerzas[local].get("local", {}).get("defensa", 1.0)
        
        f_ataque_visita = self.fuerzas[visita].get("visita", {}).get("ataque", 1.0)
        f_defensa_visita = self.fuerzas[visita].get("visita", {}).get("defensa", 1.0)

        # Goles Esperados
        # Lambda Local = F.Ataque Local * F.Defensa Visita * Media Goles Local Liga
        expectativa_goles_local = f_ataque_local * f_defensa_visita * self.medias_liga["local"]
        
        # Lambda Visita = F.Ataque Visita * F.Defensa Local * Media Goles Visita Liga
        expectativa_goles_visita = f_ataque_visita * f_defensa_local * self.medias_liga["visita"]

        # Calcular probabilidades con Poisson (hasta 10 goles por lado)
        range_goles = range(10)
        probs_local = [poisson.pmf(i, expectativa_goles_local) for i in range_goles]
        probs_visita = [poisson.pmf(i, expectativa_goles_visita) for i in range_goles]

        prob_victoria_local = 0.0
        prob_empate = 0.0
        prob_victoria_visita = 0.0
        prob_over_05 = 0.0
        prob_over_15 = 0.0
        prob_over_25 = 0.0
        prob_over_35 = 0.0
        prob_over_45 = 0.0
        prob_over_55 = 0.0
        
        prob_ambos_marcan = 0.0
        
        # Para marcador exacto
        max_prob_score = 0.0
        best_score = "0-0"

        for g_local in range_goles:
            for g_visita in range_goles:
                prob_evento = probs_local[g_local] * probs_visita[g_visita]
                
                # 1X2
                if g_local > g_visita:
                    prob_victoria_local += prob_evento
                elif g_local == g_visita:
                    prob_empate += prob_evento
                else:
                    prob_victoria_visita += prob_evento
                
                # Totals
                total_goles = g_local + g_visita
                if total_goles > 0.5: prob_over_05 += prob_evento
                if total_goles > 1.5: prob_over_15 += prob_evento
                if total_goles > 2.5: prob_over_25 += prob_evento
                if total_goles > 3.5: prob_over_35 += prob_evento
                if total_goles > 4.5: prob_over_45 += prob_evento
                if total_goles > 5.5: prob_over_55 += prob_evento

                # Ambos Marcan
                if g_local > 0 and g_visita > 0:
                    prob_ambos_marcan += prob_evento
                    
                # Marcador exacto más probable
                if prob_evento > max_prob_score:
                    max_prob_score = prob_evento
                    best_score = f"{g_local}-{g_visita}"

        # Doble Oportunidad
        prob_1x = prob_victoria_local + prob_empate
        prob_x2 = prob_empate + prob_victoria_visita
        prob_12 = prob_victoria_local + prob_victoria_visita
        
        return {
            "EquipoLocal": local,
            "EquipoVisita": visita,
            # 1X2
            "ProbLocal": prob_victoria_local * 100,
            "ProbEmpate": prob_empate * 100,
            "ProbVisita": prob_victoria_visita * 100,
            # Doble Oportunidad
            "Prob1X": prob_1x * 100,
            "ProbX2": prob_x2 * 100,
            "Prob12": prob_12 * 100,
            # Goles Over
            "ProbOver05": prob_over_05 * 100,
            "ProbOver15": prob_over_15 * 100,
            "ProbOver25": prob_over_25 * 100,
            "ProbOver35": prob_over_35 * 100,
            "ProbOver45": prob_over_45 * 100,
            "ProbOver55": prob_over_55 * 100,
            # Goles Under
            "ProbUnder05": (1 - prob_over_05) * 100,
            "ProbUnder15": (1 - prob_over_15) * 100,
            "ProbUnder25": (1 - prob_over_25) * 100,
            "ProbUnder35": (1 - prob_over_35) * 100,
            "ProbUnder45": (1 - prob_over_45) * 100,
            "ProbUnder55": (1 - prob_over_55) * 100,
            # BTTS
            "ProbAmbosMarcan": prob_ambos_marcan * 100,
            "ProbNoAmbosMarcan": (1 - prob_ambos_marcan) * 100,
            # Marcador
            "MarcadorProbable": best_score,
            "ExpGolesLocal": expectativa_goles_local,
            "ExpGolesVisita": expectativa_goles_visita,
        }

    def calcular_pronosticos_todos(self):
        # Generar lista de pronósticos para todos los partidos del calendario
        pronosticos = []
        for row in self.df_partidos.iter_rows(named=True):
            local = row["Local"]
            visita = row["Visita"]
            
            # Si el equipo no tiene stats suficientes, se ignora o se pone nulo
            pred = self.predecir_partido(local, visita)
            if pred:
                # Agregar información del resultado real si existe
                pred["Jornada"] = row["Jornada"]
                pred["Fecha"] = row["Fecha"]
                pred["ResultadoReal"] = f"{row['GA']}-{row['GV']}" if row['GA'] is not None else "N/A"
                pronosticos.append(pred)
        
        return pronosticos

