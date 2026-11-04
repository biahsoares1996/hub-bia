# 🚀 Hub da Bia — Craft Suite Desktop

O **Hub da Bia** é uma central de aplicativos e produtividade pessoal inspirada na filosofia e design do **Craft Launcher** (*ArtCraft / PhotoCraft / PdfCraft*), desenvolvida sob medida para a Bia.

![Hub da Bia Preview](screenshot_hub.png)

---

## ✨ Destaques & Funcionalidades

1. **Design Moderno (Craft Dark Suite)**
   - Interface limpa com estética Dark Mode de alto padrão, sombras suaves e tipografia Segoe UI.
   - Cards dedicados com ícone oficial, tags e descrição de cada aplicativo.

2. **Monitoramento em Tempo Real de Processos**
   - Detecta instantaneamente se o aplicativo já está aberto no Windows via Win32 ctypes (`CreateToolhelp32Snapshot`), sem travar a interface e sem uso de CPU.
   - Mostra badge **`● Rodando`** em verde esmeralda quando o app está em execução.

3. **Lançamento Assíncrono com 1 Clique**
   - O botão **"Abrir"** inicia o programa em segundo plano desanexado do Hub.
   - Botão **"📁 Pasta"** para abrir o diretório do projeto direto no Windows Explorer.

4. **100% Modular e Expansível (`apps.json`)**
   - Adicione novos programas a qualquer momento pelo botão **`＋ Novo Aplicativo`** na interface ou editando diretamente o arquivo [`config/apps.json`](config/apps.json).

5. **Bandeja do Sistema (System Tray)**
   - Minimiza de forma limpa para a bandeja perto do relógio do Windows.
   - Menu rápido com botão direito para iniciar qualquer app imediatamente.

---

## 🛠️ Aplicativos Atualmente Integrados

| Aplicativo | Categoria | Descrição |
|---|---|---|
| **Áurea Browser** | Navegação & Web | Navegador ultra veloz com dock de WhatsApp integrado e abas limpas. |
| **Gatoceiro** | Finanças & Gestão | Sistema completo de controle financeiro, conciliação e fluxo de caixa. |
| **OmniDVR** | Segurança & CFTV | Central de câmeras de segurança, monitoramento ao vivo e gravação contínua. |
| *(Próximos Apps)* | Design / 3D / Utilitários | Espaço reservado para Canva Personalizado, Blocos Dinâmicos, etc. |

---

## 📦 Instalador Executável Standalone (.exe)

O Hub possui um instalador executável próprio com interface gráfica:
👉 **[`Instalador_Hub_da_Bia.exe`](Instalador_Hub_da_Bia.exe)**

Ao executar o instalador `.exe`:
1. Exibe a interface gráfica com barra de progresso e etapas em tempo real.
2. Instala o programa completo em `%LOCALAPPDATA%\Programs\HubDaBia`.
3. Cria os atalhos com ícone oficial na **Área de Trabalho** e no **Menu Iniciar**.
4. **Fixa o ícone oficial na Barra de Tarefas do Windows** automaticamente.
5. Inicia o Hub da Bia pronto para uso.

---

## 🔄 Sistema de Atualização (Auto-Updater)

O Hub possui um mecanismo integrado de auto-atualização (`core/updater.py`):
- Monitora silenciosamente novas versões através de `version.json`.
- Exibe o botão **`✨ Nova Versão!`** na barra lateral com a lista de melhorias quando houver novidade.
- Atualiza os arquivos com 1 clique direto pela interface.
