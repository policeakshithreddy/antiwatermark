chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "antiwatermark-parent",
    title: "AntiWatermark",
    contexts: ["selection"]
  });

  chrome.contextMenus.create({
    id: "clean-selection",
    parentId: "antiwatermark-parent",
    title: "Clean Selection",
    contexts: ["selection"]
  });

  chrome.contextMenus.create({
    id: "rewrite-selection",
    parentId: "antiwatermark-parent",
    title: "Rewrite Selection Locally",
    contexts: ["selection"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (!tab.id) return;
  
  if (info.menuItemId === "clean-selection") {
    chrome.tabs.sendMessage(tab.id, {
      action: "clean_selection",
      text: info.selectionText
    });
  } else if (info.menuItemId === "rewrite-selection") {
    chrome.tabs.sendMessage(tab.id, {
      action: "rewrite_selection",
      text: info.selectionText
    });
  }
});
