"""
Testes básicos das ferramentas do Módulo 1A.

Como o pytest funciona (resumo rápido):
- Ele descobre automaticamente funções cujo nome começa com `test_`.
- "Fixtures" (como `unique_email`) são passadas como argumentos e preparadas antes do teste.
- Usamos `assert` para verificar resultados esperados — se falhar, o pytest mostra o erro.

Por que usamos `.invoke({...})` nas ferramentas:
- As funções decoradas com `@tool` viram `StructuredTool` (LangChain). A forma recomendada de chamá-las é
  `tool.invoke({"arg": valor, ...})` — a chamada direta `tool(...)` é deprecada.
- `.invoke` recebe um dicionário com os parâmetros esperados (mesmos nomes dos argumentos da função).

UUID → string nos argumentos:
- Em alguns tools, o `args_schema` (Pydantic) espera `str`. Quando o banco retorna um UUID como objeto,
  convertemos com `str(uuid)` ao passar para `.invoke`.
"""

from app.agent import tools as t


def test_listar_status_lead(db_ready):
    r = t.listar_status_lead.invoke({})
    assert r.get("error") is None
    items = r["data"]["items"]
    assert len(items) >= 6
    assert any(x["codigo"] == "novo" for x in items)

def test_criar_e_obter_lead(unique_email):
    # Cria um lead novo usando um e-mail único (evita duplicidade)
    # Em ferramentas decoradas com @tool, usamos .invoke({args...}) no teste
    r = t.criar_lead.invoke({"nome": "João Teste", "email": unique_email, "empresa": "ACME"})
    assert r.get("error") is None
    lead_id = r["data"]["lead_id"]
    assert lead_id and len(str(lead_id)) == 36  # UUID v4 tem 36 caracteres com hifens

    # Recupera o mesmo lead usando a referência natural (email)
    r2 = t.obter_lead.invoke({"ref": unique_email})
    assert r2.get("error") is None
    assert r2["data"]["lead_id"] == lead_id
    # Saída educativa (visível com pytest -s)
    print(f"[lead_criar] {r['message']} id={lead_id} email={unique_email}")
    print(f"[lead_obter] {r2['message']} nome={r2['data']['nome']} status={r2['data']['status_codigo']}")


def test_notas_para_lead(unique_email):
    # Cria um lead de teste
    lead = t.criar_lead.invoke({"nome": "Maria Teste", "email": unique_email, "empresa": "Beta"})
    lead_id = lead["data"]["lead_id"]

    # Adiciona uma nota ao lead
    # (converter UUID para str, pois o schema desta tool valida string)
    n1 = t.adicionar_nota_ao_lead.invoke({"lead_ref_ou_id": str(lead_id), "texto": "Retornar orçamento amanhã"})
    assert n1.get("error") is None
    assert n1["data"]["note_id"]

    # Lista as notas do lead e confere se a nova nota aparece
    lst = t.listar_notas.invoke({"lead_ref_ou_id": str(lead_id)})  # idem: usar string
    assert lst.get("error") is None
    assert lst["data"]["total"] >= 1
    assert any(item["note_id"] == n1["data"]["note_id"] for item in lst["data"]["items"]) 
    print(f"[nota_adicionar] note_id={n1['data']['note_id']}")
    print(f"[nota_listar] total={lst['data']['total']}")


def test_tarefas_criar_e_concluir(unique_email):
    # Cria um lead e registra uma tarefa do tipo ligação
    lead = t.criar_lead.invoke({"nome": "Carlos Teste", "email": unique_email, "empresa": "Gamma"})
    lead_id = lead["data"]["lead_id"]

    tk = t.criar_tarefa.invoke({"lead_ref_ou_id": str(lead_id), "titulo": "Ligar amanhã", "tipo": "ligacao"})  # string
    assert tk.get("error") is None
    tarefa_id = tk["data"]["tarefa_id"]

    # Conclui a tarefa e valida o status
    done = t.concluir_tarefa.invoke({"tarefa_id": str(tarefa_id)})  # string
    assert done.get("error") is None
    assert done["data"]["status"] == "concluida"

    # Lista tarefas concluídas do lead e verifica a presença da tarefa concluída
    lst = t.listar_tarefas.invoke({"lead_ref_ou_id": str(lead_id), "status": "concluida"})
    assert lst.get("error") is None
    assert any(item["tarefa_id"] == tarefa_id for item in lst["data"]["items"]) 
    print(f"[tarefa_criar] tarefa_id={tarefa_id}")
    print(f"[tarefa_concluir] status={done['data']['status']}")
    print(f"[tarefa_listar] total={lst['data']['total']}")


