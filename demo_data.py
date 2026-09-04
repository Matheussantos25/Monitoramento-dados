"""Fictional, session-only data for SOLEM_DEMO=1. No network or database access."""
from copy import deepcopy
from datetime import datetime, timedelta
from types import SimpleNamespace
import streamlit as st


def sample_records():
    today = (datetime.utcnow() - timedelta(hours=3)).date()
    rows = []
    def add(offset, group, exercise, **fields):
        row = dict(id=len(rows)+1, data=str(today-timedelta(days=offset)), horario="08:30:00",
                   grupo_muscular=group, exercicio=exercise, series=0, repeticoes=0, carga_kg=0.0,
                   descanso_seg=0, duracao_min=0, distancia_km=0.0, alimentacao_saudavel="",
                   alimentacao_besteirol="", peso_corporal=0.0, dados_extras={})
        row.update(fields)
        rows.append(row)
    for offset in range(25, 0, -1):
        if offset % 7 == 6:
            continue
        if offset % 2:
            add(offset, "Peitoral", "Flexão", series=3, repeticoes=24+offset, descanso_seg=60, dados_extras={"humor":"Normal"})
        add(offset, "Estudos", "Banco de Dados (SQL/NoSQL/Big Data)", duracao_min=35+offset,
            repeticoes=18+offset, dados_extras={"q_certas":15+offset,"q_erradas":3,"tempo_video":0,
                "topico_edital":"1 Modelagem de dados (conceitual, lógica e física)","fonte_questoes":"FGV"})
        if offset % 3 == 0:
            add(offset, "Nutrição", "Refeição Diária", alimentacao_saudavel="Ovo, Aveia, Banana")
        if offset % 5 == 0:
            add(offset, "Métricas", "Peso Diário", peso_corporal=70+offset/20)
    add(0, "Estudos", "Língua Portuguesa", duracao_min=42, repeticoes=27,
        dados_extras={"q_certas":23,"q_erradas":4,"tempo_video":0,"fonte_questoes":"FGV",
                      "topico_edital":"1 Compreensão e interpretação de textos"})
    return rows


class DemoClient:
    def __init__(self):
        if "solem_demo_records" not in st.session_state:
            st.session_state["solem_demo_records"] = sample_records()

    def table(self, name):
        if name != "treinos":
            raise ValueError("Tabela indisponível na demonstração")
        return DemoQuery()


class DemoQuery:
    def __init__(self):
        self.operation, self.payload, self.filters = "select", None, []

    def select(self, columns):
        return self

    def insert(self, data):
        self.operation, self.payload = "insert", deepcopy(data)
        return self

    def update(self, data):
        self.operation, self.payload = "update", deepcopy(data)
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def execute(self):
        rows = st.session_state["solem_demo_records"]
        matches = lambda row: all(row.get(key) == value for key, value in self.filters)
        if self.operation == "insert":
            added = self.payload if isinstance(self.payload, list) else [self.payload]
            for row in added:
                row["id"] = max((r["id"] for r in rows), default=0) + 1
                rows.append(row)
        elif self.operation == "update":
            for row in rows:
                if matches(row):
                    row.update(self.payload)
        elif self.operation == "delete":
            st.session_state["solem_demo_records"] = [row for row in rows if not matches(row)]
        return SimpleNamespace(data=deepcopy([row for row in st.session_state["solem_demo_records"] if matches(row)]))
