Bot Discord para gerenciamento de fila com comandos e botões interativos.

## Funcionalidades

- **Iniciar Fila**: Inicializa a fila com os membros online ou ausentes (idle) do canal do discord.
- **Remover Membro**: Remove um membro específico da fila.
- **Passar Bastão**: Sai do primeiro membro da fila para o ultimo.
- **Entrar/Sair da Fila**: Adiciona ou remove um membro da fila.
- **Indisponível**: Marca um membro como indisponível, quando primeiro, é movido para o final da fila.

## Configuração

### Pré-requisitos

- Python 3.8 ou superior
- Conta de desenvolvedor do Discord e um bot configurado

### Instalando dependências

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/bot-bastao.git
   cd bot-bastao
   pip install -r requirements.txt
   python Bot_Bastao.py
