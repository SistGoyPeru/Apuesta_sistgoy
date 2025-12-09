from estadisticas_ligas import EstadisticasLiga
import pronostico
if __name__ == "__main__":



    print("\n" + "="*80)
    print("PRONÓSTICOS PRÓXIMA JORNADA (Método Poisson)")
    print("="*80)
    
    pronosticador = pronostico.PronosticoPoisson()
    todos = pronosticador.calcular_pronosticos_todos()
    # Filtrar partidos pendientes (ResultadoReal == 'N/A')
    pendientes = [p for p in todos if p["ResultadoReal"] == "N/A"]
    
    import polars as pl
    
    # Configurar ancho de impresión de Polars para que se vea bien en terminal
    pl.Config.set_tbl_rows(100) # Mostrar suficientes filas
    pl.Config.set_tbl_cols(10)
    pl.Config.set_fmt_str_lengths(30)
    
    if pendientes:
        # Crear DataFrame
        df_preds = pl.DataFrame(pendientes)
        
        # Seleccionar y renombrar columnas relevantes
        df_display = df_preds.select([
            pl.col("Jornada").alias("Jor"),
            pl.col("EquipoLocal").alias("Local"),
            pl.col("EquipoVisita").alias("Visita"),
            # 1X2
            pl.col("ProbLocal").round(1).alias("1(%)"),
            pl.col("ProbEmpate").round(1).alias("X(%)"),
            pl.col("ProbVisita").round(1).alias("2(%)"),
            # Doble Oportunidad
            pl.col("Prob1X").round(1).alias("1X(%)"),
            pl.col("Prob12").round(1).alias("12(%)"),
            pl.col("ProbX2").round(1).alias("X2(%)"),
            # Goles Over
            pl.col("ProbOver05").round(1).alias(">0.5"),
            pl.col("ProbOver15").round(1).alias(">1.5"),
            pl.col("ProbOver25").round(1).alias(">2.5"),
            pl.col("ProbOver35").round(1).alias(">3.5"),
            pl.col("ProbOver45").round(1).alias(">4.5"),
            pl.col("ProbOver55").round(1).alias(">5.5"),
            # Goles Under
            pl.col("ProbUnder05").round(1).alias("<0.5"),
            pl.col("ProbUnder15").round(1).alias("<1.5"),
            pl.col("ProbUnder25").round(1).alias("<2.5"),
            pl.col("ProbUnder35").round(1).alias("<3.5"),
            pl.col("ProbUnder45").round(1).alias("<4.5"),
            pl.col("ProbUnder55").round(1).alias("<5.5"),
            # BTTS
            pl.col("ProbAmbosMarcan").round(1).alias("BTTS Y"),
            pl.col("ProbNoAmbosMarcan").round(1).alias("BTTS N"),
            # Score
            pl.col("MarcadorProbable").alias("Score")
        ])
        
        # Ajustar ancho de columnas para ver todo
        pl.Config.set_tbl_width_chars(400)
        pl.Config.set_tbl_cols(30) # Aumentar para que quepan todas las columnas
        
        print(df_display)
    else:
        print("No hay partidos pendientes.")
