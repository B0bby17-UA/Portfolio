# Captive Portal Test

Um captive portal falso de prova de conceito que replica uma página de login Wi-Fi para **WI-FI FORUM AVEIRO**. Construído como uma demonstração de engenharia social para mostrar como os usuários podem ser facilmente enganados a inserir credenciais em uma página falsificada.

## Visão Geral

Este projeto replica a aparência de um captive portal legítimo de Wi-Fi público — do tipo que você encontra em shoppings, aeroportos e hotéis. A página é um fluxo de login do Google, guiando o usuário através de um formulário de dois passos (email → senha) que parece autêntico à primeira vista.

O objetivo é educacional: conscientizar sobre o quão convincentes as páginas de phishing podem ser e por que os usuários sempre devem verificar a URL antes de inserir informações sensíveis.

## Funcionalidades

- **Replicação perfeita do login do Google** — estilizado para combinar com o fluxo real de autenticação do Google
- **Formulário de dois passos** — email primeiro, depois senha, exatamente como o original
- **Transições suaves** — mudanças animadas de tela entre início → login → sucesso
- **Simulação de verificação de rede** — tela falsa de "Verificando rede..." adiciona credibilidade
- **Design responsivo** — funciona em desktop e dispositivos móveis
- **Autossuficiente** — todo HTML, CSS e JavaScript em um único arquivo (sem dependências externas)
- **Captura de credenciais** — envia os dados do formulário via POST para um endpoint configurável
- **Registro de metadados** — registra o nome do AP (`WI-FI FORUM AVEIRO`) e o timestamp de login a cada envio

## Como Funciona

1. O usuário se conecta a uma rede Wi-Fi falsa (ou é redirecionado via DNS spoofing)
2. A página do captive portal aparece, mostrando a tela de login da **WI-FI FORUM AVEIRO**
3. O usuário clica em **"Continuar com Google"**
4. Uma tela falsa de "Verificando rede..." aparece brevemente
5. Um formulário de login estilo Google aparece — primeiro pedindo email, depois senha
6. Após o envio, uma tela de sucesso é exibida ("Conectado! Você pode fechar esta tela e navegar com segurança") enquanto as credenciais são capturadas em segundo plano

## Detecção

Apesar da aparência realista, a página possui sinais sutis:

- **Sem cadeado HTTPS** — a URL não corresponde ao domínio do Google
- **Links fictícios** — os links de Termos de Serviço, Política de Privacidade e Ajuda não apontam para lugar nenhum
- **Sem fluxo OAuth real** — o formulário envia diretamente para um endpoint local (`/BruceEvilCreds/credenciais.txt`), não para os servidores do Google
- **Inconsistências visuais leves** — fontes, espaçamento ou cores podem diferir da página real
- **Campos de metadados ocultos** — o formulário inclui inputs ocultos para nome do AP e timestamp, que não existiriam em um login real do Google

## Estrutura de Arquivos

```
captive-portal-test/
├── index.html          # Página principal do captive portal (tudo em um)
├── README.md           # Este arquivo (English)
└── README.pt-BR.md     # Este arquivo (Português do Brasil)
```

## Configuração

1. Clone o repositório:
   ```bash
   git clone https://github.com/your-username/captive-portal-test.git
   cd captive-portal-test
   ```

2. Configure o endpoint de envio do formulário em `index.html`:
   ```html
   <form id="loginForm" method="POST" action="/BruceEvilCreds/credenciais.txt">
   ```

3. Execute a página usando um servidor web local:
   ```bash
   # Python
   python -m http.server 8080

   # Node.js
   npx http-server -p 8080
   ```

4. Acesse a página em `http://localhost:8080`

## Detalhes Técnicos

| Componente | Tecnologia |
|------------|------------|
| Markup | HTML5 |
| Estilos | CSS inline (sistema de design inspirado no Google) |
| Lógica | JavaScript vanilla (sem frameworks) |
| Ícones | PNGs e SVGs codificados em Base64 |
| Formulários | Fluxo de dois passos email → senha com validação no cliente |
| Captura de dados | POST para `/BruceEvilCreds/credenciais.txt` |

## Campos do Formulário

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `ap_name` | hidden | SSID da rede (`WI-FI FORUM AVEIRO`) |
| `login_date` | hidden | Timestamp ISO do envio |
| `email` | text | Endereço de email do usuário |
| `password` | password | Senha do usuário |

## Casos de Uso

- **Treinamento de conscientização de segurança** — demonstrar riscos de phishing para usuários não técnicos
- **Teste de penetração** — testar a resiliência organizacional contra phishing de credenciais
- **Educação** — ensinar estudantes sobre engenharia social e segurança web

## Aviso Legal

Esta ferramenta é destinada **exclusivamente para testes de segurança autorizados e fins educacionais**. O uso não autorizado desta ferramenta para capturar credenciais sem consentimento explícito é ilegal e antiético. O autor não se responsabiliza por usos indevidos.

## Licença

MIT
