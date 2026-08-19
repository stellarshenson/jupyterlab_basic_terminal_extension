/**
 * Unit tests for the 'basic-terminal:launch' command - cwd resolution
 * between explicit args, the file browser fallback, and omission.
 */

import plugin from '../index';
import { requestAPI } from '../request';

// The real module drags in an ESM-only dependency chain jest does not
// transform; the tests only need the token as an opaque value.
jest.mock('@jupyterlab/filebrowser', () => ({
  IDefaultFileBrowser: 'IDefaultFileBrowser-token'
}));

jest.mock('../request');

const requestAPIMock = requestAPI as jest.MockedFunction<typeof requestAPI>;

function makeApp(): any {
  return {
    commands: {
      addCommand: jest.fn(),
      execute: jest.fn().mockResolvedValue(null)
    },
    serviceManager: { serverSettings: {} },
    shell: { activateById: jest.fn() }
  };
}

function activateAndGetExecute(browser: any): (args: any) => Promise<any> {
  const app = makeApp();
  (plugin.activate as any)(app, browser);
  return app.commands.addCommand.mock.calls[0][1].execute;
}

function postedBody(): any {
  expect(requestAPIMock).toHaveBeenCalledTimes(1);
  return JSON.parse(requestAPIMock.mock.calls[0][2]?.body as string);
}

describe('jupyterlab_basic_terminal_extension', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    requestAPIMock.mockResolvedValue({ terminal_name: 'term-1' });
  });

  it('falls back to the file browser path when args.cwd is absent', async () => {
    const execute = activateAndGetExecute({
      model: { path: 'some/folder' }
    });
    await execute({ argv: ['lab-utils'] });
    expect(postedBody().cwd).toBe('some/folder');
  });

  it('lets an explicit args.cwd win over the file browser path', async () => {
    const execute = activateAndGetExecute({
      model: { path: 'some/folder' }
    });
    await execute({ argv: ['lab-utils'], cwd: '/explicit/dir' });
    expect(postedBody().cwd).toBe('/explicit/dir');
  });

  it('omits cwd from the POST body without a browser or args.cwd', async () => {
    const execute = activateAndGetExecute(null);
    await execute({ argv: ['lab-utils'] });
    expect('cwd' in postedBody()).toBe(false);
  });
});
