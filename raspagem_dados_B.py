import io
import os
import pandas as pd
import requests

# -------------------------------------------------------------------------
# 1. MAPEAMENTO DAS 9 LIGAS SELECIONADAS (PLANO B)
# -------------------------------------------------------------------------
URLS_PLANO_B = {
    # 🟢 Top Ligas Over / Alta Frequência de Gols
    'Noruega_Eliteserien': 'https://www.football-data.co.uk/new/NOR.csv',
    'Suica_SuperLeague': 'https://www.football-data.co.uk/new/SWZ.csv',
    'Austria_Bundesliga': 'https://www.football-data.co.uk/new/AUT.csv',
    'Dinamarca_Superliga': 'https://www.football-data.co.uk/new/DNK.csv',
    'EUA_MLS': 'https://www.football-data.co.uk/new/USA.csv',
    'Suecia_Allsvenskan': 'https://www.football-data.co.uk/new/SWE.csv',
    # 🟡 Ligas Estratégicas / Grade Alternativa
    'Brasil_Serie_A': 'https://www.football-data.co.uk/new/BRA.csv',
    'Mexico_LigaMX': 'https://www.football-data.co.uk/new/MEX.csv',
    'Japao_JLeague': 'https://www.football-data.co.uk/new/JPN.csv',
}

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
}


def baixar_e_salvar_plano_b(
    urls_dict=URLS_PLANO_B,
    seasons_atuais=['2026', '2026/2027'],
    apenas_temporada_atual=True,
    arquivo_saida='base_gols_plano_b.csv',
):
  dfs = []
  print('🚀 Iniciando coleta padronizada do Plano B...')

  for nome_liga, url in urls_dict.items():
    try:
      resposta = requests.get(url, headers=HEADERS, timeout=15)

      if resposta.status_code == 200:
        # Fallback de encoding (UTF-8 ou Latin-1)
        try:
          df_temp = pd.read_csv(io.StringIO(resposta.content.decode('utf-8')))
        except UnicodeDecodeError:
          df_temp = pd.read_csv(io.StringIO(resposta.content.decode('latin1')))

        # Normalização dos nomes de colunas originais do football-data /new/
        rename_map = {
            'Country': 'Pais',
            'League': 'Liga_Nome',
            'Season': 'Temporada',
            'Date': 'Date',
            'Time': 'Hora',
            'Home': 'HomeTeam',
            'Away': 'AwayTeam',
            'HG': 'FTHG',
            'AG': 'FTAG',
            'Res': 'FTR',
        }
        df_temp.rename(columns=rename_map, inplace=True)
        df_temp['Liga'] = nome_liga

        # Descarte de partidas sem times ou placar final
        colunas_obrigatorias = ['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']
        if not all(col in df_temp.columns for col in colunas_obrigatorias):
          print(f'Aviso: {nome_liga} sem colunas completas de placar.')
          continue

        df_temp = df_temp.dropna(subset=colunas_obrigatorias).copy()

        # Filtro de temporada (opcional: foca na atual para ficar leve)
        if apenas_temporada_atual and 'Temporada' in df_temp.columns:
          df_temp = df_temp[
              df_temp['Temporada'].astype(str).isin(seasons_atuais)
          ].copy()

        if df_temp.empty:
          print(f'Aviso: {nome_liga} sem jogos para a temporada selecionada.')
          continue

        # Tratamento de colunas que não vêm no Plano B (preenche com 0 para manter paridade com Plano A)
        colunas_verificar = ['HTHG', 'HTAG', 'HST', 'AST']
        for col in colunas_verificar:
          if col not in df_temp.columns:
            df_temp[col] = 0
          else:
            df_temp[col] = df_temp[col].fillna(0)

        # Conversão de tipos
        for col in ['FTHG', 'FTAG', 'HTHG', 'HTAG', 'HST', 'AST']:
          df_temp[col] = df_temp[col].astype(int)

        # ==========================================
        # FEATURES DERIVADAS PADRONIZADAS COM O PLANO A
        # ==========================================
        df_temp['TotalGols_FT'] = df_temp['FTHG'] + df_temp['FTAG']
        df_temp['TotalGols_HT'] = df_temp['HTHG'] + df_temp['HTAG']

        # Mercados Binários
        df_temp['Over05_FT'] = (df_temp['TotalGols_FT'] > 0.5).astype(int)
        df_temp['Over15_FT'] = (df_temp['TotalGols_FT'] > 1.5).astype(int)
        df_temp['Over25_FT'] = (df_temp['TotalGols_FT'] > 2.5).astype(int)
        df_temp['Over05_HT'] = (df_temp['TotalGols_HT'] > 0.5).astype(int)
        df_temp['BTTS'] = (
            (df_temp['FTHG'] > 0) & (df_temp['FTAG'] > 0)
        ).astype(int)

        # Estrutura idêntica ao Plano A + Origem/País
        colunas_finais = [
            'Liga',
            'Temporada',
            'Date',
            'HomeTeam',
            'AwayTeam',
            'FTHG',
            'FTAG',
            'HTHG',
            'HTAG',
            'HST',
            'AST',
            'TotalGols_FT',
            'TotalGols_HT',
            'Over05_FT',
            'Over15_FT',
            'Over25_FT',
            'Over05_HT',
            'BTTS',
            'Pais',
        ]

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
    print('BASE CONSOLIDADA DO PLANO B CRIADA COM SUCESSO!')
    print(f'Arquivo: {os.path.abspath(arquivo_saida)}')
    print(f'Total geral de jogos: {len(df_consolidado)}')
    print('Colunas idênticas às do Plano A prontas para o app.')
    print('=' * 60 + '\n')
    return df_consolidado
  else:
    print('Nenhum dado foi baixado.')
    return pd.DataFrame()


if __name__ == '__main__':
  df_base_b = baixar_e_salvar_plano_b()