import pandas as pd
import numpy as np


def calcular_elo_com_ajustes(df, k=32, elo_inicial=1500, fator_regressao=0.7):
    """
    Calcula o Elo com ajustes para times promovidos e rebaixados no início de cada temporada.

    Args:
        df (pd.DataFrame): DataFrame com os dados das partidas.
        k (int): Fator K.
        elo_inicial (int): Pontuação de Elo inicial.
        fator_regressao (float): Quanto do Elo anterior é conservado (0 a 1).
                                  Um valor de 0.7 significa que 30% do Elo retorna para a média.
    """
    elos = {}

    df["datetime"] = pd.to_datetime(df["data"] + " " + df["hora"])
    df = df.sort_values("datetime").reset_index(drop=True)
    df["temporada"] = df["datetime"].dt.year

    temporada_anterior = None
    equipes_temporada_anterior = set()

    elo_mandante_lista = []
    elo_visitante_lista = []

    for index, row in df.iterrows():
        temporada_actual = row["temporada"]

        # --- LÓGICA DE AJUSTE ENTRE TEMPORADAS ---
        if temporada_actual != temporada_anterior and temporada_anterior is not None:
            print(
                f"\n--- Mudança de temporada detectada: {temporada_anterior} -> {temporada_actual} ---"
            )

            # Aplicar regressão à média para todas as equipes existentes
            for equipe, elo in elos.items():
                elos[equipe] = (elo * fator_regressao) + (
                    elo_inicial * (1 - fator_regressao)
                )
            print("Regressão à média aplicada às equipes existentes.")

            # Identificar equipes promovidas (subiram) e rebaixadas (caíram)
            equipes_esta_temporada = set(
                df[df["temporada"] == temporada_actual]["mandante"]
            ).union(set(df[df["temporada"] == temporada_actual]["visitante"]))

            equipes_rebaixadas = equipes_temporada_anterior - equipes_esta_temporada
            equipes_promovidas = equipes_esta_temporada - equipes_temporada_anterior

            if equipes_rebaixadas:
                # Calcular o Elo médio das equipes que foram rebaixadas
                elos_rebaixados = [
                    elos.get(equipe, elo_inicial) for equipe in equipes_rebaixadas
                ]
                elo_medio_rebaixados = np.mean(elos_rebaixados)

                print(f"Equipes rebaixadas: {equipes_rebaixadas}")
                print(f"Equipes promovidas: {equipes_promovidas}")
                print(f"Elo médio das equipes rebaixadas: {elo_medio_rebaixados:.2f}")

                # Atribuir este Elo às equipes promovidas
                for equipe in equipes_promovidas:
                    elos[equipe] = elo_medio_rebaixados
                print("Elo das equipes promovidas ajustado.")

        # Atualizar a lista de equipes da temporada atual
        equipes_temporada_anterior = set(
            df[df["temporada"] == temporada_actual]["mandante"]
        ).union(set(df[df["temporada"] == temporada_actual]["visitante"]))
        temporada_anterior = temporada_actual

        mandante = row["mandante"]
        visitante = row["visitante"]

        elo_mandante = elos.get(mandante, elo_inicial)
        elo_visitante = elos.get(visitante, elo_inicial)

        # Se a equipe é completamente nova (primeira temporada nos dados), atribui-se o elo inicial
        if mandante not in elos:
            elos[mandante] = elo_inicial
        if visitante not in elos:
            elos[visitante] = elo_inicial

        elo_mandante_lista.append(elo_mandante)
        elo_visitante_lista.append(elo_visitante)

        prob_mandante = 1 / (1 + 10 ** ((elo_visitante - elo_mandante) / 400))
        prob_visitante = 1 - prob_mandante

        if row["vencedor"] == mandante:
            resultado_mandante, resultado_visitante = 1, 0
        elif row["vencedor"] == visitante:
            resultado_mandante, resultado_visitante = 0, 1
        else:
            resultado_mandante, resultado_visitante = 0.5, 0.5

        # Ver a questão do valor do k
        novo_elo_mandante = elo_mandante + k * (resultado_mandante - prob_mandante)
        novo_elo_visitante = elo_visitante + k * (resultado_visitante - prob_visitante)

        elos[mandante] = novo_elo_mandante
        elos[visitante] = novo_elo_visitante

    df["elo_mandante_antes"] = elo_mandante_lista
    df["elo_visitante_antes"] = elo_visitante_lista

    return df


# --- Executar o script ---
try:
    df_original = pd.read_csv("campeonato-brasileiro-full.csv")
    df_com_elo_ajustado = calcular_elo_com_ajustes(df_original)

    df_com_elo_ajustado.to_csv(
        "campeonato-brasileiro-com-elo-ajustado.csv", index=False
    )

    print("\n✅ Cálculo de Elo com ajustes concluído.")
    print("Resultados salvos em 'campeonato-brasileiro-com-elo-ajustado.csv'")

except FileNotFoundError:
    print("Erro: O arquivo 'campeonato-brasileiro-full.csv' não foi encontrado.")
