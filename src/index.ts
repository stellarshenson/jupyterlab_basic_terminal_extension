import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { IDefaultFileBrowser } from '@jupyterlab/filebrowser';

import { requestAPI } from './request';

export interface ILaunchTerminalArgs {
  argv: string[];
  /**
   * Directory to spawn in - absolute, or a server-relative API path ('' is
   * the server root). When omitted, falls back to the file browser's
   * current path if the browser is available.
   */
  cwd?: string;
}

export interface ILaunchTerminalResponse {
  terminal_name: string;
}

const COMMAND_LAUNCH = 'basic-terminal:launch';

const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyterlab_basic_terminal_extension:plugin',
  description:
    'Launch a JupyterLab terminal whose pty runs a utility directly with no shell. The tab is focused on launch and closes when the process exits.',
  autoStart: true,
  optional: [IDefaultFileBrowser],
  activate: (
    app: JupyterFrontEnd,
    defaultBrowser: IDefaultFileBrowser | null
  ) => {
    console.log(
      'JupyterLab extension jupyterlab_basic_terminal_extension is activated!'
    );
    app.commands.addCommand(COMMAND_LAUNCH, {
      label: 'Launch utility terminal (shell-less)',
      caption:
        'Spawn a JupyterLab terminal whose only process is the supplied argv. Tab is focused on launch and closes when the process exits.',
      execute: async args => {
        const { argv, cwd } = args as unknown as ILaunchTerminalArgs;
        if (!Array.isArray(argv) || argv.length === 0) {
          throw new Error(
            `${COMMAND_LAUNCH}: argv must be a non-empty string array`
          );
        }
        // Explicit args.cwd wins; otherwise fall back to the file browser's
        // current path (a server-relative API path, '' at root). When neither
        // exists cwd stays undefined and JSON.stringify drops it.
        const effectiveCwd =
          cwd !== undefined ? cwd : defaultBrowser?.model.path;
        const launched = await requestAPI<ILaunchTerminalResponse>(
          'launch-terminal',
          app.serviceManager.serverSettings,
          {
            method: 'POST',
            body: JSON.stringify({ argv, cwd: effectiveCwd })
          }
        );
        const widget: any = await app.commands.execute('terminal:open', {
          name: launched.terminal_name
        });
        if (widget?.id) {
          app.shell.activateById(widget.id);
        }
        const session = widget?.content?.session;
        if (session) {
          const disposeWidget = (): void => {
            if (widget && !widget.isDisposed) {
              widget.dispose();
            }
          };
          session.disposed?.connect?.(disposeWidget);
          session.connectionStatusChanged?.connect?.(
            (_: unknown, status: string) => {
              if (status === 'disconnected') {
                disposeWidget();
              }
            }
          );
        }
        return widget;
      }
    });
  }
};

export default plugin;
