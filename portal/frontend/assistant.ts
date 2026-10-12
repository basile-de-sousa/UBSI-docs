type Source = {title: string; reference: string; section: string; excerpt: string; excerpt_truncated?: boolean; url: string};
type Result = {status: string; message: string; sources: Source[]; experimental?: boolean};

export function initializeAssistant() {
  document.querySelectorAll<HTMLElement>("[data-assistant]").forEach(panel => {
    const form = panel.querySelector<HTMLFormElement>("[data-chat-form]")!;
    const input = form.querySelector<HTMLTextAreaElement>('[name="question"]')!;
    const transcript = panel.querySelector<HTMLElement>("[data-chat-transcript]")!;
    const status = panel.querySelector<HTMLElement>("[data-chat-status]")!;
    const send = panel.querySelector<HTMLButtonElement>("[data-chat-send]")!;
    input.setAttribute("aria-describedby", "chat-help");
    let controller: AbortController | undefined;
    let busy = false;
    const element = <K extends keyof HTMLElementTagNameMap>(tag: K, text: string, className = "") => {
      const node = document.createElement(tag); node.textContent = text; node.className = className; return node;
    };
    const reset = () => {
      controller?.abort(); controller = undefined;
      transcript.replaceChildren(); status.textContent = ""; input.value = "";
      busy = false; send.disabled = false; form.removeAttribute("aria-busy");
    };
    panel.querySelector<HTMLButtonElement>("[data-chat-clear]")!.addEventListener("click", () => { reset(); input.focus(); });
    window.addEventListener("pagehide", reset);
    form.addEventListener("submit", async event => {
      event.preventDefault(); if (busy) return;
      const question = input.value.trim();
      if (!question || question.length > 500) { status.textContent = "Saisissez une question de 1 à 500 caractères."; input.focus(); return; }
      busy = true; send.disabled = true; form.setAttribute("aria-busy", "true");
      const request = new AbortController(); controller = request;
      const timeout = window.setTimeout(() => request.abort(), 25000);
      const exchange = element("section", "", "chat-exchange");
      exchange.append(element("p", "Votre question", "eyebrow"), element("p", question, "chat-question"));
      const reply = element("div", "", "chat-reply"); exchange.append(reply); transcript.append(exchange);
      while (transcript.children.length > 12) transcript.firstElementChild?.remove();
      status.textContent = "Recherche dans les contenus publiés…";
      const retryButton = (seconds = 0) => {
        const button = element("button", "Réessayer", "button button-secondary"); button.type = "button";
        if (seconds) { button.disabled = true; window.setTimeout(() => { button.disabled = false; }, seconds * 1000); }
        button.addEventListener("click", () => { input.value = question; form.requestSubmit(); }); reply.append(button);
      };
      try {
        const response = await fetch(panel.dataset.queryUrl!, {
          method: "POST", credentials: "same-origin", cache: "no-store", redirect: "error",
          headers: {"Content-Type": "application/json", "X-CSRFToken": form.querySelector<HTMLInputElement>('[name="csrfmiddlewaretoken"]')!.value},
          body: JSON.stringify({question}), signal: request.signal,
        });
        const result: Result = await response.json();
        if (controller !== request) return;
        if (!Array.isArray(result.sources) || typeof result.message !== "string") throw new Error();
        reply.append(element("p", result.message, "chat-answer"));
        if (result.experimental) reply.append(element("span", "Aperçu expérimental", "reference-chip"));
        for (const source of result.sources.slice(0, 3)) {
          const url = new URL(source.url, location.origin);
          if (url.origin !== location.origin || !url.pathname.startsWith("/assistant/source/")) throw new Error();
          const card = element("article", "", "chat-source");
          card.append(element("span", source.reference, "reference-chip"), element("h3", source.title));
          if (source.section && source.section !== source.title) card.append(element("p", source.section, "source-section"));
          card.append(element("blockquote", source.excerpt));
          if (source.excerpt_truncated) card.append(element("p", "Extrait abrégé. Consultez la source pour lire la suite.", "field-help"));
          const link = element("a", "Voir la réponse →", "subtle-link"); link.href = url.href; card.append(link); reply.append(card);
        }
        if (!response.ok && !["qualification_pending", "unauthenticated", "forbidden", "invalid"].includes(result.status)) retryButton(Math.min(300, Math.max(1, Number(response.headers.get("Retry-After")) || 3)));
        status.textContent = result.status === "answer" ? "Réponse disponible, avec sa source." : response.ok ? "Recherche terminée." : "La recherche n’a pas pu aboutir.";
        input.value = "";
      } catch {
        if (controller !== request) return;
        reply.replaceChildren(element("p", "La recherche de réponses est temporairement indisponible. Réessayez dans quelques instants.")); retryButton();
        status.textContent = "La recherche n’a pas pu aboutir.";
      } finally {
        window.clearTimeout(timeout);
        if (controller === request) { controller = undefined; busy = false; send.disabled = false; form.removeAttribute("aria-busy"); }
      }
    });
  });
}
