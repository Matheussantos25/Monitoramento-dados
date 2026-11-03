"""Menu preferences only; authorization remains in the existing owner-scoped stores."""
TABS = {
    "overview": "Visão geral", "training": "Treino", "physical": "Evolução física",
    "health": "Saúde", "study": "Estudar", "study_progress": "Evolução nos estudos",
    "prompts": "Prompts", "notes": "Anotações", "summaries": "Resumos", "pdfs": "PDFs",
    "mindmaps": "Mapas mentais", "schedule": "Cronograma", "finance": "Financeiro",
    "publications": "Publicações", "settings": "Metas e aparência", "account": "Configurações",
    "scripts": "Ideias e roteiros", "languages": "Idiomas", "weight": "Peso",
    "history": "Todos os registros", "calendar": "Calendário", "ranks": "Elos",
}
PINNED = {"overview", "settings", "account"}
STARTER = {"overview", "training", "physical", "health", "languages", "settings", "account", "weight", "history", "calendar", "ranks"}


def menu_tabs(saved=None, generic=False):
    if saved is None:
        return [key for key in TABS if not generic or key in STARTER]
    if not isinstance(saved, list) or any(not isinstance(key, str) for key in saved):
        raise ValueError("Seleção de abas inválida.")
    # Preserve known cross-platform IDs; ignore obsolete IDs from newer/older clients.
    return [key for key in TABS if key in saved or key in PINNED]


def visible_menu(pages, prefs, generic=False):
    enabled = menu_tabs(prefs.get("menu_tabs"), generic)
    labels = {TABS[key] for key in enabled}
    return [page for page in pages if page in labels]
