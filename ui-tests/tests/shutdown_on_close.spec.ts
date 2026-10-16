import { expect, IJupyterLabPageFixture, test } from '@jupyterlab/galata';

/**
 * The argument shutdownOnClose of basic-terminal:launch, against the real
 * server: the terminal list of the server shows whether closing the tab
 * ended the program.
 */

// Galata answers GET api/terminals in the page with the terminals created
// through POST api/terminals only. The command starts its terminal through
// its own route, so with that mock its check of the live list fails.
test.use({ terminals: null });

const LONG_ARGV = ['sleep', '300'];

/** The names of the terminals the server runs. */
async function terminalNames(page: IJupyterLabPageFixture): Promise<string[]> {
  const response = await page.request.get('api/terminals');
  expect(response.ok()).toBe(true);
  return ((await response.json()) as Array<{ name: string }>).map(
    model => model.name
  );
}

/** Launch argv through the command; return the terminal name and the tab id. */
async function launch(
  page: IJupyterLabPageFixture,
  args: Record<string, unknown>
): Promise<{ name: string; id: string }> {
  return page.evaluate(async launchArgs => {
    const widget: any = await (window as any).jupyterapp.commands.execute(
      'basic-terminal:launch',
      launchArgs
    );
    return { name: widget.content.session.name, id: widget.id };
  }, args);
}

/** Close the tab with the close icon of its tab bar entry, as a user does. */
async function closeTab(page: IJupyterLabPageFixture, id: string) {
  const tab = page.locator(
    `#jp-main-dock-panel li.lm-TabBar-tab[data-id="${id}"]`
  );
  await tab.locator('.lm-TabBar-tabCloseIcon').click();
  await expect(tab).toHaveCount(0);
}

test('SIB-shutdownOnClose closing the tab ends the program when shutdownOnClose is true', async ({
  page
}) => {
  const { name, id } = await launch(page, {
    argv: LONG_ARGV,
    shutdownOnClose: true
  });
  expect(await terminalNames(page)).toContain(name);

  await closeTab(page, id);

  await expect
    .poll(() => terminalNames(page), { timeout: 10000 })
    .not.toContain(name);
});

test('SIB-shutdownOnClose closing the tab leaves the program running without shutdownOnClose', async ({
  page
}) => {
  const { name, id } = await launch(page, { argv: LONG_ARGV });
  expect(await terminalNames(page)).toContain(name);

  await closeTab(page, id);

  // A shutdown removes the terminal well within this wait: in the test
  // above the removal took 286 ms after the close click (2026-10-16).
  await page.waitForTimeout(3000);
  expect(await terminalNames(page)).toContain(name);

  const removed = await page.request.delete(`api/terminals/${name}`);
  expect(removed.status()).toBe(204);
  expect(await terminalNames(page)).not.toContain(name);
});
