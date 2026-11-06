// Capturas de tela da interface para a monografia e a apresentação (docs/capturas/).
// Requer o Data Talk no ar (docker compose up) e roda num container do Playwright:
//   docker run --rm --add-host=host.docker.internal:host-gateway -v "$PWD/docs/capturas:/saida" -v "$PWD/frontend/capturar-telas.mjs:/tmp/capturar.mjs" -w /tmp mcr.microsoft.com/playwright:v1.49.0-noble sh -c "npm i -s playwright@1.49.0 && node capturar.mjs"
// Atenção: faz duas perguntas reais ao modelo (alguns centavos de dólar).
import { chromium } from "playwright";
const base = "http://host.docker.internal:3030";
const navegador = await chromium.launch();
const pagina = await navegador.newPage({ viewport: { width: 1440, height: 900 } });
const foto = (nome, cheia = false) => pagina.screenshot({ path: `/saida/${nome}.png`, fullPage: cheia });
const perguntar = async (texto) => {
  await pagina.locator(".caixa textarea").fill(texto);
  await pagina.keyboard.press("Enter");
};

await pagina.goto(`${base}/?aba=dados`); await pagina.waitForTimeout(1000); await foto("2-dados", true);

await pagina.goto(`${base}/?aba=conversa`); await pagina.waitForTimeout(800);
await perguntar("Como evoluiu a receita mês a mês em 2026?");
await pagina.waitForTimeout(600); await foto("4-pensando");
await pagina.waitForSelector(".painel, .indicador, .alerta", { timeout: 90000 }); await pagina.waitForTimeout(1500);
await foto("5-resposta-grafico");

await pagina.locator(".avancado").click(); await pagina.waitForTimeout(300);
await perguntar("Quantas vendas houve em março de 2026?");
await pagina.waitForFunction(() => document.querySelectorAll(".troca .corpo .pensando").length === 0 && document.querySelectorAll(".troca").length === 2, null, { timeout: 90000 });
await pagina.waitForTimeout(800);
await pagina.locator("details.tecnico").last().locator("summary").click(); await pagina.waitForTimeout(500);
await foto("6-indicador-avancado", true);
await navegador.close();