def test_proposta_rascunho_itens_totais_export(unique_email):
    # Cria um lead e rascunha uma proposta
    lead = t.criar_lead.invoke({"nome": "Ana Teste", "email": unique_email, "empresa": "Delta"})
    lead_id = lead["data"]["lead_id"]

    prop = t.rascunhar_proposta.invoke({"lead_ref_ou_id": str(lead_id), "titulo": "Proposta Delta"})  # string
    assert prop.get("error") is None
    proposta_id = prop["data"]["proposta_id"]

    # Adiciona um item e recalcula os totais
    item = t.adicionar_item_proposta.invoke({"proposta_id": str(proposta_id), "descricao": "Consultoria", "quantidade": 2, "preco_unitario": 5000})  # string
    assert item.get("error") is None

    tot = t.calcular_totais_proposta.invoke({"proposta_id": str(proposta_id)})  # string
    assert tot.get("error") is None
    assert tot["data"]["subtotal"] >= 10000
    assert tot["data"]["total"] == tot["data"]["subtotal"]  # sem desconto por padrão

    # Exporta a proposta em markdown para visualização
    md = t.exportar_proposta.invoke({"proposta_id": str(proposta_id), "formato": "markdown"})  # string
    assert md.get("error") is None
    assert "Proposta exportada" in md["message"]
    assert "markdown" == md["data"]["formato"]
    print(f"[proposta_rascunhar] proposta_id={proposta_id}")
    print(f"[proposta_add_item] item_id={item['data']['item_id']}")
    print(f"[proposta_totais] subtotal={tot['data']['subtotal']} total={tot['data']['total']}")
    print(f"[proposta_exportar] formato={md['data']['formato']} len={len(md['data']['conteudo'])}")


def test_leads_buscar_listar_e_atualizar(unique_email):
    # cria alguns leads
    t.criar_lead.invoke({"nome": "Alice ACME", "email": unique_email, "empresa": "ACME"})
    t.criar_lead.invoke({"nome": "Bob Beta", "empresa": "Beta"})

    # buscar por nome/empresa
    res = t.buscar_leads.invoke({"consulta": "acm"})
    assert res.get("error") is None
    assert res["data"]["total"] >= 1

    # listar leads
    lst = t.listar_leads.invoke({})
    assert lst.get("error") is None
    assert lst["data"]["total"] >= 2

    # atualizar status/qualificado
    lead_id = t.obter_lead.invoke({"ref": unique_email})["data"]["lead_id"]
    up = t.atualizar_lead.invoke({"lead_id": str(lead_id), "status_codigo": "qualificado", "qualificado": True})
    assert up.get("error") is None
    got = t.obter_lead.invoke({"ref": unique_email})
    assert got["data"]["status_codigo"] == "qualificado"


def test_propostas_listar_export_json_e_atualizar_corpo(unique_email):
    # cria lead e proposta
    lead = t.criar_lead.invoke({"nome": "Cliente JSON", "email": unique_email})
    lead_id = lead["data"]["lead_id"]
    prop = t.rascunhar_proposta.invoke({"lead_ref_ou_id": str(lead_id), "titulo": "Proposta JSON"})
    proposta_id = prop["data"]["proposta_id"]

    # atualizar corpo markdown e exportar json
    corpo = "# Proposta JSON\n\nConteúdo didático."
    up = t.atualizar_corpo_proposta.invoke({"proposta_id": str(proposta_id), "corpo_md": corpo})
    assert up.get("error") is None
    j = t.exportar_proposta.invoke({"proposta_id": str(proposta_id), "formato": "json"})
    assert j.get("error") is None
    assert j["data"]["corpo_md"].startswith("# Proposta JSON")

    # listar propostas do lead
    lst = t.listar_propostas.invoke({"lead_ref_ou_id": str(lead_id)})
    assert lst.get("error") is None
    assert any(item["proposta_id"] == proposta_id for item in lst["data"]["items"])


def test_resolver_lead_e_responder(unique_email):
    # cria lead e resolve por email
    t.criar_lead.invoke({"nome": "Resolver Teste", "email": unique_email})
    r = t.resolver_lead.invoke({"ref": unique_email})
    assert r.get("error") is None
    assert r["data"]["lead_id"]

    # responder é um utilitário para padronizar a saída
    resp = t.responder.invoke({"mensagem": "ok", "intent": "conversa_geral"})
    assert resp["message"] == "ok"
    assert resp["intent"] == "conversa_geral"