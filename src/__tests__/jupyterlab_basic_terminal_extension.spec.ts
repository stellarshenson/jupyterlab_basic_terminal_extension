/**
 * Unit tests for the 'basic-terminal:launch' command - cwd resolution
 * between explicit args, the file browser fallback, and omission, plus
 * the guard that refuses to open a terminal whose pty already exited.
 */

import plugin from '../index';
import { requestAPI } from '../request';
import { TerminalAPI } from '@jupyterlab/services';

// The real module drags in an ESM-only dependency chain jest does not
// transform; the tests only need the token as an opaque value.
jest.mock('@jupyterlab/filebrowser', () => ({
  IDefaultFileBrowser: 'IDefaultFileBrowser-token'
}));

jest.mock('../request');

// Only the static listRunning is used; the rest of the module is heavy.
jest.mock('@jupyterlab/services', () => ({
  TerminalAPI: { listRunning: jest.fn() }
}));

const requestAPIMock = requestAPI as jest.MockedFunction<typeof requestAPI>;

const TERMINAL_NAME = 'term-1';

function makeApp(runningNames: string[] = [TERMINAL_NAME]): any {
  (TerminalAPI.listRunning as jest.Mock).mockResolvedValue(
    runningNames.map(name => ({ name }))
  );
  return {
    commands: {
      addCommand: jest.fn(),
      execute: jest.fn().mockResolvedValue(null)
    },
    serviceManager: {
      serverSettings: {},
      // Mirrors ContentsManager: driveName is '' for the default drive and
      // the registered drive otherwise; localPath strips a known prefix.
      contents: {
        driveName: jest.fn((path: string) => {
          const m = /^([A-Za-z0-9-]+):/.exec(path);
          return m && m[1] === 'S3' ? m[1] : '';
        }),
        localPath: jest.fn((path: string) => path.replace(/^S3:/, ''))
      }
    },
    shell: { activateById: jest.fn() }
  };
}

function activateAndGetExecute(
  browser: any,
  runningNames?: string[]
): (args: any) => Promise<any> {
  const app = makeApp(runningNames);
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
    requestAPIMock.mockResolvedValue({ terminal_name: TERMINAL_NAME });
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

  it('omits cwd when the file browser is on a non-server drive', async () => {
    // Stripping `S3:` would yield `some/folder`, which the server resolves
    // against its own root - silently launching in an unrelated directory.
    const execute = activateAndGetExecute({
      model: { path: 'S3:some/folder' }
    });
    await execute({ argv: ['lab-utils'] });
    expect('cwd' in postedBody()).toBe(false);
  });

  it('keeps the file browser root as an empty path', async () => {
    const execute = activateAndGetExecute({ model: { path: '' } });
    await execute({ argv: ['lab-utils'] });
    expect(postedBody().cwd).toBe('');
  });

  it('checks the live terminal list rather than a cached snapshot', async () => {
    const execute = activateAndGetExecute({ model: { path: '' } });
    await execute({ argv: ['lab-utils'] });
    expect(TerminalAPI.listRunning).toHaveBeenCalledTimes(1);
  });

  it('refuses to open a terminal whose pty already exited', async () => {
    const execute = activateAndGetExecute({ model: { path: '' } }, []);
    await expect(execute({ argv: ['lab-utils'] })).rejects.toThrow(
      /exited before it could be displayed/
    );
  });

  it('does not delegate to terminal:open when the pty is gone', async () => {
    const app = makeApp([]);
    (plugin.activate as any)(app, null);
    const execute = app.commands.addCommand.mock.calls[0][1].execute;
    await expect(execute({ argv: ['lab-utils'] })).rejects.toThrow();
    expect(app.commands.execute).not.toHaveBeenCalled();
  });
});
