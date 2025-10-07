🔥 Bot Telegram — Fogos.PT

Um bot do Telegram que fornece em tempo real as ocorrências ativas de incêndios em Portugal, com dados provenientes da API oficial do Fogos.PT
.
O utilizador pode selecionar o seu distrito preferido e receber notificações automáticas sempre que surgir uma nova ocorrência ou uma atualização relevante.

🚀 Funcionalidades

✅ Consulta de incêndios ativos em todo o país
✅ Filtro por distrito (com seleção interativa no Telegram)
✅ Notificações automáticas de novas ocorrências e atualizações
✅ Integração direta com a API Fogos.PT
✅ Dados armazenados em ficheiros locais (users.json, incidents.json)
✅ Interface simples com botões interativos (InlineKeyboard)

🧠 Como funciona

O utilizador inicia o bot com o comando /start.

Pode selecionar o distrito de interesse ou ver todas as ocorrências ativas.

O bot consulta periodicamente a API https://api.fogos.pt/v2/incidents/active?all=1.

Se houver novas ocorrências ou mudanças nos dados, o bot envia notificações automáticas.

⚙️ Tecnologias utilizadas

Python 3

python-telegram-bot (framework principal)

Requests (para chamadas à API)

JSON (para persistência simples de dados)

Logging (para monitorização)

💬 Comandos disponíveis
Comando	Descrição
/start	Mostra o menu inicial e as opções principais
/ver	Lista as ocorrências atuais no distrito selecionado
/alterar	Permite escolher um novo distrito
/help	(Opcional) Mostra instruções básicas

