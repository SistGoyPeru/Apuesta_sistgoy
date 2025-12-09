import extraer_data
import polars as pl

class EstadisticasLiga:
    def __init__(self, url=None):
        self.url = url
        self.df = self._obtener_dataframe()

    def _obtener_dataframe(self):
        if self.url:
            calendario = extraer_data.CalendarioLiga(url=self.url)
        else:
            calendario = extraer_data.CalendarioLiga()
        df = calendario.extraer_calendario()
        return df

    def media_goles(self):
        if self.df.is_empty():
            return 0
        # Filtrar partidos con goles válidos
        df_goles = self.df.filter((self.df['GA'].is_not_null()) & (self.df['GV'].is_not_null()))
        total_goles = (df_goles['GA'] + df_goles['GV']).sum()
        total_partidos = df_goles.height
        if total_partidos == 0:
            return 0
        return total_goles / total_partidos

    def partidos_jugados(self):
        if self.df.is_empty():
            return self.df
        # Retorna el DataFrame con solo los partidos jugados (que tienen resultado)
        return self.df.filter((self.df['GA'].is_not_null()) & (self.df['GV'].is_not_null()))

    def total_partidos_jugados(self):
        return self.partidos_jugados().height

    def total_partidos_liga(self):
        return self.df.height

    def total_partidos_por_jugar(self):
        return self.total_partidos_liga() - self.total_partidos_jugados()

    def porcentaje_partidos_jugados(self):
        total = self.total_partidos_liga()
        if total == 0:
            return 0.0
        return (self.total_partidos_jugados() / total) * 100

    def media_goles_local(self):
        df_jugados = self.partidos_jugados()
        if df_jugados.height == 0:
            return 0.0
        return df_jugados['GA'].mean()

    def media_goles_en_contra_local(self):
        df_jugados = self.partidos_jugados()
        if df_jugados.height == 0:
            return 0.0
        return df_jugados['GV'].mean()

    def media_goles_visita(self):
        df_jugados = self.partidos_jugados()
        if df_jugados.height == 0:
            return 0.0
        return df_jugados['GV'].mean()

    def media_goles_en_contra_visita(self):
        df_jugados = self.partidos_jugados()
        if df_jugados.height == 0:
            return 0.0
        return df_jugados['GA'].mean()

    def porcentaje_over_05(self):
        df_jugados = self.partidos_jugados()
        total = df_jugados.height
        if total == 0:
            return 0.0
        matches_over = df_jugados.filter((df_jugados['GA'] + df_jugados['GV']) > 0.5).height
        return (matches_over / total) * 100

    def porcentaje_over_15(self):
        df_jugados = self.partidos_jugados()
        total = df_jugados.height
        if total == 0:
            return 0.0
        matches_over = df_jugados.filter((df_jugados['GA'] + df_jugados['GV']) > 1.5).height
        return (matches_over / total) * 100

    def porcentaje_over_25(self):
        df_jugados = self.partidos_jugados()
        total = df_jugados.height
        if total == 0:
            return 0.0
        matches_over = df_jugados.filter((df_jugados['GA'] + df_jugados['GV']) > 2.5).height
        return (matches_over / total) * 100

    def porcentaje_over_35(self):
        df_jugados = self.partidos_jugados()
        total = df_jugados.height
        if total == 0:
            return 0.0
        matches_over = df_jugados.filter((df_jugados['GA'] + df_jugados['GV']) > 3.5).height
        return (matches_over / total) * 100

    def porcentaje_over_45(self):
        df_jugados = self.partidos_jugados()
        total = df_jugados.height
        if total == 0:
            return 0.0
        matches_over = df_jugados.filter((df_jugados['GA'] + df_jugados['GV']) > 4.5).height
        return (matches_over / total) * 100

    def porcentaje_over_55(self):
        df_jugados = self.partidos_jugados()
        total = df_jugados.height
        if total == 0:
            return 0.0
        matches_over = df_jugados.filter((df_jugados['GA'] + df_jugados['GV']) > 5.5).height
        return (matches_over / total) * 100

    def porcentaje_under_05(self):
        df_jugados = self.partidos_jugados()
        total = df_jugados.height
        if total == 0:
            return 0.0
        matches_under = df_jugados.filter((df_jugados['GA'] + df_jugados['GV']) < 0.5).height
        return (matches_under / total) * 100

    def porcentaje_under_15(self):
        df_jugados = self.partidos_jugados()
        total = df_jugados.height
        if total == 0:
            return 0.0
        matches_under = df_jugados.filter((df_jugados['GA'] + df_jugados['GV']) < 1.5).height
        return (matches_under / total) * 100

    def porcentaje_under_25(self):
        df_jugados = self.partidos_jugados()
        total = df_jugados.height
        if total == 0:
            return 0.0
        matches_under = df_jugados.filter((df_jugados['GA'] + df_jugados['GV']) < 2.5).height
        return (matches_under / total) * 100

    def porcentaje_under_35(self):
        df_jugados = self.partidos_jugados()
        total = df_jugados.height
        if total == 0:
            return 0.0
        matches_under = df_jugados.filter((df_jugados['GA'] + df_jugados['GV']) < 3.5).height
        return (matches_under / total) * 100

    def porcentaje_under_45(self):
        df_jugados = self.partidos_jugados()
        total = df_jugados.height
        if total == 0:
            return 0.0
        matches_under = df_jugados.filter((df_jugados['GA'] + df_jugados['GV']) < 4.5).height
        return (matches_under / total) * 100

    def porcentaje_under_55(self):
        df_jugados = self.partidos_jugados()
        total = df_jugados.height
        if total == 0:
            return 0.0
        matches_under = df_jugados.filter((df_jugados['GA'] + df_jugados['GV']) < 5.5).height
        return (matches_under / total) * 100

    def porcentaje_ambos_marcan(self):
        df_jugados = self.partidos_jugados()
        total = df_jugados.height
        if total == 0:
            return 0.0
        # Ambos marcan si GA > 0 y GV > 0
        matches_btts = df_jugados.filter((df_jugados['GA'] > 0) & (df_jugados['GV'] > 0)).height
        return (matches_btts / total) * 100

    def porcentaje_hay_goles(self):
        return self.porcentaje_over_05()

    def porcentaje_victorias_local(self):
        df_jugados = self.partidos_jugados()
        total = df_jugados.height
        if total == 0:
            return 0.0
        matches_home_win = df_jugados.filter(df_jugados['GA'] > df_jugados['GV']).height
        return (matches_home_win / total) * 100

    def porcentaje_porteria_cero(self):
        # Partidos donde al menos un equipo no marcó (Portería a cero de alguno)
        # Es el complemento de Ambos Marcan
        return 100.0 - self.porcentaje_ambos_marcan()

    def porcentaje_empates(self):
        df_jugados = self.partidos_jugados()
        total = df_jugados.height
        if total == 0:
            return 0.0
        matches_draw = df_jugados.filter(df_jugados['GA'] == df_jugados['GV']).height
        return (matches_draw / total) * 100

    def porcentaje_victorias_visita(self):
        df_jugados = self.partidos_jugados()
        total = df_jugados.height
        if total == 0:
            return 0.0
        matches_away_win = df_jugados.filter(df_jugados['GA'] < df_jugados['GV']).height
        return (matches_away_win / total) * 100

    def porcentaje_clean_sheet_local(self):
        # Local mantiene portería a cero (Visita no marca)
        df_jugados = self.partidos_jugados()
        total = df_jugados.height
        if total == 0:
            return 0.0
        matches = df_jugados.filter(df_jugados['GV'] == 0).height
        return (matches / total) * 100

    def porcentaje_clean_sheet_visita(self):
        # Visita mantiene portería a cero (Local no marca)
        df_jugados = self.partidos_jugados()
        total = df_jugados.height
        if total == 0:
            return 0.0
        matches = df_jugados.filter(df_jugados['GA'] == 0).height
        return (matches / total) * 100

    def porcentaje_local_no_marca(self):
        return self.porcentaje_clean_sheet_visita()

    def porcentaje_visita_no_marca(self):
        return self.porcentaje_clean_sheet_local()

    def marcadores_comunes(self, top_n=5):
        df_jugados = self.partidos_jugados()
        if df_jugados.height == 0:
            return []
        
        # Crear una columna de marcador "GA-GV"
        scores = df_jugados.with_columns(
            (df_jugados['GA'].cast(str) + "-" + df_jugados['GV'].cast(str)).alias('Marcador')
        )
        
        # Contar frecuencias y ordenar
        score_counts = scores['Marcador'].value_counts(sort=True).head(top_n)
        
        # Convertir a lista de diccionarios o tuplas
        result = []
        total = df_jugados.height
        for row in score_counts.iter_rows(named=True):
            marcador = row['Marcador']
            count = row['count'] # polars value_counts returns 'count' or similar
            percentage = (count / total) * 100
            result.append((marcador, percentage))
            
        return result

    def total_goles_liga(self):
        df_jugados = self.partidos_jugados()
        if df_jugados.height == 0: return 0
        return (df_jugados['GA'] + df_jugados['GV']).sum()

    def total_goles_local(self):
        df_jugados = self.partidos_jugados()
        if df_jugados.height == 0: return 0
        return df_jugados['GA'].sum()

    def total_goles_visita(self):
        df_jugados = self.partidos_jugados()
        if df_jugados.height == 0: return 0
        return df_jugados['GV'].sum()

    def distribucion_goles_exactos(self):
        # Cantidad de partidos con exactamente X goles
        df_jugados = self.partidos_jugados()
        if df_jugados.height == 0: return []
        
        goles_totales = (df_jugados['GA'] + df_jugados['GV']).alias('Goles')
        dist = goles_totales.value_counts(sort=True)
        
        result = []
        total = df_jugados.height
        for row in dist.iter_rows(named=True):
            goles = row['Goles']
            count = row['count']
            percentage = (count / total) * 100
            result.append((goles, count, percentage))
        # Ordenar por cantidad de goles ascendente para mostrar 0, 1, 2...
        result.sort(key=lambda x: x[0])
        return result

    def _agrupar_por_equipo(self):
        df = self.partidos_jugados()
        if df.height == 0: return pl.DataFrame()
        
        # Goles anotados y recibidos como local
        local_stats = df.group_by("Local").agg([
            pl.col("GA").sum().alias("GF"),
            pl.col("GV").sum().alias("GC")
        ]).rename({"Local": "Equipo"})
        
        # Goles anotados y recibidos como visita
        visita_stats = df.group_by("Visita").agg([
            pl.col("GV").sum().alias("GF"),
            pl.col("GA").sum().alias("GC")
        ]).rename({"Visita": "Equipo"})
        
        # Unir y sumar
        total_stats = local_stats.join(visita_stats, on="Equipo", how="outer_coalesce")
        # Sumar GF y GF_right, GC y GC_right (rellenando nulls con 0 si es necesario)
        return total_stats.with_columns([
            (pl.col("GF").fill_null(0) + pl.col("GF_right").fill_null(0)).alias("GolesFavor"),
            (pl.col("GC").fill_null(0) + pl.col("GC_right").fill_null(0)).alias("GolesContra")
        ]).select(["Equipo", "GolesFavor", "GolesContra"])

    def equipos_mas_goleadores(self, top_n=5):
        stats = self._agrupar_por_equipo()
        if stats.height == 0: return []
        top = stats.sort("GolesFavor", descending=True).head(top_n)
        return list(top.select(["Equipo", "GolesFavor"]).iter_rows())

    def equipos_mas_goleados(self, top_n=5):
        stats = self._agrupar_por_equipo()
        if stats.height == 0: return []
        top = stats.sort("GolesContra", descending=True).head(top_n)
        return list(top.select(["Equipo", "GolesContra"]).iter_rows())

    def equipos_menos_goleados_defensivos(self, top_n=5):
        # Equipos con MENOS goles en contra (Mejor defensa)
        stats = self._agrupar_por_equipo()
        if stats.height == 0: return []
        top = stats.sort("GolesContra", descending=False).head(top_n)
        return list(top.select(["Equipo", "GolesContra"]).iter_rows())

    def equipos_mas_empates(self, top_n=5):
        df = self.partidos_jugados()
        if df.height == 0: return []
        
        # Filtrar solo empates
        empates = df.filter(pl.col("GA") == pl.col("GV"))
        
        if empates.height == 0: return []

        # Contar empates como local
        local_counts = empates.group_by("Local").agg(pl.len().alias("EmpatesLocal")).rename({"Local": "Equipo"})
        
        # Contar empates como visita
        visita_counts = empates.group_by("Visita").agg(pl.len().alias("EmpatesVisita")).rename({"Visita": "Equipo"})
        
        # Unir stats
        total_counts = local_counts.join(visita_counts, on="Equipo", how="outer_coalesce")
        
        result = total_counts.with_columns(
            (pl.col("EmpatesLocal").fill_null(0) + pl.col("EmpatesVisita").fill_null(0)).alias("TotalEmpates")
        ).sort("TotalEmpates", descending=True).head(top_n)
        
        return list(result.select(["Equipo", "TotalEmpates"]).iter_rows())

    def equipos_mas_derrotas(self, top_n=5):
        df = self.partidos_jugados()
        if df.height == 0: return []
        
        # Derrotas local: GA < GV
        derrotas_local = df.filter(pl.col("GA") < pl.col("GV"))
        # Derrotas visita: GV < GA
        derrotas_visita = df.filter(pl.col("GV") < pl.col("GA"))
        
        local_counts = derrotas_local.group_by("Local").agg(pl.len().alias("DerrotasLocal")).rename({"Local": "Equipo"})
        visita_counts = derrotas_visita.group_by("Visita").agg(pl.len().alias("DerrotasVisita")).rename({"Visita": "Equipo"})
        
        total_counts = local_counts.join(visita_counts, on="Equipo", how="outer_coalesce")
        
        result = total_counts.with_columns(
            (pl.col("DerrotasLocal").fill_null(0) + pl.col("DerrotasVisita").fill_null(0)).alias("TotalDerrotas")
        ).sort("TotalDerrotas", descending=True).head(top_n)
        
        return list(result.select(["Equipo", "TotalDerrotas"]).iter_rows())

    def tabla_posiciones(self):
        df = self.partidos_jugados()
        if df.height == 0: return []

        # Calcular puntos y estadísticas para locales
        # 3 ptos win, 1 pto draw, 0 loss
        def calc_points_local(ga, gv):
            if ga > gv: return 3
            elif ga == gv: return 1
            else: return 0
        
        # No podemos usar apply/map_elements fácilmente en Polars de forma eficiente sin expresiones
        # Usaremos expresiones booleanas para sumar
        
        # Stats Local
        stats_local = df.group_by("Local").agg([
            pl.col("GA").sum().alias("GF_L"),
            pl.col("GV").sum().alias("GC_L"),
            pl.len().alias("PJ_L"),
            (pl.col("GA") > pl.col("GV")).sum().alias("PG_L"),
            (pl.col("GA") == pl.col("GV")).sum().alias("PE_L"),
            (pl.col("GA") < pl.col("GV")).sum().alias("PP_L")
        ]).rename({"Local": "Equipo"})

        # Stats Visita
        stats_visita = df.group_by("Visita").agg([
            pl.col("GV").sum().alias("GF_V"),
            pl.col("GA").sum().alias("GC_V"),
            pl.len().alias("PJ_V"),
            (pl.col("GV") > pl.col("GA")).sum().alias("PG_V"),
            (pl.col("GV") == pl.col("GA")).sum().alias("PE_V"),
            (pl.col("GV") < pl.col("GA")).sum().alias("PP_V")
        ]).rename({"Visita": "Equipo"})

        # Unir
        total = stats_local.join(stats_visita, on="Equipo", how="outer_coalesce").fill_null(0)

        # Calcular totales
        tabla = total.with_columns([
            (pl.col("PJ_L") + pl.col("PJ_V")).alias("PJ"),
            (pl.col("PG_L") + pl.col("PG_V")).alias("PG"),
            (pl.col("PE_L") + pl.col("PE_V")).alias("PE"),
            (pl.col("PP_L") + pl.col("PP_V")).alias("PP"),
            (pl.col("GF_L") + pl.col("GF_V")).alias("GF"),
            (pl.col("GC_L") + pl.col("GC_V")).alias("GC")
        ])
        
        # Calcular Puntos y Diferencia de Gol
        tabla = tabla.with_columns([
            ((pl.col("PG") * 3) + pl.col("PE")).alias("Puntos"),
            (pl.col("GF") - pl.col("GC")).alias("DG")
        ])

        # Calcular PPP (Puntos por Partido)
        tabla = tabla.with_columns([
            (pl.col("Puntos") / pl.col("PJ")).alias("PPP")
        ])

        # Seleccionar y Ordenar: Puntos (desc), DG (desc), GF (desc)
        final_table = tabla.select([
            "Equipo", "Puntos", "PJ", "PG", "PE", "PP", "GF", "GC", "DG", "PPP"
        ]).sort(["Puntos", "DG", "GF"], descending=[True, True, True])

        return list(final_table.iter_rows(named=True))

    def equipos_mas_porterias_cero(self, top_n=5):
        df = self.partidos_jugados()
        if df.height == 0: return []

        # Clean Sheet Local: GV == 0
        cs_local = df.filter(pl.col("GV") == 0).group_by("Local").agg(pl.len().alias("CS_Local")).rename({"Local": "Equipo"})
        # Clean Sheet Visita: GA == 0
        cs_visita = df.filter(pl.col("GA") == 0).group_by("Visita").agg(pl.len().alias("CS_Visita")).rename({"Visita": "Equipo"})

        # Total Matches (PJ)
        pj_local = df.group_by("Local").agg(pl.len().alias("PJ_Local")).rename({"Local": "Equipo"})
        pj_visita = df.group_by("Visita").agg(pl.len().alias("PJ_Visita")).rename({"Visita": "Equipo"})

        # Combine PJ info first
        equipos_pj = pj_local.join(pj_visita, on="Equipo", how="outer_coalesce").select([
            "Equipo", 
            (pl.col("PJ_Local").fill_null(0) + pl.col("PJ_Visita").fill_null(0)).alias("TotalPJ")
        ])

        # Join with CS stats
        # We join back to equipos_pj to ensure we have TotalPJ for percentage
        stats = equipos_pj.join(cs_local, on="Equipo", how="left").join(cs_visita, on="Equipo", how="left")

        result = stats.with_columns(
            (pl.col("CS_Local").fill_null(0) + pl.col("CS_Visita").fill_null(0)).alias("TotalCS")
        ).with_columns(
            ((pl.col("TotalCS") / pl.col("TotalPJ")) * 100).alias("PorcentajeCS")
        ).sort("TotalCS", descending=True).head(top_n)

        return list(result.select(["Equipo", "TotalCS", "PorcentajeCS"]).iter_rows())

    def equipos_sin_marcar(self, top_n=5):
        # Equipos que se quedaron sin marcar gol (Failed to Score)
        df = self.partidos_jugados()
        if df.height == 0: return []

        # Local sin marcar: GA == 0
        fts_local = df.filter(pl.col("GA") == 0).group_by("Local").agg(pl.len().alias("FTS_Local")).rename({"Local": "Equipo"})
        # Visita sin marcar: GV == 0
        fts_visita = df.filter(pl.col("GV") == 0).group_by("Visita").agg(pl.len().alias("FTS_Visita")).rename({"Visita": "Equipo"})

        # Total Matches (PJ)
        pj_local = df.group_by("Local").agg(pl.len().alias("PJ_Local")).rename({"Local": "Equipo"})
        pj_visita = df.group_by("Visita").agg(pl.len().alias("PJ_Visita")).rename({"Visita": "Equipo"})

        # Combine PJ info
        equipos_pj = pj_local.join(pj_visita, on="Equipo", how="outer_coalesce").select([
            "Equipo", 
            (pl.col("PJ_Local").fill_null(0) + pl.col("PJ_Visita").fill_null(0)).alias("TotalPJ")
        ])

        # Join with FTS stats
        stats = equipos_pj.join(fts_local, on="Equipo", how="left").join(fts_visita, on="Equipo", how="left")

        result = stats.with_columns(
            (pl.col("FTS_Local").fill_null(0) + pl.col("FTS_Visita").fill_null(0)).alias("TotalFTS")
        ).with_columns(
            ((pl.col("TotalFTS") / pl.col("TotalPJ")) * 100).alias("PorcentajeFTS")
        ).sort("TotalFTS", descending=True).head(top_n)

        return list(result.select(["Equipo", "TotalFTS", "PorcentajeFTS"]).iter_rows())
