import pandas as pd
import plotly.express as px


def graficar_evolucao_elo_interativo(arquivo_csv, temporada):
    """
    Cria um gráfico de linhas INTERATIVO para a evolução do Elo de cada equipe.
    """
    # Carregar e preparar os dados
    try:
        df = pd.read_csv(arquivo_csv)
    except FileNotFoundError:
        print(f"Erro: O arquivo '{arquivo_csv}' não foi encontrado.")
        return

    df["datetime"] = pd.to_datetime(df["datetime"])

    # Calculamos as colunas 'depois' que não estão no arquivo
    df = df.sort_values("datetime")
    df["elo_mandante_depois"] = df.groupby("mandante")["elo_mandante_antes"].shift(-1)
    df["elo_visitante_depois"] = df.groupby("visitante")["elo_visitante_antes"].shift(
        -1
    )

    df_temporada = df[df["datetime"].dt.year == temporada].copy()

    if df_temporada.empty:
        print(f"Nenhum dado encontrado para a temporada {temporada}.")
        return

    mandante_elo = df_temporada[["datetime", "mandante", "elo_mandante_depois"]].rename(
        columns={"mandante": "equipe", "elo_mandante_depois": "elo"}
    )
    visitante_elo = df_temporada[
        ["datetime", "visitante", "elo_visitante_depois"]
    ].rename(columns={"visitante": "equipe", "elo_visitante_depois": "elo"})

    elo_evolucao = (
        pd.concat([mandante_elo, visitante_elo]).dropna().sort_values("datetime")
    )

    elo_inicial_df = (
        df_temporada.groupby("mandante")["elo_mandante_antes"]
        .first()
        .reset_index()
        .rename(columns={"mandante": "equipe", "elo_mandante_antes": "elo"})
    )
    elo_inicial_df["datetime"] = df_temporada["datetime"].min() - pd.Timedelta(days=1)
    elo_evolucao = pd.concat([elo_evolucao, elo_inicial_df]).sort_values("datetime")

    # Criar o gráfico interativo com o Plotly Express
    fig = px.line(
        elo_evolucao,
        x="datetime",
        y="elo",
        color="equipe",  # Define uma cor para cada equipe e cria a legenda interativa
        labels={"datetime": "Data", "elo": "Pontuação Elo", "equipe": "Equipe"},
        title=f"Evolução Interativa do Elo - Brasileirão {temporada}",
    )

    # Melhorar o design do gráfico
    fig.update_layout(
        title_x=0.5,  # Centralizar o título
        legend_title_text="Equipes (clique para filtrar)",
        hovermode="x unified",  # Mostra os dados de todas as equipes ao passar o mouse sobre uma data
    )

    # Mostrar o gráfico e salvá-lo como um arquivo HTML
    fig.show()

    nome_grafico = f"evolucao_elo_interativo_{temporada}.html"
    fig.write_html(nome_grafico)
    print(f"Gráfico interativo salvo como '{nome_grafico}'")


# --- Executar a função ---
if __name__ == "__main__":
    graficar_evolucao_elo_interativo(
        "campeonato-brasileiro-con-elo-ajustado.csv", temporada=2023
    )
