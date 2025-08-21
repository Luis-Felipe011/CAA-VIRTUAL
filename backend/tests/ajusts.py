import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Diretório base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "tests" / "reports"
CSV_RESULT = REPORTS_DIR / "resultados_similaridade.csv"

# Carregar os resultados já existentes
df = pd.read_csv(CSV_RESULT)

# Remover resultados com similaridade == 1
df_filtrado = df[df["similaridade"] < 1.0]

# Estilo bonito para os gráficos
sns.set(style="whitegrid", palette="muted", font_scale=1.2)

# Gerar histogramas para cada categoria (sem similaridade == 1)
categorias = df_filtrado["categoria"].unique()
cores = sns.color_palette("Set2", len(categorias))

for idx, categoria in enumerate(categorias):
    subset = df_filtrado[df_filtrado["categoria"] == categoria]
    if subset.empty:
        print(f"A categoria '{categoria}' não possui dados suficientes para gerar um histograma.")
        continue

    plt.figure(figsize=(8, 5))
    ax = sns.histplot(
        subset["similaridade"],
        bins=10,
        kde=True,
        color=cores[idx],
        edgecolor="black"
    )

    media = subset["similaridade"].mean()
    plt.title(f"Distribuição de Similaridade - {categoria} (sem similaridade 1)", fontsize=16, weight='bold')
    plt.xlabel("Similaridade", fontsize=13)
    plt.ylabel("Frequência", fontsize=13)
    plt.xlim(0, 1)
    plt.ylim(0)
    plt.tight_layout()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.axvline(media, color='red', linestyle='--', linewidth=2, label=f"Média: {media:.2f}")
    plt.legend()
    output_path = REPORTS_DIR / f"histograma_{categoria}_sem_1.png"
    plt.savefig(output_path, dpi=150)
    print(f"Histograma salvo em: {output_path}")
    plt.close()

# Histograma sobreposto para todas as categorias (sem similaridade == 1)
plt.figure(figsize=(10, 6))
for idx, categoria in enumerate(categorias):
    subset = df_filtrado[df_filtrado["categoria"] == categoria]
    if not subset.empty:
        sns.histplot(
            subset["similaridade"],
            bins=10,
            kde=True,
            color=cores[idx],
            label=categoria,
            edgecolor="black",
            alpha=0.5
        )
        media = subset["similaridade"].mean()
        plt.axvline(media, color=cores[idx], linestyle='--', linewidth=2, label=f"Média {categoria}: {media:.2f}")

plt.title("Distribuição Sobreposta de Similaridade por Categoria (sem similaridade 1)", fontsize=16, weight='bold')
plt.xlabel("Similaridade", fontsize=13)
plt.ylabel("Frequência", fontsize=13)
plt.xlim(0, 1)
plt.ylim(0)
plt.tight_layout()
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.legend()
output_path = REPORTS_DIR / "histograma_sobreposto_sem_1.png"
plt.savefig(output_path, dpi=150)
print(f"Histograma sobreposto salvo em: {output_path}")
plt.close()

print("Histogramas gerados e salvos como imagens.")