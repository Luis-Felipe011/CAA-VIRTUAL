import numpy as np
from sklearn.base import TransformerMixin, BaseEstimator
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from tqdm.notebook import tqdm
import pandas as pd
from sentence_transformers import SentenceTransformer


DADOS_DE_TREINO = {
    "text": [
        # Saudação (10)
        "oi",
        "olá",
        "bom dia",
        "boa tarde",
        "e aí",
        "como vai?",
        "tudo bem?",
        "vamos começar?",
        "iniciar",
        "saudações",

        # Menu (6)
        "mostrar opções",
        "o que você pode fazer?",
        "menu",
        "quais são as opções?",
        "mudar de assunto",
        "falar de outro tópico",

        # Reiniciar (5)
        "reiniciar",
        "quero recomeçar",
        "refazer",
        "de novo, por favor",
        "voltar ao início",

        # Elegibilidade (5)
        "quem pode se inscrever no PROUNI?",
        "quais são os requisitos para o PROUNI?",
        "qual a renda mínima para PROUNI?",
        "quem é elegível para o PROUNI?",
        "como funciona a renda per capita no PROUNI?",

        # Processo de inscrição (5)
        "como faço inscrição no PROUNI?",
        "quando começam as inscrições do PROUNI?",
        "qual o prazo para inscrição no PROUNI?",
        "onde posso me inscrever no PROUNI?",
        "como me inscrevo no PROUNI?",

        # Documentos necessários (6)
        "quais documentos preciso para PROUNI?",
        "o que apresentar na matrícula do PROUNI?",
        "documentos exigidos para bolsa PROUNI",
        "que documentos são necessários para PROUNI?",
        "como comprovo minha renda para o PROUNI?",
        "quais documentos devo enviar?",

        # Prazos (5)
        "qual a data limite de inscrição no PROUNI?",
        "até quando posso me inscrever no PROUNI?",
        "quando encerra o prazo do PROUNI?",
        "prazo final PROUNI?",
        "data de fechamento das inscrições do PROUNI?",

        # Tipos de bolsa (5)
        "quais tipos de bolsa o PROUNI oferece?",
        "bolsa integral ou parcial no PROUNI?",
        "modalidades de bolsa do PROUNI?",
        "o que é bolsa parcial no PROUNI?",
        "o que é bolsa integral no PROUNI?",

        # Opções de curso (5)
        "posso escolher dois cursos no PROUNI?",
        "quantas opções de curso posso selecionar?",
        "posso mudar minha opção de curso?",
        "como funcionam as opções de curso no PROUNI?",
        "quantas escolhas tenho no PROUNI?"
    ],
    "intent": [
        # saudacao (10)
        "saudacao","saudacao","saudacao","saudacao","saudacao",
        "saudacao","saudacao","saudacao","saudacao","saudacao",

        # menu (6)
        "menu","menu","menu","menu","menu","menu",

        # reiniciar (5)
        "reiniciar","reiniciar","reiniciar","reiniciar","reiniciar",

        # elegibilidade (5)
        "elegibilidade","elegibilidade","elegibilidade","elegibilidade","elegibilidade",

        # processo_inscricao (5)
        "processo_inscricao","processo_inscricao","processo_inscricao","processo_inscricao","processo_inscricao",

        # documentos_necessarios (6)
        "documentos_necessarios","documentos_necessarios","documentos_necessarios","documentos_necessarios","documentos_necessarios","documentos_necessarios",

        # prazos (5)
        "prazos","prazos","prazos","prazos","prazos",

        # tipos_bolsa (5)
        "tipos_bolsa","tipos_bolsa","tipos_bolsa","tipos_bolsa","tipos_bolsa",

        # opcoes_curso (5)
        "opcoes_curso","opcoes_curso","opcoes_curso","opcoes_curso","opcoes_curso"
    ]
}


embedding_model = SentenceTransformer("all-mpnet-base-v2")

class Encoder(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.embedding_model = embedding_model

    def transform(self, X):
        return self.embedding_model.encode(list(X))

    def fit(self, X, y=None):
        return self


def preve_intencao(mensagem):

    df = pd.DataFrame(DADOS_DE_TREINO)

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"],
        df["intent"],
        test_size=0.5,
        random_state=14
    )


    pipeline = Pipeline([
        ('encoder', Encoder()),
        ('clf', LogisticRegression()),
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    y_pred

    single_pred = pipeline.predict([mensagem])
    return single_pred[0]