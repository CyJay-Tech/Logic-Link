# Plano para Manter o Painel de Propriedades Sempre Aberto

## Objetivo
Manter o painel de propriedades sempre visível, mesmo quando nenhum node estiver selecionado, exibindo uma mensagem padrão "Nenhum node selecionado" nesse caso.

---

## 1. Funcionamento Atual

- O painel de propriedades é um QDockWidget chamado "Propriedades do Node" (src/main.py).
- Ele é exibido (`self.dock.show()`) quando um node é selecionado e ocultado (`self.dock.hide()`) quando não há seleção.
- O método `on_selection_changed` faz essa lógica.
- Os campos do painel são preenchidos via `fill_properties_panel(node)`.

---

## 2. Mudanças Necessárias

### a) Remover o Ocultamento do Painel
- Eliminar ou comentar todas as chamadas a `self.dock.hide()` no código.
- O painel deve ser exibido permanentemente após a inicialização.

### b) Exibir Mensagem Padrão Quando Nenhum Node Estiver Selecionado
- No método `on_selection_changed`, quando não houver node selecionado:
  - Exibir um `QLabel` centralizado no painel com o texto "Nenhum node selecionado".
  - Ocultar/desabilitar os campos de edição, se necessário.
- Quando um node for selecionado:
  - Remover o `QLabel` de mensagem e exibir os campos normalmente.

### c) Garantir Atualização Dinâmica
- O painel deve alternar entre a mensagem padrão e os campos de edição conforme a seleção muda.

---

## 3. Fluxo de Estados do Painel

```mermaid
flowchart TD
    A[Início do App] --> B[Exibe painel de propriedades]
    B --> |Node selecionado| C[Mostra campos de edição]
    B --> |Nenhum node selecionado| D[Mostra mensagem "Nenhum node selecionado"]
    C --> |Node desmarcado| D
    D --> |Node selecionado| C
```

---

## 4. Passos Técnicos

1. No `src/main.py`, localize todos os pontos onde `self.dock.hide()` é chamado e remova/comente.
2. No método `on_selection_changed`:
   - Se não houver node selecionado, exiba o `QLabel` com a mensagem padrão e oculte/desabilite os campos de edição.
   - Se houver node selecionado, remova o `QLabel` e exiba/preencha os campos normalmente.
3. Adicione um `QLabel` (ex: `self.no_selection_label`) ao painel, inicialmente oculto.
4. Garanta que a interface não quebre ao alternar entre os estados.

---

## Resumo Visual

- Painel sempre visível.
- Alterna entre:
  - Mensagem "Nenhum node selecionado" (quando nada está selecionado)
  - Campos de edição (quando um node está selecionado)

---

**Confirme se está satisfeito com este plano ou se deseja sugerir algum ajuste.**