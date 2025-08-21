import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Diretório base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

CSV = BASE_DIR / "tests" / "perguntas.csv"
REPORTS_DIR = BASE_DIR / "tests" / "reports"

# Certifique-se de que o diretório REPORTS_DIR existe
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

CHATBOT_URL = "http://127.0.0.1:5000/api/chatbot"

INPUT_FILE = CSV
OUTPUT_FILE = REPORTS_DIR / "resultados_similaridade.csv"

# Carregar o arquivo de perguntas
df = pd.read_csv(INPUT_FILE)

print("Visualizando os dados de entrada:")
print(df.head())

required_columns = ["categoria", "mensagem"]
if not all(col in df.columns for col in required_columns):
    raise ValueError(f"O arquivo deve conter as colunas: {required_columns}")

# Adicionar colunas para armazenar as respostas e similaridades
df["resposta"] = ""
df["similaridade"] = 0.0

# Iterar sobre as perguntas e enviar ao chatbot
for index, row in df.iterrows():
    mensagem = row["mensagem"]
    categoria = row["categoria"]

    try:
        response = requests.post(CHATBOT_URL, json={"message": mensagem})
        response_data = response.json()

        # Armazenar a resposta e a similaridade
        df.at[index, "resposta"] = response_data.get("response", "Erro na resposta")
        df.at[index, "similaridade"] = response_data.get("similaridade", 0.0)

        print(f"Mensagem: {mensagem}")
        print(f"Resposta: {response_data.get('response')}")
        print(f"Similaridade: {response_data.get('similaridade')}\n")

    except Exception as e:
        print(f"Erro ao processar a mensagem '{mensagem}': {e}")
        df.at[index, "resposta"] = "Erro"
        df.at[index, "similaridade"] = 0.0

# Salvar os resultados em um arquivo CSV
df.to_csv(OUTPUT_FILE, index=False)
print(f"Resultados salvos em '{OUTPUT_FILE}'")

# Estilo bonito para os gráficos
sns.set(style="whitegrid", palette="muted", font_scale=1.2)

# Gerar histogramas para cada categoria
categorias = df["categoria"].unique()
for categoria in categorias:
    subset = df[df["categoria"] == categoria]

    if subset.empty:
        print(f"A categoria '{categoria}' não possui dados suficientes para gerar um histograma.")
        continue

    plt.figure(figsize=(8, 5))
    ax = sns.histplot(
        subset["similaridade"],
        bins=10,
        kde=True,
        color=sns.color_palette("Set2")[0],
        edgecolor="black"
    )

    plt.title(f"Distribuição de Similaridade - {categoria}", fontsize=16, weight='bold')
    plt.xlabel("Similaridade", fontsize=13)
    plt.ylabel("Frequência", fontsize=13)
    plt.xlim(0, 1)
    plt.ylim(0)
    plt.tight_layout()
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Adiciona a média no gráfico
    media = subset["similaridade"].mean()
    plt.axvline(media, color='red', linestyle='--', linewidth=2, label=f"Média: {media:.2f}")
    plt.legend()

    # Salvar o histograma
    output_path = REPORTS_DIR / f"histograma_{categoria}.png"
    plt.savefig(output_path, dpi=150)
    print(f"Histograma salvo em: {output_path}")
    plt.close()

print("Histogramas gerados e salvos como imagens.")