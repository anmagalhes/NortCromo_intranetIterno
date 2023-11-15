// background.js

// Registra um listener para mensagens do content_script
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (request.type === "CS_ASK_BG_4706") {
      // Execute a lógica necessária aqui
      chrome.tabs.sendMessage(sender.tab.id, { type: "BG_RESPONSE", data: "Resposta do script de fundo" });
    }
  });
  