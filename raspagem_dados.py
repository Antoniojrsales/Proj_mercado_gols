import io
import os
import pandas as pd
import requests

# Ligas confirmadas com sucesso no Football-Data
LIGAS = {
    'Inglaterra_Premier': 'E0',
    'Escocia_Premiership': 'SC0',
    'Alemanha_Bundesliga': 'D1',
    'Italia_SerieA': 'I1',
    'Espanha_LaLiga': 'SP1',
    'Franca_Ligue1': 'F1',
    'Holanda_Eredivisie': 'N1',
    'Belgica_Jupiler': 'B1',
    'Portugal_Primeira': 'P1',
    'Turquia_SuperLig': 'T1',
}

headers = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,'
        ' like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
}

def baixar_e_salvar_csv(
    ligas_dict, temporada='2526', arquivo_saida='base_gols_consolidada.csv'
):
    dfs = []

    for nome_liga, codigo in ligas_dict.items():
        url = f'https://www.football-data.co.uk/mmz4281/{temporada}/{codigo}.csv'
        try:
            resposta = requests.get(url, headers=headers, timeout=12)

            if resposta.status_code == 200:
                df_temp = pd.read_csv(io.StringIO(resposta.text))

                # Metadados
                df_temp['Liga'] = nome_liga
                df_temp['Temporada'] = temporada

                # Colunas essenciais
                colunas_obrigatorias = ['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']
                
                # Descarta jogos sem placar realizado
                if not all(col in df_temp.columns for col in colunas_obrigatorias):
                    print(f'Aviso: {nome_liga} sem colunas completas de placar.')
                    continue

                df_temp = df_temp.dropna(subset=['FTHG', 'FTAG']).copy()

                # Tratamento de dados faltantes em HT e Chutes
                colunas_verificar = ['HTHG', 'HTAG', 'HST', 'AST']
                for col in colunas_verificar:
                    if col not in df_temp.columns:
                        df_temp[col] = 0
                    else:
                        df_temp[col] = df_temp[col].fillna(0)

                # Conversão para números inteiros
                for col in ['FTHG', 'FTAG', 'HTHG', 'HTAG', 'HST', 'AST']:
                    df_temp[col] = df_temp[col].astype(int)

                # ==========================================
                # FEATURES DERIVADAS PARA TODOS OS MERCADOS
                # ==========================================
                df_temp['TotalGols_FT'] = df_temp['FTHG'] + df_temp['FTAG']
                df_temp['TotalGols_HT'] = df_temp['HTHG'] + df_temp['HTAG']
                
                # Mercados Binários (1 para bateu, 0 para não bateu)
                df_temp['Over05_FT'] = (df_temp['TotalGols_FT'] > 0.5).astype(int)
                df_temp['Over15_FT'] = (df_temp['TotalGols_FT'] > 1.5).astype(int)
                df_temp['Over25_FT'] = (df_temp['TotalGols_FT'] > 2.5).astype(int)
                df_temp['Over05_HT'] = (df_temp['TotalGols_HT'] > 0.5).astype(int)
                df_temp['BTTS'] = ((df_temp['FTHG'] > 0) & (df_temp['FTAG'] > 0)).astype(int)

                colunas_finais = [
                    'Liga', 'Temporada', 'Date', 'HomeTeam', 'AwayTeam',
                    'FTHG', 'FTAG', 'HTHG', 'HTAG', 'HST', 'AST',
                    'TotalGols_FT', 'TotalGols_HT',
                    'Over05_FT', 'Over15_FT', 'Over25_FT', 'Over05_HT', 'BTTS'
                ]

                # Filtra apenas o que interessa
                df_temp = df_temp[[c for c in colunas_finais if c in df_temp.columns]]

                dfs.append(df_temp)
                print(f'Sucesso: {nome_liga} ({len(df_temp)} jogos processados)')
            else:
                print(f'Aviso: {nome_liga} retornou Status {resposta.status_code}')

        except Exception as erro:
            print(f'Erro ao processar {nome_liga}: {erro}')

    if dfs:
        df_consolidado = pd.concat(dfs, ignore_index=True)
        df_consolidado.to_csv(arquivo_saida, index=False, encoding='utf-8-sig')

        print('\n' + '=' * 60)
        print('BASE CONSOLIDADA CRIADA COM SUCESSO!')
        print(f'Arquivo: {os.path.abspath(arquivo_saida)}')
        print(f'Total geral de jogos: {len(df_consolidado)}')
        print('Mercados disponíveis: 0.5 FT, 1.5 FT, 2.5 FT, 0.5 HT e BTTS')
        print('=' * 60 + '\n')
        return df_consolidado
    else:
        print('Nenhum dado foi baixado.')
        return pd.DataFrame()

if __name__ == '__main__':
    df_base = baixar_e_salvar_csv(LIGAS)